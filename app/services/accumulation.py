from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from app.daily_snapshot import daily_watchlist
from app.services.announcements import AnnouncementsService
from app.services.disclosure_interests import DisclosureInterestsService
from app.services.fundamentals import FundamentalsService
from app.services.intelligence_events import IntelligenceEventsService

ACCUMULATION_WINDOW_DAYS = 2 * 365
DEFAULT_SLICE_SIZE = 13  # 52-stock watchlist rotates over ~4 days


@dataclass
class StockOutcome:
    code: str
    steps: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, **self.steps}


class AccumulationService:
    """Daily evidence-cache accumulation: a rotating slice of the watchlist
    gets DI + announcements + fundamentals fetched and persisted, then the
    intelligence event snapshot is rebuilt. Idempotent — reruns upsert."""

    def __init__(
        self,
        disclosure_service: DisclosureInterestsService | None = None,
        announcements_service: AnnouncementsService | None = None,
        fundamentals_service: FundamentalsService | None = None,
        events_service: IntelligenceEventsService | None = None,
        watchlist: tuple[str, ...] | None = None,
    ):
        self.disclosure_service = disclosure_service
        self.announcements_service = announcements_service
        self.fundamentals_service = fundamentals_service
        self.events_service = events_service
        self.watchlist = watchlist or tuple(daily_watchlist())

    def today_slice(self, count: int = DEFAULT_SLICE_SIZE, *, day_index: int | None = None) -> list[str]:
        if not self.watchlist:
            return []
        rotation_days = max(1, -(-len(self.watchlist) // count))
        index = (date.today().toordinal() if day_index is None else day_index) % rotation_days
        start_at = (index * count) % len(self.watchlist)
        return [self.watchlist[(start_at + i) % len(self.watchlist)] for i in range(min(count, len(self.watchlist)))]

    async def run(
        self,
        *,
        count: int = DEFAULT_SLICE_SIZE,
        per_step_budget: float = 100.0,
        progress=None,
    ) -> dict[str, object]:
        started = datetime.now(UTC)
        codes = self.today_slice(count)
        end = datetime.now(UTC).date()
        start = end - timedelta(days=ACCUMULATION_WINDOW_DAYS)
        outcomes: list[StockOutcome] = []
        disclosure = self.disclosure_service or DisclosureInterestsService()
        announcements = self.announcements_service or AnnouncementsService()
        fundamentals = self.fundamentals_service or FundamentalsService()
        events = self.events_service or get_events_service()

        for index, code in enumerate(codes):
            outcome = StockOutcome(code=code)
            for step_name, coroutine in (
                ("di", disclosure.get_disclosures(code, start_date=start, end_date=end)),
                ("announcements", announcements.get_announcements(code, start_date=start, end_date=end)),
                ("fundamentals", fundamentals.get_fundamentals(code)),
                ("events", events.get_events(code, start_date=start, end_date=end)),
            ):
                try:
                    await asyncio.wait_for(coroutine, timeout=per_step_budget)
                    outcome.steps[step_name] = "ok"
                except asyncio.TimeoutError:
                    outcome.steps[step_name] = "timeout"
                except Exception as exc:
                    outcome.steps[step_name] = f"{type(exc).__name__}"
                if progress is not None:
                    progress({
                        "done": sum(len(o.steps) for o in outcomes) + len(outcome.steps),
                        "total": len(codes) * 4,
                        "current_code": code,
                        "current_step": step_name,
                        "outcomes": [o.as_dict() for o in outcomes] + [outcome.as_dict()],
                    })
            outcomes.append(outcome)
        elapsed = (datetime.now(UTC) - started).total_seconds()
        ok = sum(1 for o in outcomes if all(v == "ok" for v in o.steps.values()))
        return {
            "slice_size": len(codes),
            "stocks_ok": ok,
            "stocks_partial": sum(1 for o in outcomes if o.steps and any(v != "ok" for v in o.steps.values())),
            "outcomes": [o.as_dict() for o in outcomes],
            "coverage_start": start.isoformat(),
            "coverage_end": end.isoformat(),
            "elapsed_s": round(elapsed, 1),
        }


def get_events_service() -> IntelligenceEventsService:
    from app.services.intelligence_events import get_intelligence_events_service

    return get_intelligence_events_service()

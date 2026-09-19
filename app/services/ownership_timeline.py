from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from functools import lru_cache

from app.config import get_settings
from app.models import (
    OwnershipFilerTimeline,
    OwnershipMovement,
    OwnershipTimelineMetadata,
    OwnershipTimelineResponse,
)
from app.storage.disclosure_interests import DisclosureInterestRepository
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.normalize import normalize_stock_code

DEFAULT_LOOKBACK_DAYS = 5 * 365


class OwnershipTimelineService:
    """🥈 DI/Ownership engine: turns persisted official DION rows into a
    per-filer 5-year increase/decrease timeline — CCASS inference becomes
    official fact."""

    def __init__(self, disclosure_repository: DisclosureInterestRepository | None = None):
        self.disclosure_repository = disclosure_repository or DisclosureInterestRepository(NormalizedSnapshotRepository(get_settings().ccass_sqlite_path))

    async def get_timeline(
        self,
        code: str | int,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        filer: str | None = None,
    ) -> OwnershipTimelineResponse:
        normalized = normalize_stock_code(code)
        end = end_date or datetime.now(UTC).date()
        start = start_date or end - timedelta(days=DEFAULT_LOOKBACK_DAYS)
        warnings: list[str] = []
        try:
            rows = self.disclosure_repository.load_rows(normalized, start_date=start, end_date=end)
        except Exception as exc:
            return OwnershipTimelineResponse(metadata=OwnershipTimelineMetadata(code=normalized, fetched_at=datetime.now(UTC), source_status="unavailable", coverage_start=start, coverage_end=end), data_quality_warnings=[f"DI_SOURCE_READ_FAILED:{type(exc).__name__}"])

        if filer:
            needle = filer.casefold()
            rows = [row for row in rows if needle in row.filer.casefold()]

        by_filer: dict[str, list] = {}
        for row in rows:
            by_filer.setdefault(row.filer, []).append(row)

        timelines: list[OwnershipFilerTimeline] = []
        for filer_name, filer_rows in by_filer.items():
            filer_rows.sort(key=lambda row: row.event_date)
            movements: list[OwnershipMovement] = []
            increases = decreases = 0
            for row in filer_rows:
                if row.previous_balance is not None and row.present_balance is not None:
                    change = row.present_balance - row.previous_balance
                    direction = "increase" if change > 0 else ("decrease" if change < 0 else "unknown")
                else:
                    change = None
                    direction = "unknown"
                if direction == "increase":
                    increases += 1
                elif direction == "decrease":
                    decreases += 1
                movements.append(OwnershipMovement(
                    event_date=row.event_date,
                    filing_id=row.filing_id,
                    direction=direction,
                    change_shares=change,
                    shares_involved=row.shares_involved,
                    previous_balance=row.previous_balance,
                    present_balance=row.present_balance,
                    percentage=row.percentage,
                    average_price=row.average_price,
                    reason=row.reason,
                    source_url=row.source_url,
                ))
            latest = filer_rows[-1]
            timelines.append(OwnershipFilerTimeline(
                filer=filer_name,
                classification=latest.classification,
                first_seen=filer_rows[0].event_date,
                last_seen=latest.event_date,
                movements_count=len(movements),
                increases=increases,
                decreases=decreases,
                latest_present_balance=latest.present_balance,
                latest_percentage=latest.percentage,
                movements=list(reversed(movements)),
            ))
        timelines.sort(key=lambda t: (t.latest_present_balance or 0), reverse=True)
        status = "ready" if timelines else "unavailable"
        if not timelines:
            warnings.append("NO_OWNERSHIP_MOVEMENTS: no DION filings for this code and window")
        return OwnershipTimelineResponse(
            metadata=OwnershipTimelineMetadata(
                code=normalized,
                fetched_at=datetime.now(UTC),
                source_status=status,
                filers=len(timelines),
                movements=sum(t.movements_count for t in timelines),
                coverage_start=start,
                coverage_end=end,
            ),
            timelines=timelines,
            data_quality_warnings=warnings,
        )


@lru_cache
def get_ownership_timeline_service() -> OwnershipTimelineService:
    settings = get_settings()
    return OwnershipTimelineService(DisclosureInterestRepository(NormalizedSnapshotRepository(settings.ccass_sqlite_path)))

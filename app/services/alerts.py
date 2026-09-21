from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.models import IntelligenceEventsResponse
from ccass_core.normalize import normalize_stock_code

# Alert rules are deliberately conservative and labelled: the intelligence
# event layer is facts-only, so every alert restates facts (never advice).
LARGE_DI_CHANGE_SHARES = 5_000_000
BASELINE_LOOKBACK_DAYS = 120  # chain DI balances against a longer baseline
DI_EVENT_TYPE = "disclosure_of_interest"
SHARE_CAPITAL_EVENT_TYPE = "share_capital_change"
RESULTS_EVENT_TYPE = "announcement:results"


class AlertsService:
    """Monitor/Alerts v0 (§8 item 6): derives labelled alert cards from the
    persisted intelligence event layer — no new fetching, no advice."""

    def __init__(self, events_service):
        self.events_service = events_service

    async def get_alerts(self, code: str | int, *, days: int = 7, end_date: date | None = None) -> dict:
        normalized = normalize_stock_code(code)
        end = end_date or datetime.now(UTC).date()
        start = end - timedelta(days=max(days, 1))
        baseline_start = start - timedelta(days=BASELINE_LOOKBACK_DAYS)

        response: IntelligenceEventsResponse = await self.events_service.get_events(normalized, start_date=baseline_start, end_date=end)
        events = response.events

        alerts: list[dict] = []

        # DI: chain each counterparty's disclosed balance across time, then
        # flag movements that fall inside the requested alert window.
        di_series: dict[str, list] = {}
        for event in events:
            if event.event_type == DI_EVENT_TYPE and event.counterparty:
                di_series.setdefault(event.counterparty, []).append(event)
        for counterparty, series in di_series.items():
            series.sort(key=lambda e: e.announce_date)
            previous: int | None = None
            for event in series:
                present = event.shares_after
                if present is not None and previous is not None:
                    change = present - previous
                    direction = "增持" if change > 0 else ("減持" if change < 0 else "持平")
                else:
                    change = None
                    direction = None
                if start <= event.announce_date <= end and direction in ("增持", "減持"):
                    severity = "notable" if abs(change) >= LARGE_DI_CHANGE_SHARES else "info"
                    alerts.append({
                        "type": "di_movement",
                        "severity": severity,
                        "date": event.announce_date.isoformat(),
                        "title": f"{counterparty} {direction} {abs(change):,} 股（現持 {present:,}）",
                        "facts": {
                            "counterparty": counterparty,
                            "present_balance": present,
                            "previous_balance": previous,
                            "change": change,
                            "price": event.price,
                        },
                        "confidence": event.confidence,
                        "source_document": event.source_document,
                        "source_url": event.source_url,
                    })
                if present is not None:
                    previous = present

        # Share-capital + results events: surface any inside the window.
        for event in events:
            if event.announce_date < start or event.announce_date > end:
                continue
            if event.event_type == SHARE_CAPITAL_EVENT_TYPE:
                alerts.append({
                    "type": "share_capital_change",
                    "severity": "info",
                    "date": event.announce_date.isoformat(),
                    "title": f"股本變動 {event.shares_after}M",
                    "facts": {"shares_million": event.shares_after, "ratio": event.ratio},
                    "confidence": event.confidence,
                    "source_document": event.source_document,
                    "source_url": event.source_url,
                })
            elif event.event_type == RESULTS_EVENT_TYPE:
                alerts.append({
                    "type": "results_announcement",
                    "severity": "info",
                    "date": event.announce_date.isoformat(),
                    "title": "業績公告刊發",
                    "facts": {"source_document": event.source_document},
                    "confidence": event.confidence,
                    "source_document": event.source_document,
                    "source_url": event.source_url,
                })

        alerts.sort(key=lambda a: a["date"], reverse=True)
        notable = sum(1 for a in alerts if a["severity"] == "notable")
        return {
            "code": normalized,
            "window_days": days,
            "window": {"start": start.isoformat(), "end": end.isoformat()},
            "alert_count": len(alerts),
            "notable_count": notable,
            "alerts": alerts,
            "disclaimer": "報時工具：話你知邊度有官方申報/公告變動，唔構成買賣建議。訊號本身無超額報酬（616 樣本 p=0.600）。",
        }

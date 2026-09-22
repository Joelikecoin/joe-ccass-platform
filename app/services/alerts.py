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
        streak_threshold = 3
        for counterparty, series in di_series.items():
            series.sort(key=lambda e: e.announce_date)
            previous: int | None = None
            prev_pct: float | None = None
            directions: list[str] = []  # chained, unknown excluded
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

                # v1 rule: 5% disclosure-line crossings (both ways)
                event_pct = getattr(event, "percentage", None)
                if start <= event.announce_date <= end and event_pct is not None and prev_pct is not None:
                    crossed_up = prev_pct < 5 <= event.percentage
                    crossed_down = prev_pct >= 5 > event.percentage
                    if crossed_up or crossed_down:
                        alerts.append({
                            "type": "filing_threshold_cross",
                            "severity": "notable",
                            "date": event.announce_date.isoformat(),
                            "title": f"{counterparty} {'升至' if crossed_up else '跌穿'} 5% 申報線（{prev_pct:.2f}% → {event_pct:.2f}%）",
                            "facts": {"counterparty": counterparty, "previous_percentage": prev_pct, "percentage": event_pct},
                            "confidence": event.confidence,
                            "source_document": event.source_document,
                            "source_url": event.source_url,
                        })

                # v1 rule: new filer — first-ever disclosure inside the window
                if start <= event.announce_date <= end and previous is None and present is not None and len(series) >= 2:
                    alerts.append({
                        "type": "new_filer",
                        "severity": "info",
                        "date": event.announce_date.isoformat(),
                        "title": f"{counterparty} 首次出現申報（現持 {present:,}）",
                        "facts": {"counterparty": counterparty, "present_balance": present},
                        "confidence": event.confidence,
                        "source_document": event.source_document,
                        "source_url": event.source_url,
                    })

                if present is not None:
                    previous = present
                if direction in ("增持", "減持"):
                    directions.append(direction)
                if getattr(event, "percentage", None) is not None:
                    prev_pct = getattr(event, "percentage", None)

            # v1 rule: sustained direction streak (trailing same-direction run)
            if directions:
                trailing_kind = directions[-1]
                run = 0
                for d in reversed(directions):
                    if d == trailing_kind:
                        run += 1
                    else:
                        break
                if run >= streak_threshold and trailing_kind in ("增持", "減持"):
                    alerts.append({
                        "type": "direction_streak",
                        "severity": "notable",
                        "date": series[-1].announce_date.isoformat(),
                        "title": f"{counterparty} 連續 {run} 次{trailing_kind} — {'持續收貨模式' if trailing_kind == '增持' else '持續減持模式'}",
                        "facts": {"counterparty": counterparty, "streak": run, "direction": trailing_kind},
                        "confidence": "derived",
                        "source_document": "chained DION series",
                        "source_url": series[-1].source_url,
                    })

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

        # v2 rule: cumulative net flow per counterparty inside the window —
        # many small same-direction moves add up even when each is small.
        net_flow: dict[str, int] = {}
        for counterparty, series in di_series.items():
            series.sort(key=lambda e: e.announce_date)
            previous: int | None = None
            window_net = 0
            for event in series:
                present = event.shares_after
                if present is not None and previous is not None:
                    if start <= event.announce_date <= end:
                        window_net += present - previous
                if present is not None:
                    previous = present
            if window_net != 0:
                net_flow[counterparty] = window_net
        for counterparty, net in sorted(net_flow.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]:
            if abs(net) < LARGE_DI_CHANGE_SHARES:
                continue
            direction = "淨增持" if net > 0 else "淨減持"
            alerts.append({
                "type": "net_flow",
                "severity": "notable",
                "date": end.isoformat(),
                "title": f"{counterparty} 窗口內{direction} {abs(net):,} 股（累計申報差）",
                "facts": {"counterparty": counterparty, "net_shares": net},
                "confidence": "derived",
                "source_document": "chained DION series",
                "source_url": "",
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

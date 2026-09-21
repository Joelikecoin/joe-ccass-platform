from datetime import date, datetime, timedelta, UTC
from types import SimpleNamespace

import pytest

from app.services.alerts import AlertsService


def _event(event_type, announce_date, counterparty=None, entity_name=None, shares_after=None, source_document="DOC"):
    from types import SimpleNamespace

    return SimpleNamespace(
        event_type=event_type,
        announce_date=announce_date,
        counterparty=counterparty,
        entity_name=entity_name,
        shares_after=shares_after,
        shares_before=None,
        price=None,
        ratio=None,
        confidence="official",
        source_document=source_document,
        source_url=f"https://di.hkex.com.hk/{source_document}",
        data_quality_warnings=[],
    )


class _FakeEvents:
    def __init__(self, events):
        self.events = events

    async def get_events(self, code, *, start_date=None, end_date=None):
        return SimpleNamespace(metadata=SimpleNamespace(event_count=len(self.events)), events=self.events, data_quality_warnings=[])


@pytest.mark.asyncio
async def test_alerts_chain_balances_and_flag_window_movements():
    today = date(2026, 9, 19)
    # BlackRock chain: baseline (outside 7d window) -> two moves inside it
    events = [
        _event("disclosure_of_interest", today - timedelta(days=90), counterparty="BlackRock, Inc.", shares_after=1_000_000_000),
        _event("disclosure_of_interest", today - timedelta(days=10), counterparty="BlackRock, Inc.", shares_after=1_010_000_000),
        _event("disclosure_of_interest", today - timedelta(days=2), counterparty="BlackRock, Inc.", shares_after=1_016_000_000),
        _event("disclosure_of_interest", today - timedelta(days=2), counterparty="Lei Jun", shares_after=3_989_013_134),
        _event("announcement:results", today - timedelta(days=1)),
        _event("share_capital_change", today - timedelta(days=3), shares_after=10_295),
    ]
    service = AlertsService(_FakeEvents(events))
    result = await service.get_alerts("02318", days=7, end_date=today)

    assert result["alert_count"] == 3  # 1 DI in-window + share capital + results
    di_alerts = [a for a in result["alerts"] if a["type"] == "di_movement"]
    assert len(di_alerts) == 1
    newest = di_alerts[0]
    assert newest["title"].startswith("BlackRock, Inc. 增持 6,000,000")  # chained: 1.01B -> 1.016B
    assert newest["severity"] == "notable"  # 6M >= 5M threshold
    assert newest["facts"]["previous_balance"] == 1_010_000_000  # baseline chained from the day-10 filing
    assert "p=0.600" in result["disclaimer"]


@pytest.mark.asyncio
async def test_alerts_empty_window_reports_zero_with_disclaimer():
    service = AlertsService(_FakeEvents([]))
    result = await service.get_alerts("00941", days=7, end_date=date(2026, 9, 19))
    assert result["alert_count"] == 0
    assert result["disclaimer"]

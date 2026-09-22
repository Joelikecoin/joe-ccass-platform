from datetime import date, datetime, timedelta, UTC
from types import SimpleNamespace

import pytest

from app.services.alerts import AlertsService


def _event(event_type, announce_date, counterparty=None, entity_name=None, shares_after=None, source_document="DOC", percentage=None):
    from types import SimpleNamespace

    return SimpleNamespace(
        percentage=percentage,
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

    assert result["alert_count"] == 4  # 1 DI + share capital + results + BlackRock net-flow (10M+6M = 淨增持 16M, notable)
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


def _pct_event(event_date, counterparty, present, percentage):
    return _event("disclosure_of_interest", event_date, counterparty=counterparty, shares_after=present) | {}


def _di(announce_date, counterparty, present, percentage=None):
    from types import SimpleNamespace

    return SimpleNamespace(
        event_type="disclosure_of_interest",
        announce_date=announce_date,
        counterparty=counterparty,
        entity_name=None,
        shares_after=present,
        shares_before=None,
        price=None,
        ratio=None,
        confidence="official",
        source_document=f"D-{counterparty[:6]}-{announce_date}",
        source_url="https://di.hkex.com.hk/x",
        data_quality_warnings=[],
        percentage=percentage,
    )


@pytest.mark.asyncio
async def test_alerts_v1_sustained_streak_rule():
    today = date(2026, 9, 19)
    events = [
        _di(today - timedelta(days=60), "Quiet Holder", 100),
        _di(today - timedelta(days=40), "BlackRock, Inc.", 500_000_000),
        _di(today - timedelta(days=30), "BlackRock, Inc.", 502_000_000),
        _di(today - timedelta(days=20), "BlackRock, Inc.", 505_000_000),
        _di(today - timedelta(days=10), "BlackRock, Inc.", 510_000_000),
    ]
    result = await AlertsService(_FakeEvents(events)).get_alerts("02318", days=7, end_date=today)
    streaks = [a for a in result["alerts"] if a["type"] == "direction_streak"]
    assert len(streaks) == 1
    assert "連續 3 次增持" in streaks[0]["title"]
    assert streaks[0]["severity"] == "notable"


@pytest.mark.asyncio
async def test_alerts_v1_new_filer_rule():
    today = date(2026, 9, 19)
    events = [
        _di(today - timedelta(days=3), "New Face Capital", 12_000_000),
        _di(today - timedelta(days=1), "New Face Capital", 12_500_000),
    ]
    result = await AlertsService(_FakeEvents(events)).get_alerts("02318", days=30, end_date=today)
    new_filers = [a for a in result["alerts"] if a["type"] == "new_filer"]
    assert len(new_filers) == 1
    assert "首次出現申報" in new_filers[0]["title"]


@pytest.mark.asyncio
async def test_alerts_v1_filing_threshold_cross_rule():
    today = date(2026, 9, 19)
    events = [
        _di(today - timedelta(days=10), "Crossing Fund", 49_000_000, percentage=4.88),
        _di(today - timedelta(days=2), "Crossing Fund", 51_500_000, percentage=5.14),
    ]
    result = await AlertsService(_FakeEvents(events)).get_alerts("02318", days=30, end_date=today)
    crossings = [a for a in result["alerts"] if a["type"] == "filing_threshold_cross"]
    assert len(crossings) == 1
    assert "跌穿" in crossings[0]["title"] or "升至" in crossings[0]["title"]
    assert crossings[0]["severity"] == "notable"

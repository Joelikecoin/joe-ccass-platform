from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.portal_8504 import app as portal_app
from app.services.accumulation import AccumulationService


def test_today_slice_rotates_deterministically():
    watchlist = tuple(f"{1000 + i}" for i in range(52))
    service = AccumulationService(watchlist=watchlist)
    day_a = service.today_slice(count=13, day_index=0)
    day_b = service.today_slice(count=13, day_index=1)
    assert len(day_a) == 13 and len(day_b) == 13
    assert day_a[0] == "1000" and day_b[0] == "1013"
    assert not set(day_a) & set(day_b)
    assert service.today_slice(count=13, day_index=4) == day_a  # full rotation wraps


class _D:
    async def get_disclosures(self, code, *, start_date, end_date):
        return SimpleNamespace()


class _A:
    async def get_announcements(self, code, *, start_date, end_date):
        return SimpleNamespace()


class _F:
    async def get_fundamentals(self, code):
        raise RuntimeError("upstream")


class _E:
    async def get_events(self, code, *, start_date=None, end_date=None):
        return SimpleNamespace(metadata=SimpleNamespace(event_count=0), events=[], data_quality_warnings=[])


@pytest.mark.asyncio
async def test_accumulation_run_reports_per_stock_outcomes():
    service = AccumulationService(
        watchlist=("02020", "00941"),
        disclosure_service=_D(),
        announcements_service=_A(),
        fundamentals_service=_F(),
        events_service=_E(),
    )
    result = await service.run(count=2)

    assert result["slice_size"] == 2
    assert result["stocks_ok"] == 0   # fundamentals fails on every stock in this fixture
    assert result["stocks_partial"] == 2
    for outcome in result["outcomes"]:
        assert outcome["di"] == "ok"
        assert outcome["events"] == "ok"
        assert outcome["fundamentals"] == "RuntimeError"  # isolated, never aborts the run


def test_accumulation_service_isolates_step_failures():
    # a per-stock failure must not abort remaining stocks — enforced by design
    service = AccumulationService(watchlist=("02020",), disclosure_service=_D(), announcements_service=_A(), fundamentals_service=_F(), events_service=_E())
    import asyncio

    outcomes = asyncio.run(service.run(count=1))
    assert len(outcomes["outcomes"]) == 1


def test_console_page_renders_without_code():
    client = TestClient(portal_app)
    response = client.get("/console")
    assert response.status_code == 200
    assert "Joe Intelligence Console" in response.text
    assert "Enter a stock code" in response.text


def test_accumulation_job_routes_require_auth(monkeypatch):
    monkeypatch.setattr(
        "app.portal_8504.get_settings",
        lambda: SimpleNamespace(api_key="configured", request_timeout_seconds=90.0),
    )
    monkeyclient = TestClient(portal_app)
    assert monkeyclient.post("/admin/accumulation/job").status_code == 401
    assert monkeyclient.get("/admin/accumulation/job/nope").status_code == 401

import hashlib
import logging
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.daily_snapshot import CAIJI, LSHAPE79, daily_watchlist, run_daily_snapshot
from app.portal_8504 import app as portal_app


class FakeService:
    def __init__(self, failures=()):
        self.calls = []
        self.failures = set(failures)

    async def fetch_and_persist(self, code):
        self.calls.append(code)
        if code in self.failures:
            raise RuntimeError("upstream unavailable")
        return SimpleNamespace(
            metadata=SimpleNamespace(holdings_date=date(2026, 9, 10)),
            holdings=[object(), object()],
        )


def test_daily_watchlist_is_deduplicated_and_excludes_research():
    codes = daily_watchlist()
    assert len(LSHAPE79) == 25
    assert len(CAIJI) == 28
    assert len(codes) == 52
    assert len(codes) == len(set(codes))
    assert all(len(code) == 5 and code.isdigit() for code in codes)


@pytest.mark.asyncio
async def test_daily_snapshot_holiday_skips_all_source_calls(monkeypatch):
    monkeypatch.setattr(
        "app.daily_snapshot.hkt_now",
        lambda: __import__("datetime").datetime(
            2026, 9, 12, tzinfo=__import__("zoneinfo").ZoneInfo("Asia/Hong_Kong")
        ),
    )
    monkeypatch.setattr("app.daily_snapshot.is_trading_day", lambda _: False)
    service = FakeService()

    result = await run_daily_snapshot(("00005", "06182"), service=service)

    assert result["status"] == "skipped_holiday"
    assert result["next_trading_day"]
    assert service.calls == []


@pytest.mark.asyncio
async def test_daily_snapshot_isolates_failure_and_retries_once(monkeypatch):
    monkeypatch.setattr(
        "app.daily_snapshot.hkt_now",
        lambda: __import__("datetime").datetime(
            2026, 9, 10, tzinfo=__import__("zoneinfo").ZoneInfo("Asia/Hong_Kong")
        ),
    )
    monkeypatch.setattr("app.daily_snapshot.is_trading_day", lambda _: True)
    service = FakeService(failures={"06182"})

    result = await run_daily_snapshot(("00005", "06182"), service=service, pacing_seconds=0)

    assert result["status"] == "partial"
    assert result["succeeded"] == 1
    assert result["failed"] == 1
    assert service.calls == ["00005", "06182", "06182"]
    assert result["results"][0]["persist_status"] == "persisted"
    assert result["results"][1]["status"] == "ERROR"


def test_snapshot_watchlist_requires_configured_auth(monkeypatch):
    monkeypatch.setattr(
        "app.portal_8504.get_settings", lambda: SimpleNamespace(api_key="configured")
    )
    response = TestClient(portal_app).post("/admin/longbridge/snapshot_watchlist")
    assert response.status_code == 401


def test_snapshot_watchlist_bounds_controlled_rollout(monkeypatch):
    monkeypatch.setattr(
        "app.portal_8504.get_settings", lambda: SimpleNamespace(api_key="configured")
    )
    response = TestClient(portal_app).post(
        "/admin/longbridge/snapshot_watchlist?key=configured&stocks=00005,06182,00700"
    )
    assert response.status_code == 400


def test_failed_scheduler_auth_logs_only_request_fingerprint(monkeypatch, caplog):
    expected = "expected-production-key"
    supplied = "supplied-request-key"
    monkeypatch.setattr(
        "app.portal_8504.get_settings", lambda: SimpleNamespace(api_key=expected)
    )

    with caplog.at_level(logging.WARNING, logger="app.portal_8504"):
        response = TestClient(portal_app).post(
            "/admin/longbridge/snapshot_watchlist",
            headers={"X-API-Key": supplied},
        )

    assert response.status_code == 401
    assert response.json()["error_code"] == "AUTH_FAILED"
    assert "AUTH_FAILED EXPECTED_KEY_PRESENT=yes" in caplog.text
    assert "EXPECTED_KEY_LENGTH=23" in caplog.text
    assert (
        f"EXPECTED_KEY_SHA256_PREFIX={hashlib.sha256(expected.encode()).hexdigest()[:8]}"
        in caplog.text
    )
    assert "REQUEST_KEY_PRESENT=yes" in caplog.text
    assert "REQUEST_KEY_LENGTH=20" in caplog.text
    assert (
        f"REQUEST_KEY_SHA256_PREFIX={hashlib.sha256(supplied.encode()).hexdigest()[:8]}"
        in caplog.text
    )
    assert "AUTH_SOURCE=x_api_key" in caplog.text
    assert expected not in caplog.text
    assert supplied not in caplog.text


def test_settings_startup_log_contains_only_api_key_fingerprint(monkeypatch, caplog):
    secret = "startup-secret-value"
    monkeypatch.setenv("API_KEY", secret)
    from app.config import get_settings

    get_settings.cache_clear()
    with caplog.at_level(logging.INFO, logger="app.config"):
        settings = get_settings()

    assert settings.api_key == secret
    assert "API_KEY_PRESENT=yes" in caplog.text
    assert "API_KEY_LENGTH=20" in caplog.text
    assert f"API_KEY_SHA256_PREFIX={hashlib.sha256(secret.encode()).hexdigest()[:8]}" in caplog.text
    assert secret not in caplog.text
    get_settings.cache_clear()


def test_snapshot_watchlist_dispatches_background_job(monkeypatch):
    monkeypatch.setattr(
        "app.portal_8504.get_settings", lambda: SimpleNamespace(api_key="configured")
    )
    jobs = []

    def fake_create_task(coro):
        jobs.append(coro)
        coro.close()
        return None

    monkeypatch.setattr("app.portal_8504.asyncio.create_task", fake_create_task)
    response = TestClient(portal_app).post(
        "/admin/longbridge/snapshot_watchlist?key=configured&stocks=00005,06182&dry_run=true"
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"
    assert body["state"] == "running"
    assert body["job_id"]
    assert len(jobs) == 1


def test_snapshot_job_status_requires_auth_and_returns_progress(monkeypatch):
    monkeypatch.setattr(
        "app.portal_8504.get_settings", lambda: SimpleNamespace(api_key="configured")
    )
    monkeypatch.setattr("app.portal_8504.asyncio.create_task", lambda coro: coro.close())
    response = TestClient(portal_app).post(
        "/admin/longbridge/snapshot_watchlist?key=configured&stocks=00005&dry_run=true"
    )
    job_id = response.json()["job_id"]

    unauthenticated = TestClient(portal_app).get(f"/admin/longbridge/snapshot_job/{job_id}")
    authenticated = TestClient(portal_app).get(
        f"/admin/longbridge/snapshot_job/{job_id}?key=configured"
    )

    assert unauthenticated.status_code == 401
    assert authenticated.status_code == 200
    assert authenticated.json()["job_id"] == job_id
    assert "current_code" in authenticated.json()

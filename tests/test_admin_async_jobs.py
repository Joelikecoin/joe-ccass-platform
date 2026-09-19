from datetime import date, datetime, UTC, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.portal_8504 import (
    _announcements_jobs,
    _announcements_jobs_lock,
    _fundamentals_jobs,
    _fundamentals_jobs_lock,
    _run_announcements_job,
    _run_fundamentals_job,
    app as portal_app,
)


def _settings():
    return SimpleNamespace(api_key="configured", request_timeout_seconds=90.0)


class _FakeFundamentalsService:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    async def get_fundamentals(self, code):
        if self.error is not None:
            raise self.error
        return self.response


class _FakeAnnouncementsService:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    async def get_announcements(self, code, *, start_date, end_date):
        if self.error is not None:
            raise self.error
        return self.response


def _fundamentals_response(status="ready"):
    metadata = SimpleNamespace(source_status=status, documents_attempted=4, documents_parsed=4, documents_failed=0)
    rows = [SimpleNamespace(reporting_period="2025-FY"), SimpleNamespace(reporting_period="2025-H1")]
    return SimpleNamespace(metadata=metadata, rows=rows, data_quality_warnings=["DISCOVERY_CAPPED: ..."])


def _announcements_response(status="ready"):
    metadata = SimpleNamespace(source_status=status, announcement_count=236, coverage_start=date(2024, 9, 18), coverage_end=date(2026, 9, 18))
    return SimpleNamespace(metadata=metadata, announcements=[object() for _ in range(236)], data_quality_warnings=[])


def _register(store, lock, job_id, **extra):
    with lock:
        store[job_id] = {"job_id": job_id, "state": "running", "error": None, "warnings": [], "elapsed_s": 0.0, **extra}


@pytest.mark.asyncio
async def test_fundamentals_job_runner_succeeds(monkeypatch):
    monkeypatch.setattr("app.portal_8504.get_settings", _settings)
    fake = _FakeFundamentalsService(response=_fundamentals_response())
    monkeypatch.setattr("app.portal_8504.get_fundamentals_service", lambda: fake)
    _register(_fundamentals_jobs, _fundamentals_jobs_lock, "f-ok")

    await _run_fundamentals_job("f-ok", "00941", service=fake)

    job = _fundamentals_jobs["f-ok"]
    assert job["state"] == "succeeded"
    assert job["rows"] == 2
    assert job["periods"] == ["2025-FY", "2025-H1"]
    assert job["documents_attempted"] == 4


@pytest.mark.asyncio
async def test_fundamentals_job_runner_reports_partial(monkeypatch):
    monkeypatch.setattr("app.portal_8504.get_settings", _settings)
    fake = _FakeFundamentalsService(response=_fundamentals_response(status="partial"))
    monkeypatch.setattr("app.portal_8504.get_fundamentals_service", lambda: fake)
    _register(_fundamentals_jobs, _fundamentals_jobs_lock, "f-partial")

    await _run_fundamentals_job("f-partial", "00941", service=fake)

    assert _fundamentals_jobs["f-partial"]["state"] == "partial"


@pytest.mark.asyncio
async def test_fundamentals_job_runner_marks_error(monkeypatch):
    monkeypatch.setattr("app.portal_8504.get_settings", _settings)
    fake = _FakeFundamentalsService(error=RuntimeError("boom"))
    monkeypatch.setattr("app.portal_8504.get_fundamentals_service", lambda: fake)
    _register(_fundamentals_jobs, _fundamentals_jobs_lock, "f-err")

    await _run_fundamentals_job("f-err", "00941", service=fake)

    job = _fundamentals_jobs["f-err"]
    assert job["state"] == "error"
    assert "RuntimeError" in job["error"]


@pytest.mark.asyncio
async def test_announcements_job_runner_succeeds(monkeypatch):
    monkeypatch.setattr("app.portal_8504.get_settings", _settings)
    fake = _FakeAnnouncementsService(response=_announcements_response())
    monkeypatch.setattr("app.portal_8504.get_announcements_service", lambda: fake)
    _register(_announcements_jobs, _announcements_jobs_lock, "a-ok")

    await _run_announcements_job("a-ok", "02318", date(2024, 9, 18), date(2026, 9, 18), service=fake)

    job = _announcements_jobs["a-ok"]
    assert job["state"] == "succeeded"
    assert job["announcement_count"] == 236
    assert job["coverage_start"] == "2024-09-18"
    assert job["coverage_end"] == "2026-09-18"


def test_async_job_routes_require_auth(monkeypatch):
    monkeypatch.setattr("app.portal_8504.get_settings", _settings)
    client = TestClient(portal_app)
    assert client.post("/admin/fundamentals/job?stock_code=00941").status_code == 401
    assert client.post("/admin/announcements/job?stock_code=02318").status_code == 401


def test_announcements_job_rejects_oversized_window(monkeypatch):
    monkeypatch.setattr("app.portal_8504.get_settings", _settings)
    client = TestClient(portal_app)
    response = client.post(
        "/admin/announcements/job?key=configured&stock_code=02318&start_date=2016-09-18&end_date=2026-09-18"
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_SCHEMA"


def test_async_job_status_unknown_returns_404(monkeypatch):
    monkeypatch.setattr("app.portal_8504.get_settings", _settings)
    client = TestClient(portal_app)
    assert client.get("/admin/fundamentals/job/nope?key=configured").status_code == 404
    assert client.get("/admin/announcements/job/nope?key=configured").status_code == 404

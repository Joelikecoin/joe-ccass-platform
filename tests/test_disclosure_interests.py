import asyncio
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.models import DisclosureInterestRow, DisclosureInterestsMetadata, DisclosureInterestsResponse
from app.portal_8504 import (
    _disclosure_interests_jobs,
    _disclosure_interests_jobs_lock,
    _run_disclosure_interests_job,
    app as portal_app,
)
from app.services.disclosure_interests import DisclosureInterestsService, get_disclosure_interests_service
from app.sources.disclosure_interests import HKEXDisclosureInterestsSource, SEARCH


def _ready_response(code: str = "00388") -> DisclosureInterestsResponse:
    retrieved = datetime(2026, 9, 18, tzinfo=UTC)
    row = DisclosureInterestRow(
        filing_id="CS20260824E00178",
        stock_code=code,
        event_date=date(2026, 8, 19),
        filer="JPMorgan Chase & Co.",
        classification="substantial_shareholder",
        shares_involved=775802,
        present_balance=101583554,
        percentage=8.01,
        source_url="https://di.hkex.com.hk/di/NSForm2.aspx?fn=CS20260824E00178",
        retrieved_at=retrieved,
    )
    metadata = DisclosureInterestsMetadata(
        code=code,
        source_url=SEARCH,
        fetched_at=retrieved,
        source_status="ready",
        filing_count=1,
    )
    return DisclosureInterestsResponse(metadata=metadata, filings=[row])


def _unavailable_response(code: str = "00388") -> DisclosureInterestsResponse:
    metadata = DisclosureInterestsMetadata(
        code=code,
        source_url=SEARCH,
        fetched_at=datetime(2026, 9, 18, tzinfo=UTC),
        source_status="unavailable",
        filing_count=0,
    )
    return DisclosureInterestsResponse(metadata=metadata, data_quality_warnings=["DION browser transport timed out"])


class _FakeRepository:
    def __init__(self, stored_rows: int = 0):
        self.stored_rows = stored_rows
        self.saved: list[DisclosureInterestsResponse] = []

    def save(self, response: DisclosureInterestsResponse) -> None:
        self.saved.append(response)

    def count_rows(self, stock_code: str) -> int:
        return self.stored_rows

    def load_rows(self, stock_code: str, *, start_date, end_date):
        return list(_ready_response().filings) if self.stored_rows else []


class _FakeService:
    def __init__(self, response=None, error=None):
        self.repository = _FakeRepository()
        self.response = response if response is not None else _ready_response()
        self.error = error
        self.calls: list[tuple] = []

    async def get_disclosures(self, code, *, start_date, end_date):
        self.calls.append((code, start_date, end_date))
        if self.error is not None:
            raise self.error
        self.repository.save(self.response)
        return self.response


def _register_job(job_id: str) -> None:
    with _disclosure_interests_jobs_lock:
        _disclosure_interests_jobs[job_id] = {
            "job_id": job_id,
            "state": "accepted",
            "stock_code": "00388",
            "start_date": "2024-09-18",
            "end_date": "2026-09-18",
            "filing_count": 0,
            "persisted_rows": None,
            "source_status": None,
            "warnings": [],
            "error": None,
            "elapsed_s": 0.0,
        }


def test_dion_result_parser_normalizes_official_row_shape():
    html = """
    <table><tr><th>Form Serial Number</th><th>Name</th><th>Reason</th><th>Shares</th>
    <th>Average price</th><th>Interested</th><th>%</th><th>Date</th></tr>
    <tr><td><a href="NSForm2.aspx?fn=CS20260824E00178">CS20260824E00178</a></td>
    <td>JPMorgan Chase &amp; Co.</td><td>1104 (L)</td><td>775,802(L)</td>
    <td>HKD 413.2018</td><td>101,583,554(L)</td><td>8.01(L)</td>
    <td><a href="NSForm2.aspx?fn=CS20260824E00178">19/08/2026</a></td></tr></table>
    """
    result = HKEXDisclosureInterestsSource()._parse_result("00388", html, date(2025, 1, 1), date(2026, 12, 31))
    assert len(result.filings) == 1
    row = result.filings[0]
    assert row.filer == "JPMorgan Chase & Co."
    assert row.event_date == date(2026, 8, 19)
    assert row.shares_involved == 775802
    assert row.present_balance == 101583554
    assert row.percentage == 8.01
    assert row.source_url.endswith("CS20260824E00178")


def test_dion_parser_reads_rows_nested_inside_real_result_layout():
    # Real DION wraps the data rows in nested tables inside one outer row; the
    # date column is not last, and Long/Short figures share a single cell.
    html = """
    <table><tr><td>
      <table>
        <tr><td>Form Serial Number</td><td>Name</td><td>Reason</td><td>Shares involved</td>
        <td>Average price</td><td>Shares interested</td><td>%</td><td>Date of relevant event</td>
        <td>Associated corporation</td><td>Debentures</td></tr>
        <tr><td><a href="NSForm2.aspx?fn=CS20260908E00043">CS20260908E00043</a></td>
        <td>BlackRock, Inc.</td><td>1205 (L)</td><td>726,000(L)</td><td></td>
        <td>1,065,871,110(L) 30,260,800(S)</td><td>4.99(L) 0.14(S)</td><td>03/09/2026</td><td></td><td></td></tr>
        <tr><td><a href="NSForm2.aspx?fn=DA20260811E00498">DA20260811E00498</a></td>
        <td>Lei Jun</td><td>1213 (L)</td><td>12,950,321(L)</td><td></td>
        <td>3,989,013,134(L)</td><td>90.06(L)</td><td>11/08/2026</td><td>Yes</td><td></td></tr>
      </table>
      Page 1 Displayed: 1 - 2 Total records: </span><span id="lblRecCount">554</span>
    </td></tr></table>
    """
    source = HKEXDisclosureInterestsSource()
    result = source._parse_result("01810", html, date(2018, 1, 1), date(2026, 12, 31))
    assert result.metadata.filing_count == 2
    blackrock = result.filings[0]
    assert blackrock.filing_id == "CS20260908E00043"
    assert blackrock.shares_involved == 726000
    assert blackrock.present_balance == 1065871110
    assert blackrock.percentage == 4.99
    assert blackrock.event_date == date(2026, 9, 3)
    leijun = result.filings[1]
    assert leijun.filing_id == "DA20260811E00498"
    assert leijun.present_balance == 3989013134
    assert leijun.percentage == 90.06
    assert source._total_records(html) == 554


def test_dion_total_records_matches_plain_text_and_span_shapes():
    assert HKEXDisclosureInterestsSource._total_records("x Total records: 554") == 554
    assert HKEXDisclosureInterestsSource._total_records('Total records: </span><span id="lblRecCount">1,234</span>') == 1234
    assert HKEXDisclosureInterestsSource._total_records("no counter here") is None


def test_dion_page_url_appends_and_replaces_pagination_param():
    base = "https://di.hkex.com.hk/di/NSAllFormList.aspx?sd=09%2f07%2f2018&sc=01810&g_lang=en&"
    assert HKEXDisclosureInterestsSource._page_url(base, 2).endswith("g_lang=en&pg=2")
    assert "pg=3" in HKEXDisclosureInterestsSource._page_url(base + "pg=2", 3)
    assert HKEXDisclosureInterestsSource._page_url("https://di.hkex.com.hk/di/NSSrchCorp.aspx?a=1", 2) is None


def test_dion_genuine_zero_returns_ready_with_no_rows():
    html = "<table><tr><td>No matching records. Total records: </span><span id='lblRecCount'>0</span></td></tr></table>"
    source = HKEXDisclosureInterestsSource()
    result = source._parse_result("00388", html, date(2024, 9, 18), date(2026, 9, 18))
    assert result.metadata.source_status == "ready"
    assert result.metadata.filing_count == 0
    assert result.filings == []


@pytest.mark.asyncio
async def test_di_job_runner_succeeds_and_reports_persisted_rows(monkeypatch):
    fake = _FakeService()
    fake.repository.stored_rows = 1
    monkeypatch.setattr("app.portal_8504.get_disclosure_interests_service", lambda: fake)
    _register_job("job-ok")

    await _run_disclosure_interests_job("job-ok", "00388", date(2024, 9, 18), date(2026, 9, 18))

    job = _disclosure_interests_jobs["job-ok"]
    assert job["state"] == "succeeded"
    assert job["filing_count"] == 1
    assert job["persisted_rows"] == 1
    assert job["source_status"] == "ready"
    assert job["error"] is None
    assert job["warnings"] == []
    assert fake.calls == [("00388", date(2024, 9, 18), date(2026, 9, 18))]
    assert len(fake.repository.saved) == 1


@pytest.mark.asyncio
async def test_di_job_runner_reports_unavailable_fail_loud(monkeypatch):
    fake = _FakeService(response=_unavailable_response())
    monkeypatch.setattr("app.portal_8504.get_disclosure_interests_service", lambda: fake)
    _register_job("job-unavailable")

    await _run_disclosure_interests_job("job-unavailable", "00388", date(2024, 9, 18), date(2026, 9, 18))

    job = _disclosure_interests_jobs["job-unavailable"]
    assert job["state"] == "unavailable"
    assert job["filing_count"] == 0
    assert job["source_status"] == "unavailable"
    assert "DION browser transport timed out" in job["warnings"]


@pytest.mark.asyncio
async def test_di_job_runner_marks_error_on_exception(monkeypatch):
    fake = _FakeService(error=RuntimeError("turso down"))
    monkeypatch.setattr("app.portal_8504.get_disclosure_interests_service", lambda: fake)
    _register_job("job-error")

    await _run_disclosure_interests_job("job-error", "00388", date(2024, 9, 18), date(2026, 9, 18))

    job = _disclosure_interests_jobs["job-error"]
    assert job["state"] == "error"
    assert "RuntimeError" in job["error"]


@pytest.mark.asyncio
async def test_di_job_runner_marks_error_on_budget_timeout(monkeypatch):
    class _SlowService(_FakeService):
        async def get_disclosures(self, code, *, start_date, end_date):
            await asyncio.sleep(0.5)
            return self.response

    fake = _SlowService()
    monkeypatch.setattr("app.portal_8504.get_disclosure_interests_service", lambda: fake)
    monkeypatch.setattr("app.portal_8504._di_job_timeout_budget", lambda: 0.05)
    _register_job("job-slow")

    await _run_disclosure_interests_job("job-slow", "00388", date(2024, 9, 18), date(2026, 9, 18))

    job = _disclosure_interests_jobs["job-slow"]
    assert job["state"] == "error"
    assert "budget" in job["error"]


def test_di_job_trigger_requires_configured_auth(monkeypatch):
    monkeypatch.setattr(
        "app.portal_8504.get_settings",
        lambda: SimpleNamespace(api_key="configured", request_timeout_seconds=90.0),
    )
    response = TestClient(portal_app).post("/admin/disclosure-interests/job?stock_code=00388")
    assert response.status_code == 401


def test_di_job_trigger_rejects_inverted_range(monkeypatch):
    monkeypatch.setattr(
        "app.portal_8504.get_settings",
        lambda: SimpleNamespace(api_key="configured", request_timeout_seconds=90.0),
    )
    monkeypatch.setattr("app.portal_8504.get_disclosure_interests_service", lambda: _FakeService())
    response = TestClient(portal_app).post(
        "/admin/disclosure-interests/job?key=configured&stock_code=00388&start_date=2026-09-18&end_date=2024-09-18"
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_SCHEMA"


def test_di_job_trigger_rejects_invalid_code(monkeypatch):
    monkeypatch.setattr(
        "app.portal_8504.get_settings",
        lambda: SimpleNamespace(api_key="configured", request_timeout_seconds=90.0),
    )
    response = TestClient(portal_app).post("/admin/disclosure-interests/job?key=configured&stock_code=NOPE")
    assert response.status_code == 422


def test_di_job_trigger_accepts_and_status_route_reports_job(monkeypatch):
    monkeypatch.setattr(
        "app.portal_8504.get_settings",
        lambda: SimpleNamespace(api_key="configured", request_timeout_seconds=90.0),
    )
    fake = _FakeService()
    monkeypatch.setattr("app.portal_8504.get_disclosure_interests_service", lambda: fake)

    response = TestClient(portal_app).post(
        "/admin/disclosure-interests/job?key=configured&stock_code=00388&start_date=2024-09-18&end_date=2026-09-18"
    )

    assert response.status_code == 202
    body = response.json()
    assert body["state"] == "running"
    assert body["stock_code"] == "00388"
    assert body["start_date"] == "2024-09-18"
    assert body["end_date"] == "2026-09-18"

    status = TestClient(portal_app).get(f"/admin/disclosure-interests/job/{body['job_id']}?key=configured")
    assert status.status_code == 200
    assert status.json()["job_id"] == body["job_id"]


def test_di_job_status_unknown_returns_404(monkeypatch):
    monkeypatch.setattr(
        "app.portal_8504.get_settings",
        lambda: SimpleNamespace(api_key="configured", request_timeout_seconds=90.0),
    )
    response = TestClient(portal_app).get("/admin/disclosure-interests/job/does-not-exist?key=configured")
    assert response.status_code == 404


def test_persisted_route_serves_rows_from_repository():
    class _PersistRepo(_FakeRepository):
        def load_rows(self, stock_code, *, start_date, end_date):
            assert stock_code == "00388"
            return list(_ready_response().filings)

    service = DisclosureInterestsService(repository=_PersistRepo())
    portal_app.dependency_overrides[get_disclosure_interests_service] = lambda: service
    try:
        response = TestClient(portal_app).get(
            "/api/v1/stocks/00388/disclosure-interests/persisted?start_date=2024-09-18&end_date=2026-09-18"
        )
    finally:
        portal_app.dependency_overrides.pop(get_disclosure_interests_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["source_status"] == "ready"
    assert body["metadata"]["source_name"] == "HKEX DION (persisted)"
    assert body["metadata"]["filing_count"] == 1
    assert body["filings"][0]["filing_id"] == "CS20260824E00178"


def test_persisted_route_reports_missing_rows_fail_loud():
    class _EmptyRepo(_FakeRepository):
        def load_rows(self, stock_code, *, start_date, end_date):
            return []

    service = DisclosureInterestsService(repository=_EmptyRepo())
    portal_app.dependency_overrides[get_disclosure_interests_service] = lambda: service
    try:
        response = TestClient(portal_app).get("/api/v1/stocks/00388/disclosure-interests/persisted")
    finally:
        portal_app.dependency_overrides.pop(get_disclosure_interests_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["source_status"] == "unavailable"
    assert body["metadata"]["filing_count"] == 0
    assert "NO_PERSISTED_ROWS" in body["data_quality_warnings"][0]

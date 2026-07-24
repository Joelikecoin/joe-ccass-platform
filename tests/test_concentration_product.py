from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.services.concentration import ConcentrationService, get_concentration_service
from app.sources.registry import build_source_registry
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.concentration_report import build_concentration_markdown_report


def _service(tmp_path, current_response, *, stale=False, partial=False):
    repository = NormalizedSnapshotRepository(tmp_path / "concentration.db")
    source = build_source_registry(Settings()).select_holdings("webbsite")[0]
    repository.save_response(
        current_response,
        source_id=source.source_id,
        parser_version=source.parser_version,
        stale=stale,
        partial=partial,
    )
    return ConcentrationService(repository, (source,)), repository, source


def test_concentration_calculates_complete_snapshot_ranking_and_summary(
    tmp_path,
    current_response,
):
    service, repository, _ = _service(tmp_path, current_response)

    result = service.get_concentration(
        "1592",
        snapshot_date=date(2026, 7, 20),
        top_holders_limit=2,
    )

    assert result.metadata.code == "01592"
    assert result.metadata.snapshot_date == date(2026, 7, 20)
    assert result.metadata.snapshot_source.source_id == "webbsite"
    assert result.metadata.snapshot_source.safe_identifier == "https://fixture.invalid/"
    assert result.metadata.snapshot_source.issued_shares == 10_000
    assert result.metadata.snapshot_source.issued_shares_as_of == date(2026, 7, 20)
    assert result.summary.model_dump() == {
        "participant_count": 3,
        "total_tracked_shares": 3_300,
        "total_tracked_pct_of_issued": 33.0,
        "total_tracked_pct_of_ccass": 100.0,
        "top1_pct_of_issued": 15.0,
        "top1_pct_of_ccass": 45.454545,
        "top5_pct_of_issued": 33.0,
        "top5_pct_of_ccass": 100.0,
        "top10_pct_of_issued": 33.0,
        "top10_pct_of_ccass": 100.0,
    }
    assert [row.rank for row in result.participant_ranking] == [1, 2, 3]
    assert [row.participant_id for row in result.top_holders] == ["B00001", "B00002"]
    assert result.diagnostics.validation_status == "COMPLETE"
    assert result.diagnostics.stale_data_used is False
    assert "TEST FIXTURE warning" in result.data_quality_warnings
    assert "CONCENTRATION_VALIDATION: COMPLETE" in result.data_quality_warnings
    assert repository.count_snapshots("01592") == 1


def test_concentration_top_holders_limit_does_not_change_full_ranking_or_totals(
    tmp_path,
    current_response,
):
    service, repository, _ = _service(tmp_path, current_response)

    result = service.get_concentration(
        "01592",
        snapshot_date=date(2026, 7, 20),
        top_holders_limit=1,
    )

    assert len(result.top_holders) == 1
    assert len(result.participant_ranking) == 3
    assert result.summary.participant_count == 3
    assert result.summary.total_tracked_shares == 3_300
    assert repository.count_snapshots("01592") == 1


def test_concentration_rejects_empty_snapshot(tmp_path, current_response):
    empty = current_response.model_copy(deep=True)
    empty.holdings = []
    summary = empty.holdings_summary
    summary.participant_count = 0
    summary.total_in_ccass_shares = 0
    summary.total_in_ccass_pct_of_issued = 0.0
    summary.non_ccass_shares = 10_000
    summary.non_ccass_pct_of_issued = 100.0
    summary.top5_pct_of_issued = 0.0
    summary.top10_pct_of_issued = 0.0
    summary.top5_pct_of_ccass = 0.0
    summary.top10_pct_of_ccass = 0.0
    service, repository, _ = _service(tmp_path, empty)

    with pytest.raises(PlatformError) as caught:
        service.get_concentration("01592", snapshot_date=date(2026, 7, 20))

    assert caught.value.code == ErrorCode.INVALID_SCHEMA
    assert caught.value.status_code == 502
    assert "no participant rows" in caught.value.message
    assert repository.count_snapshots("01592") == 1


@pytest.mark.parametrize("invalid_state", ["partial", "stale"])
def test_concentration_rejects_partial_and_stale_snapshot(
    tmp_path,
    current_response,
    invalid_state,
):
    response = current_response.model_copy(deep=True)
    if invalid_state == "partial":
        response.holdings = response.holdings[:-1]
    service, repository, _ = _service(
        tmp_path,
        response,
        partial=invalid_state == "partial",
        stale=invalid_state == "stale",
    )

    with pytest.raises(PlatformError) as caught:
        service.get_concentration("01592", snapshot_date=date(2026, 7, 20))

    expected = ErrorCode.DATA_STALE if invalid_state == "stale" else ErrorCode.INVALID_SCHEMA
    expected_status = 409 if invalid_state == "stale" else 422
    assert caught.value.code == expected
    assert caught.value.status_code == expected_status
    assert repository.count_snapshots("01592") == 1


def test_concentration_rejects_identity_conflict(tmp_path, current_response):
    _, repository, source = _service(tmp_path, current_response)
    snapshot = repository.snapshot_on(
        "01592",
        date(2026, 7, 20),
        source_id=source.source_id,
    )

    class IdentityConflictRepository:
        def snapshot_on(self, *_args, **_kwargs):
            return snapshot

    service = ConcentrationService(IdentityConflictRepository(), (source,))
    with pytest.raises(PlatformError) as caught:
        service.get_concentration("00001", snapshot_date=date(2026, 7, 20))

    assert caught.value.code == ErrorCode.INVALID_SCHEMA
    assert "identity or exact-date" in caught.value.message
    assert repository.count_snapshots("01592") == 1


def test_concentration_fails_loud_when_exact_snapshot_is_missing(
    tmp_path,
    current_response,
):
    service, repository, _ = _service(tmp_path, current_response)

    with pytest.raises(PlatformError) as caught:
        service.get_concentration("01592", snapshot_date=date(2026, 7, 19))

    assert caught.value.code == ErrorCode.NOT_FOUND
    assert caught.value.status_code == 404
    assert repository.count_snapshots("01592") == 1


def test_concentration_markdown_report_contains_summary_ranking_and_provenance(
    tmp_path,
    current_response,
):
    service, _, _ = _service(tmp_path, current_response)
    result = service.get_concentration("01592", snapshot_date=date(2026, 7, 20))

    report = build_concentration_markdown_report(result)

    assert report.startswith("# CCASS Concentration — 01592")
    assert "- Snapshot date: 2026-07-20" in report
    assert "- Total tracked shares: 3,300" in report
    assert "- Top 1: 15.0000% issued / 45.4545% CCASS" in report
    assert "## Participant Ranking" in report
    assert "| 1 | B00001 | TEST FIXTURE BROKER ONE | 1,500 |" in report
    assert "CONCENTRATION_VALIDATION: COMPLETE" in report


def test_concentration_api_and_report_are_additive_without_contract_regression(
    tmp_path,
    current_response,
):
    service, repository, _ = _service(tmp_path, current_response)
    app.dependency_overrides[get_concentration_service] = lambda: service
    client = TestClient(app)
    params = {"snapshot_date": "2026-07-20", "top_holders_limit": 2}
    try:
        response = client.get("/api/v1/stocks/1592/concentration", params=params)
        report = client.get("/api/v1/stocks/1592/concentration/report", params=params)
        openapi = client.get("/openapi.json").json()
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["participant_count"] == 3
    assert len(payload["participant_ranking"]) == 3
    assert len(payload["top_holders"]) == 2
    assert payload["diagnostics"]["validation_status"] == "COMPLETE"
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("text/markdown")
    assert report.text.startswith("# CCASS Concentration — 01592")
    expected_paths = {
        "/api/v1/stocks/{stock_code}/concentration",
        "/api/v1/stocks/{stock_code}/concentration/report",
        "/api/v1/stocks/{stock_code}/big-changes",
        "/api/v1/stocks/{stock_code}/changes",
        "/api/v1/stocks/{stock_code}/holdings",
        "/api/v1/ccass/{code}",
    }
    assert expected_paths <= set(openapi["paths"])
    assert repository.count_snapshots("01592") == 1


def test_concentration_api_returns_structured_error_for_partial_snapshot(
    tmp_path,
    current_response,
):
    partial = current_response.model_copy(deep=True)
    partial.holdings = partial.holdings[:-1]
    service, repository, _ = _service(tmp_path, partial, partial=True)
    app.dependency_overrides[get_concentration_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.get(
            "/api/v1/stocks/1592/concentration",
            params={"snapshot_date": "2026-07-20"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_SCHEMA"
    assert "partial" in response.json()["message"]
    assert repository.count_snapshots("01592") == 1
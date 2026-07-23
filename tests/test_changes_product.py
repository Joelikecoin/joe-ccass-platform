from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.services.changes import ChangesService, get_changes_service
from app.sources.registry import build_source_registry
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.changes_report import build_changes_markdown_report


def _service(tmp_path, current_response, previous_response):
    repository = NormalizedSnapshotRepository(tmp_path / "changes.db")
    source = build_source_registry(Settings()).select_holdings("webbsite")[0]
    repository.save_response(
        previous_response,
        source_id=source.source_id,
        parser_version=source.parser_version,
    )
    repository.save_response(
        current_response,
        source_id=source.source_id,
        parser_version=source.parser_version,
    )
    return ChangesService(repository, (source,)), repository, source


def test_changes_product_compares_two_exact_complete_snapshots(
    tmp_path,
    current_response,
    previous_response,
):
    service, repository, _ = _service(tmp_path, current_response, previous_response)

    result = service.get_changes(
        "1592",
        snapshot_date=date(2026, 7, 20),
        compare_date=date(2026, 7, 19),
    )

    assert result.metadata.code == "01592"
    assert result.metadata.compare_date == date(2026, 7, 19)
    assert result.metadata.snapshot_date == date(2026, 7, 20)
    assert result.metadata.percentage_basis == "issued_shares"
    assert result.metadata.compare_source.source_id == "webbsite"
    assert result.metadata.snapshot_source.safe_identifier == "https://fixture.invalid/"
    assert result.metadata.compare_source.issued_shares == 10_000
    assert result.metadata.compare_source.issued_shares_as_of == date(2026, 7, 19)
    assert result.metadata.snapshot_source.issued_shares_as_of == date(2026, 7, 20)
    assert result.metadata.snapshot_source.partial is False
    assert result.metadata.snapshot_source.stale is False
    assert result.summary.model_dump() == {
        "participant_count": 4,
        "changed_count": 4,
        "new_count": 1,
        "removed_count": 1,
        "increased_count": 1,
        "decreased_count": 1,
        "unchanged_count": 0,
    }
    by_id = {row.participant_id: row for row in result.changes}
    assert by_id["B00001"].model_dump() == {
        "participant_id": "B00001",
        "participant": "TEST FIXTURE BROKER ONE",
        "shares_before": 1_000,
        "shares_after": 1_500,
        "shares_change": 500,
        "percent_before": 10.0,
        "percent_after": 15.0,
        "percent_change": 5.0,
        "relative_change_percent": 50.0,
        "new_participant": False,
        "removed_participant": False,
        "status": "increased",
    }
    assert by_id["B00003"].removed_participant is True
    assert by_id["B00003"].relative_change_percent == -100.0
    assert by_id["B00004"].new_participant is True
    assert by_id["B00004"].relative_change_percent is None
    assert result.diagnostics.validation_status == "COMPLETE"
    assert result.diagnostics.stale_data_used is False
    assert "CHANGES_VALIDATION: COMPLETE" in result.data_quality_warnings
    assert repository.count_snapshots("01592") == 2


def test_changes_api_and_markdown_report_are_directly_usable_without_legacy_drift(
    tmp_path,
    current_response,
    previous_response,
):
    service, repository, _ = _service(tmp_path, current_response, previous_response)
    app.dependency_overrides[get_changes_service] = lambda: service
    client = TestClient(app)
    params = {"snapshot_date": "2026-07-20", "compare_date": "2026-07-19"}
    try:
        response = client.get("/api/v1/stocks/1592/changes", params=params)
        report = client.get("/api/v1/stocks/1592/changes/report", params=params)
        openapi = client.get("/openapi.json").json()
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["code"] == "01592"
    assert payload["changes"][0]["shares_change"] == 500
    assert payload["diagnostics"]["validation_status"] == "COMPLETE"
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("text/markdown")
    assert report.text.startswith("# CCASS Changes — 01592")
    assert "| B00004 | TEST FIXTURE BROKER FOUR | 0 | 300 | +300 |" in report.text
    assert "/api/v1/stocks/{stock_code}/changes" in openapi["paths"]
    assert "/api/v1/stocks/{stock_code}/holdings" in openapi["paths"]
    assert "/api/v1/ccass/{code}" in openapi["paths"]
    assert repository.count_snapshots("01592") == 2


def test_changes_report_preserves_source_dates_and_honest_relative_na(
    tmp_path,
    current_response,
    previous_response,
):
    service, _, _ = _service(tmp_path, current_response, previous_response)
    result = service.get_changes(
        "01592",
        snapshot_date=date(2026, 7, 20),
        compare_date=date(2026, 7, 19),
    )

    report = build_changes_markdown_report(result)

    assert "- Compare date: 2026-07-19" in report
    assert "- Snapshot date: 2026-07-20" in report
    assert "DATA NOT AVAILABLE | new |" in report
    assert "CHANGES_VALIDATION: COMPLETE" in report


@pytest.mark.parametrize(
    ("snapshot_date", "compare_date"),
    [
        (date(2026, 7, 20), date(2026, 7, 20)),
        (date(2026, 7, 19), date(2026, 7, 20)),
    ],
)
def test_changes_rejects_non_forward_comparison_dates(
    tmp_path,
    current_response,
    previous_response,
    snapshot_date,
    compare_date,
):
    service, _, _ = _service(tmp_path, current_response, previous_response)

    with pytest.raises(PlatformError) as caught:
        service.get_changes(
            "01592",
            snapshot_date=snapshot_date,
            compare_date=compare_date,
        )

    assert caught.value.code == ErrorCode.INVALID_SCHEMA
    assert caught.value.status_code == 400


def test_changes_fails_loud_when_exact_pair_is_missing(
    tmp_path,
    current_response,
    previous_response,
):
    service, _, _ = _service(tmp_path, current_response, previous_response)

    with pytest.raises(PlatformError) as caught:
        service.get_changes(
            "01592",
            snapshot_date=date(2026, 7, 20),
            compare_date=date(2026, 7, 18),
        )

    assert caught.value.code == ErrorCode.NOT_FOUND
    assert caught.value.status_code == 404
    assert "both requested exact CCASS snapshots" in caught.value.message


@pytest.mark.parametrize("invalid_state", ["partial", "stale", "denominator"])
def test_changes_never_uses_partial_stale_or_unvalidated_snapshot_as_product_data(
    tmp_path,
    current_response,
    previous_response,
    invalid_state,
):
    repository = NormalizedSnapshotRepository(tmp_path / f"{invalid_state}.db")
    source = build_source_registry(Settings()).select_holdings("webbsite")[0]
    repository.save_response(
        previous_response,
        source_id=source.source_id,
        parser_version=source.parser_version,
    )
    invalid = current_response.model_copy(deep=True)
    if invalid_state == "partial":
        invalid.holdings = invalid.holdings[:-1]
        repository.save_response(
            invalid,
            source_id=source.source_id,
            parser_version=source.parser_version,
            partial=True,
        )
    elif invalid_state == "stale":
        repository.save_response(
            invalid,
            source_id=source.source_id,
            parser_version=source.parser_version,
            stale=True,
        )
    else:
        invalid.holdings_summary.issued_shares_as_of = None
        repository.save_response(
            invalid,
            source_id=source.source_id,
            parser_version=source.parser_version,
        )
    service = ChangesService(repository, (source,))

    with pytest.raises(PlatformError) as caught:
        service.get_changes(
            "01592",
            snapshot_date=date(2026, 7, 20),
            compare_date=date(2026, 7, 19),
        )

    expected = ErrorCode.DATA_STALE if invalid_state == "stale" else ErrorCode.INVALID_SCHEMA
    assert caught.value.code == expected
    assert repository.count_snapshots("01592") == 2


def test_changes_api_returns_structured_error_for_partial_snapshot(
    tmp_path,
    current_response,
    previous_response,
):
    repository = NormalizedSnapshotRepository(tmp_path / "partial-api.db")
    source = build_source_registry(Settings()).select_holdings("webbsite")[0]
    repository.save_response(
        previous_response,
        source_id=source.source_id,
        parser_version=source.parser_version,
    )
    partial = current_response.model_copy(deep=True)
    partial.holdings = partial.holdings[:-1]
    repository.save_response(
        partial,
        source_id=source.source_id,
        parser_version=source.parser_version,
        partial=True,
    )
    service = ChangesService(repository, (source,))
    app.dependency_overrides[get_changes_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.get(
            "/api/v1/stocks/1592/changes",
            params={"snapshot_date": "2026-07-20", "compare_date": "2026-07-19"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_SCHEMA"
    assert "missing participants cannot be treated as zero" in response.json()["message"]
    assert repository.count_snapshots("01592") == 2


def test_changes_rejects_issue_identity_conflict(
    tmp_path,
    current_response,
    previous_response,
):
    conflict = previous_response.model_copy(deep=True)
    conflict.metadata.issue_id = 99_999
    service, _, _ = _service(tmp_path, current_response, conflict)

    with pytest.raises(PlatformError) as caught:
        service.get_changes(
            "01592",
            snapshot_date=date(2026, 7, 20),
            compare_date=date(2026, 7, 19),
        )

    assert caught.value.code == ErrorCode.INVALID_SCHEMA
    assert "issue IDs do not match" in caught.value.message


def test_changes_warns_when_verified_issued_share_denominator_changes(
    tmp_path,
    current_response,
    previous_response,
):
    previous = previous_response.model_copy(deep=True)
    previous.holdings_summary.issued_shares = 20_000
    previous.holdings_summary.total_in_ccass_pct_of_issued = 17.5
    previous.holdings_summary.non_ccass_shares = 16_500
    previous.holdings_summary.non_ccass_pct_of_issued = 82.5
    for row in previous.holdings:
        row.pct_of_issued = row.shares / 20_000 * 100
    previous.holdings[0].cumulative_pct_of_issued = 10.0
    previous.holdings[1].cumulative_pct_of_issued = 15.0
    previous.holdings[2].cumulative_pct_of_issued = 17.5
    previous.holdings_summary.top5_pct_of_issued = 17.5
    previous.holdings_summary.top10_pct_of_issued = 17.5
    service, _, _ = _service(tmp_path, current_response, previous)

    result = service.get_changes(
        "01592",
        snapshot_date=date(2026, 7, 20),
        compare_date=date(2026, 7, 19),
    )

    assert any(
        warning.startswith("DENOMINATOR_CHANGED:") for warning in result.data_quality_warnings
    )
    assert result.metadata.compare_date == date(2026, 7, 19)

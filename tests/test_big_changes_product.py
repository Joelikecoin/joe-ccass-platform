from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api import app
from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.services.big_changes import BigChangesService, get_big_changes_service
from app.services.changes import ChangesService
from app.sources.registry import build_source_registry
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.big_changes_report import build_big_changes_markdown_report


class SpyChangesService:
    def __init__(self, delegate):
        self.delegate = delegate
        self.calls = []

    def get_changes(self, code, *, snapshot_date, compare_date):
        self.calls.append((code, snapshot_date, compare_date))
        return self.delegate.get_changes(
            code,
            snapshot_date=snapshot_date,
            compare_date=compare_date,
        )


def _changes_service(tmp_path, current_response, previous_response, *, database="big.db"):
    repository = NormalizedSnapshotRepository(tmp_path / database)
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


def _dates():
    return {
        "snapshot_date": date(2026, 7, 20),
        "compare_date": date(2026, 7, 19),
    }


def test_big_changes_filters_p1_08_result_without_recomputing_comparison(
    tmp_path,
    current_response,
    previous_response,
):
    changes, repository, _ = _changes_service(
        tmp_path,
        current_response,
        previous_response,
    )
    spy = SpyChangesService(changes)
    service = BigChangesService(spy, default_threshold_shares=400)

    result = service.get_big_changes("1592", **_dates())

    assert spy.calls == [("1592", date(2026, 7, 20), date(2026, 7, 19))]
    assert result.metadata.code == "01592"
    assert result.metadata.compare_source.source_id == "webbsite"
    assert result.diagnostics.validation_status == "COMPLETE"
    assert result.summary.model_dump() == {
        "threshold_shares": 400,
        "participants_compared": 4,
        "changed_participants_considered": 4,
        "big_changes_count": 3,
        "new_count": 0,
        "removed_count": 1,
        "increased_count": 1,
        "decreased_count": 1,
    }
    assert [row.participant_id for row in result.big_changes] == [
        "B00001",
        "B00002",
        "B00003",
    ]
    assert "CHANGES_VALIDATION: COMPLETE" in result.data_quality_warnings
    assert "BIG_CHANGES_VALIDATION: COMPLETE" in result.data_quality_warnings
    assert repository.count_snapshots("01592") == 2


def test_big_changes_returns_empty_product_result_when_no_change_meets_threshold(
    tmp_path,
    current_response,
    previous_response,
):
    changes, _, _ = _changes_service(tmp_path, current_response, previous_response)
    service = BigChangesService(changes, default_threshold_shares=501)

    result = service.get_big_changes("01592", **_dates())

    assert result.big_changes == []
    assert result.summary.big_changes_count == 0
    assert result.summary.threshold_shares == 501
    assert result.diagnostics.validation_status == "COMPLETE"


def test_big_changes_threshold_boundary_is_inclusive(
    tmp_path,
    current_response,
    previous_response,
):
    changes, _, _ = _changes_service(tmp_path, current_response, previous_response)
    service = BigChangesService(changes, default_threshold_shares=999)

    result = service.get_big_changes(
        "01592",
        threshold_shares=500,
        **_dates(),
    )

    assert result.summary.threshold_shares == 500
    assert [abs(row.shares_change) for row in result.big_changes] == [500, 500, 500]
    assert all(abs(row.shares_change) >= 500 for row in result.big_changes)


def test_big_changes_default_threshold_is_configuration_driven():
    settings = Settings(big_changes_threshold_shares=321)

    assert settings.big_changes_threshold_shares == 321
    with pytest.raises(ValidationError):
        Settings(big_changes_threshold_shares=0)


@pytest.mark.parametrize("invalid_state", ["partial", "stale"])
def test_big_changes_preserves_changes_partial_and_stale_rejection(
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
    else:
        repository.save_response(
            invalid,
            source_id=source.source_id,
            parser_version=source.parser_version,
            stale=True,
        )
    service = BigChangesService(
        ChangesService(repository, (source,)),
        default_threshold_shares=500,
    )

    with pytest.raises(PlatformError) as caught:
        service.get_big_changes("01592", **_dates())

    expected = ErrorCode.DATA_STALE if invalid_state == "stale" else ErrorCode.INVALID_SCHEMA
    assert caught.value.code == expected
    assert repository.count_snapshots("01592") == 2


def test_big_changes_preserves_changes_identity_conflict(
    tmp_path,
    current_response,
    previous_response,
):
    conflict = previous_response.model_copy(deep=True)
    conflict.metadata.issue_id = 99_999
    changes, _, _ = _changes_service(tmp_path, current_response, conflict)
    service = BigChangesService(changes, default_threshold_shares=500)

    with pytest.raises(PlatformError) as caught:
        service.get_big_changes("01592", **_dates())

    assert caught.value.code == ErrorCode.INVALID_SCHEMA
    assert "issue IDs do not match" in caught.value.message


def test_big_changes_preserves_changes_missing_pair_failure(
    tmp_path,
    current_response,
    previous_response,
):
    changes, _, _ = _changes_service(tmp_path, current_response, previous_response)
    service = BigChangesService(changes, default_threshold_shares=500)

    with pytest.raises(PlatformError) as caught:
        service.get_big_changes(
            "01592",
            snapshot_date=date(2026, 7, 20),
            compare_date=date(2026, 7, 18),
        )

    assert caught.value.code == ErrorCode.NOT_FOUND
    assert caught.value.status_code == 404


def test_big_changes_markdown_report_contains_threshold_metadata_and_rows(
    tmp_path,
    current_response,
    previous_response,
):
    changes, _, _ = _changes_service(tmp_path, current_response, previous_response)
    service = BigChangesService(changes, default_threshold_shares=500)
    result = service.get_big_changes("01592", **_dates())

    report = build_big_changes_markdown_report(result)

    assert report.startswith("# CCASS Big Changes — 01592")
    assert "- Threshold: 500 shares (absolute, inclusive)" in report
    assert "- Compare date: 2026-07-19" in report
    assert "| B00003 | TEST FIXTURE BROKER THREE | 500 | 0 | -500 |" in report
    assert "BIG_CHANGES_VALIDATION: COMPLETE" in report


def test_big_changes_api_and_report_are_additive_without_contract_regression(
    tmp_path,
    current_response,
    previous_response,
):
    changes, repository, _ = _changes_service(tmp_path, current_response, previous_response)
    service = BigChangesService(changes, default_threshold_shares=999)
    app.dependency_overrides[get_big_changes_service] = lambda: service
    client = TestClient(app)
    params = {
        "snapshot_date": "2026-07-20",
        "compare_date": "2026-07-19",
        "threshold_shares": 500,
    }
    try:
        response = client.get("/api/v1/stocks/1592/big-changes", params=params)
        report = client.get("/api/v1/stocks/1592/big-changes/report", params=params)
        openapi = client.get("/openapi.json").json()
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["summary"]["threshold_shares"] == 500
    assert response.json()["summary"]["big_changes_count"] == 3
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("text/markdown")
    assert report.text.startswith("# CCASS Big Changes — 01592")
    expected_paths = {
        "/api/v1/stocks/{stock_code}/big-changes",
        "/api/v1/stocks/{stock_code}/big-changes/report",
        "/api/v1/stocks/{stock_code}/changes",
        "/api/v1/stocks/{stock_code}/holdings",
        "/api/v1/ccass/{code}",
    }
    assert expected_paths <= set(openapi["paths"])
    assert repository.count_snapshots("01592") == 2

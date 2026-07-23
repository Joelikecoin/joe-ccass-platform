from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.errors import ErrorCode, PlatformError
from app.services.ccass import CcassService, get_ccass_service
from app.services.latest_holdings import finalize_latest_holdings


class FixtureSource:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def get_holdings(self, code, limit=15):
        self.calls.append((code, limit))
        return self.response.model_copy(deep=True)


async def test_service_validates_full_snapshot_before_limit_and_exposes_product_fields(
    current_response,
):
    source = FixtureSource(current_response)
    service = CcassService(client=source)

    response = await service.get_stock_data("1592", holdings_limit=1)

    assert source.calls == [("01592", 10_000)]
    assert len(response.holdings) == 1
    assert response.holdings_summary.participant_count == 3
    assert response.holdings_summary.top5_pct_of_issued == 33.0
    assert response.holdings_summary.issued_shares_as_of == date(2026, 7, 20)
    assert response.holdings[0].participant_name == response.holdings[0].participant
    assert response.holdings[0].pct_of_ccass == 45.454545
    warnings = "\n".join(response.data_quality_warnings)
    assert "SNAPSHOT_COMPLETENESS: COMPLETE" in warnings
    assert "PRODUCT_VALIDATION: COMPLETE" in warnings
    assert "pct_of_issued uses issued_shares" in warnings


def test_product_validation_marks_unverified_denominator_partial_without_guessing(
    current_response,
):
    response = current_response.model_copy(deep=True)
    response.holdings_summary.issued_shares_as_of = None

    validated = finalize_latest_holdings(response, requested_code="01592")

    warnings = "\n".join(validated.data_quality_warnings)
    assert "ISSUED_SHARES_AS_OF_MISSING" in warnings
    assert "PRODUCT_VALIDATION: PARTIAL" in warnings
    assert validated.holdings_summary.issued_shares_as_of is None


def test_product_validation_flags_summary_and_source_date_mismatches(current_response):
    response = current_response.model_copy(deep=True)
    response.holdings_summary.total_in_ccass_shares += 1
    response.holdings_summary.issued_shares_as_of = date(2026, 7, 19)
    response.holdings[0].last_change = date(2026, 7, 21)

    validated = finalize_latest_holdings(response, requested_code="01592")

    warnings = "\n".join(validated.data_quality_warnings)
    assert "SUMMARY_MISMATCH" in warnings
    assert "PERCENTAGE_MISMATCH" in warnings
    assert "CORPORATE_ACTION_RISK" in warnings
    assert "SOURCE_DATE_MISMATCH" in warnings
    assert "PRODUCT_VALIDATION: PARTIAL" in warnings


def test_product_validation_never_marks_over_100_percent_complete(current_response):
    response = current_response.model_copy(deep=True)
    response.holdings[0].pct_of_issued = 101.0
    response.holdings[0].cumulative_pct_of_issued = 101.0

    validated = finalize_latest_holdings(response, requested_code="01592")

    warnings = "\n".join(validated.data_quality_warnings)
    assert "a source percentage exceeds 100%" in warnings
    assert "PRODUCT_VALIDATION: PARTIAL" in warnings


@pytest.mark.parametrize("failure", ["future_denominator", "duplicate_participant"])
def test_product_validation_rejects_identity_and_date_integrity_failures(
    current_response, failure
):
    response = current_response.model_copy(deep=True)
    if failure == "future_denominator":
        response.holdings_summary.issued_shares_as_of = date(2026, 7, 21)
    else:
        response.holdings[1].participant_id = response.holdings[0].participant_id

    with pytest.raises(PlatformError) as caught:
        finalize_latest_holdings(response, requested_code="01592")

    assert caught.value.code == ErrorCode.INVALID_SCHEMA
    assert caught.value.status_code == 502


def test_canonical_and_legacy_api_paths_share_latest_holdings_contract(current_response):
    source = FixtureSource(current_response)
    service = CcassService(client=source)
    app.dependency_overrides[get_ccass_service] = lambda: service
    client = TestClient(app)
    try:
        canonical = client.get(
            "/api/v1/stocks/1592/holdings",
            params={"holdings_limit": 1},
        )
        legacy = client.get(
            "/api/v1/ccass/1592",
            params={"holdings_limit": 1},
        )
        schema = client.get("/openapi.json").json()
    finally:
        app.dependency_overrides.clear()

    assert canonical.status_code == legacy.status_code == 200
    assert canonical.json() == legacy.json()
    payload = canonical.json()
    assert len(payload["holdings"]) == 1
    assert payload["holdings_summary"]["participant_count"] == 3
    assert payload["holdings_summary"]["issued_shares_as_of"] == "2026-07-20"
    assert payload["holdings"][0]["participant_name"] == "TEST FIXTURE BROKER ONE"
    assert payload["holdings"][0]["pct_of_ccass"] == 45.454545
    assert "/api/v1/stocks/{stock_code}/holdings" in schema["paths"]
    holding_properties = schema["components"]["schemas"]["HoldingRow"]["properties"]
    summary_properties = schema["components"]["schemas"]["HoldingsSummary"]["properties"]
    assert {"participant", "participant_name", "pct_of_ccass"} <= holding_properties.keys()
    assert "issued_shares_as_of" in summary_properties
    assert source.calls == [("01592", 10_000), ("01592", 10_000)]

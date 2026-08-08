from datetime import date, datetime, UTC

from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse, HoldingRow, HoldingsSummary, SourceMetadata
from app.services.ccass import CcassService
from ccass_core.source_trace import (
    CCASS_DATE_CONVENTION_REFERENCE,
    CCASS_SOURCE_DATE_TYPE,
    SourceDateGovernanceReference,
    SourceDateValidationResult,
    SourceTraceIdentity,
    SourceTraceSelection,
    SourceTraceView,
    validate_ccass_date_convention,
)


class FixtureSource:
    def __init__(self, response, *, error: PlatformError | None = None):
        self.response = response
        self.error = error
        self.calls = []

    async def get_holdings(self, code, limit=15):
        self.calls.append((code, limit))
        if self.error is not None:
            raise self.error
        return self.response.model_copy(deep=True)


def _response(*, holdings_date: date | None = date(2026, 7, 20)) -> CcassResponse:
    return CcassResponse(
        metadata=SourceMetadata(
            code="01592",
            name="TEST FIXTURE GOLDEN STOCK",
            issue_id=15_920,
            holdings_date=holdings_date,
            fetched_at=datetime(2026, 7, 21, 1, tzinfo=UTC),
            source_url="https://fixture.invalid/",
            source_name="Offline test fixture",
            cached=False,
            attribution="TEST FIXTURE not production data",
        ),
        holdings_summary=HoldingsSummary(
            total_in_ccass_shares=3_300,
            total_in_ccass_pct_of_issued=33.0,
            issued_shares=10_000,
            issued_shares_as_of=date(2026, 7, 20),
            non_ccass_shares=6_700,
            non_ccass_pct_of_issued=67.0,
            participant_count=1,
            top5_pct_of_issued=33.0,
            top10_pct_of_issued=33.0,
            top5_pct_of_ccass=100.0,
            top10_pct_of_ccass=100.0,
        ),
        holdings=[
            HoldingRow(
                rank=1,
                participant_id="B00001",
                participant="TEST FIXTURE BROKER ONE",
                shares=3_300,
                last_change=date(2026, 7, 20),
                pct_of_issued=33.0,
                pct_of_ccass=100.0,
                cumulative_pct_of_issued=33.0,
                participant_category="broker",
            )
        ],
        data_quality_warnings=[],
    )


def _trace(*, source_date_type: str = CCASS_SOURCE_DATE_TYPE, date_convention_reference: str = CCASS_DATE_CONVENTION_REFERENCE,
           data_as_of: date | None = date(2026, 7, 20)) -> SourceTraceView:
    return SourceTraceView(
        request_id="trace-001",
        request_surface="service",
        route="existing_service",
        cache_first=True,
        cache_usage_state="miss",
        source_identity=SourceTraceIdentity(
            source_id="offline_test_fixture",
            source_name="Offline test fixture",
            source_url="https://fixture.invalid/",
            source_status="active",
        ),
        selection=SourceTraceSelection(
            selected_source_id="existing_service",
            selected_source_name="FixtureSource",
            selected_source_status="active",
            attempted_sources=("existing_service",),
            attempted_statuses=("active",),
            source_candidates=("existing_service",),
        ),
        fetched_at=datetime(2026, 7, 21, 1, tzinfo=UTC),
        data_as_of=data_as_of,
        date_governance=SourceDateGovernanceReference(
            source_date_type=source_date_type,
            date_convention_reference=date_convention_reference,
        ),
        authoritative=False,
    )


def test_date_convention_validation_accepts_expected_governance(current_response):
    source_trace = _trace()

    result = validate_ccass_date_convention(source_trace, data_as_of=current_response.metadata.data_as_of)

    assert result.is_consistent is True
    assert result.warnings == ()
    assert result.notes == ()
    assert result.source_date_type == CCASS_SOURCE_DATE_TYPE
    assert result.date_convention_reference == CCASS_DATE_CONVENTION_REFERENCE


def test_date_convention_validation_warns_when_data_as_of_missing():
    source_trace = _trace(data_as_of=None)

    result = validate_ccass_date_convention(source_trace, data_as_of=None)

    assert result.is_consistent is False
    assert any("CCASS_DATA_AS_OF_MISSING" in warning for warning in result.warnings)


def test_date_convention_validation_warns_when_source_date_type_inconsistent(current_response):
    source_trace = _trace(source_date_type="unknown")

    result = validate_ccass_date_convention(source_trace, data_as_of=current_response.metadata.data_as_of)

    assert result.is_consistent is False
    assert any("CCASS_SOURCE_DATE_TYPE_INCONSISTENT" in warning for warning in result.warnings)


async def test_ccass_service_appends_date_convention_warnings(monkeypatch, current_response):
    source = FixtureSource(current_response)
    service = CcassService(client=source)

    fake_validation = SourceDateValidationResult(
        source_date_type=CCASS_SOURCE_DATE_TYPE,
        date_convention_reference=CCASS_DATE_CONVENTION_REFERENCE,
        warnings=("CCASS_DATE_CONVENTION:MOCK_WARNING:mock warning.",),
        notes=("mock_date_note",),
        is_consistent=False,
    )
    monkeypatch.setattr("app.services.ccass.validate_ccass_date_convention", lambda *args, **kwargs: fake_validation)

    result = await service.get_stock_gateway_response("1592", holdings_limit=2)

    assert any("MOCK_WARNING" in warning for warning in result.normalized_response.data_quality_warnings)
    assert "mock_date_note" in result.source_trace.notes

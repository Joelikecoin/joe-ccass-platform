from datetime import UTC, date, datetime

from app.models import AnnouncementsMetadata, AnnouncementsResponse, PriceHistoryMetadata, PriceHistoryResponse, PriceHistoryRow
from app.models import CcassResponse, HoldingRow, HoldingsSummary, SourceMetadata
from app.services.ai_read_model import AIReadModelService
from ccass_core.ai_read_model_governance import (
    build_ai_read_model_consumer_view,
    build_ai_read_model_governance_context,
    build_ai_read_model_governance_interpretation,
)
from ccass_core.source_trace import (
    SourceDateGovernanceReference,
    SourceTraceIdentity,
    SourceTraceSelection,
    SourceTraceView,
)


def _ccass_response(*, cached: bool = False) -> CcassResponse:
    return CcassResponse(
        metadata=SourceMetadata(
            code="01592",
            name="TEST FIXTURE GOLDEN STOCK",
            issue_id=15_920,
            holdings_date=date(2026, 7, 20),
            fetched_at=datetime(2026, 7, 21, 1, tzinfo=UTC),
            source_url="https://fixture.invalid/",
            source_name="Offline test fixture",
            cached=cached,
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


def _announcements_response() -> AnnouncementsResponse:
    return AnnouncementsResponse(
        metadata=AnnouncementsMetadata(
            code="01592",
            name="TEST FIXTURE GOLDEN STOCK",
            source_name="HKEXnews",
            source_url="https://www1.hkexnews.hk/search/titlesearch.xhtml?category=0&lang=EN&market=SEHK&stockId=189695",
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            earliest_announcement_date=date(2026, 7, 19),
            latest_announcement_date=date(2026, 7, 20),
            announcement_count=1,
        ),
        announcements=[],
    )


def _price_history_response() -> PriceHistoryResponse:
    return PriceHistoryResponse(
        metadata=PriceHistoryMetadata(
            code="01592",
            name="TEST FIXTURE GOLDEN STOCK",
            ticker="01592.HK",
            price_date_from=date(2026, 7, 19),
            price_date_to=date(2026, 7, 20),
            source_name="Yahoo Finance",
            source_url="https://query1.finance.yahoo.com/v8/finance/chart/01592.HK",
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            adjustment_state="adjusted",
            currency="HKD",
            adjustment_note="Adjusted close values are available from Yahoo Finance.",
        ),
        prices=[
            PriceHistoryRow(
                price_date=date(2026, 7, 19),
                open=1.0,
                high=1.1,
                low=0.9,
                close=1.05,
                adjusted_close=1.01,
                volume=1000,
                turnover=1050.0,
            )
        ],
    )


class FixtureCcassService:
    def __init__(self, response: CcassResponse):
        self.response = response
        self.calls = []

    async def get_stock_data(self, code, holdings_limit: int = 15):
        self.calls.append((code, holdings_limit))
        return self.response


class FixtureAnnouncementsService:
    def __init__(self, response: AnnouncementsResponse):
        self.response = response

    async def get_announcements(self, code, start_date=None, end_date=None):
        return self.response


class FixturePriceHistoryService:
    def __init__(self, response: PriceHistoryResponse):
        self.response = response

    async def get_price_history(self, code, start_date=None, end_date=None):
        return self.response


class FixtureSnapshotRepository:
    def __init__(self, response: CcassResponse):
        self.response = response

    def snapshot_id_on(self, code: str, snapshot_date: date, *, source_id: str):
        return 101

    def previous(self, code: str, *, before_date: date, source_id: str):
        return None


def _service(response: CcassResponse | None = None) -> AIReadModelService:
    ccass_response = response or _ccass_response()
    return AIReadModelService(
        ccass_service=FixtureCcassService(ccass_response),
        announcements_service=FixtureAnnouncementsService(_announcements_response()),
        price_history_service=FixturePriceHistoryService(_price_history_response()),
        snapshot_repository=FixtureSnapshotRepository(ccass_response),
    )


def _source_trace(response: CcassResponse) -> SourceTraceView:
    return SourceTraceView(
        request_id="trace-001",
        request_surface="service",
        route="existing_service",
        cache_first=True,
        cache_usage_state="miss",
        source_identity=SourceTraceIdentity(
            source_id="offline_test_fixture",
            source_name=response.metadata.source_name,
            source_url=response.metadata.source_url,
            source_status="active",
        ),
        selection=SourceTraceSelection(
            selected_source_id="existing_service",
            selected_source_name="FixtureCcassService",
            selected_source_status="active",
            attempted_sources=("existing_service",),
            attempted_statuses=("active",),
            source_candidates=("existing_service",),
        ),
        fetched_at=response.metadata.fetched_at,
        data_as_of=response.metadata.data_as_of,
        date_governance=SourceDateGovernanceReference(),
        authoritative=False,
    )


def test_ai_read_model_governance_context_preserves_metadata(current_response):
    model = __import__("asyncio").run(_service(current_response).get_read_model("1592"))
    source_trace = _source_trace(current_response)

    context = build_ai_read_model_governance_context(model, source_trace=source_trace)

    assert context.source == current_response.metadata.source_name
    assert context.source_type == "ccass_holdings"
    assert context.primary_or_fallback == "primary"
    assert context.freshness_status == "partial"
    assert context.availability_state == "partial"
    assert context.warning_summary == f"{len(model.quality.warnings)} warning(s)"
    assert source_trace.request_id in context.source_trace_reference
    assert "Governance context:" in context.summary


def test_ai_read_model_consumer_view_exposes_governance_interpretation(current_response):
    model = __import__("asyncio").run(_service(current_response).get_read_model("1592"))
    source_trace = _source_trace(current_response)

    consumer_view = build_ai_read_model_consumer_view(model, source_trace=source_trace)

    assert consumer_view.available is True
    assert consumer_view.governance_context is not None
    assert consumer_view.governance_interpretation is not None
    assert consumer_view.governance_interpretation.data_availability_state == "partial"
    assert consumer_view.governance_interpretation.freshness_state == "partial"
    assert consumer_view.governance_interpretation.provenance_summary == (
        f"{current_response.metadata.source_name} / ccass_holdings / primary"
    )
    assert consumer_view.governance_interpretation.warning_summary == consumer_view.governance_context.warning_summary
    assert consumer_view.consumer_guidance is not None
    assert consumer_view.consumer_guidance.availability_state == "partial"
    assert consumer_view.consumer_guidance.freshness_state == "partial"
    assert "payload" in " ".join(consumer_view.consumer_guidance.usage_steps)
    assert "context" in " ".join(consumer_view.consumer_guidance.usage_steps)
    assert consumer_view.summary == consumer_view.governance_interpretation.summary
    assert "Consumer guidance:" in consumer_view.consumer_guidance.summary


def test_ai_read_model_consumer_view_handles_missing_model():
    consumer_view = build_ai_read_model_consumer_view(None)

    assert consumer_view.available is False
    assert consumer_view.governance_context is None
    assert consumer_view.governance_interpretation is None
    assert consumer_view.consumer_guidance is None
    assert consumer_view.warnings == []


def test_ai_read_model_service_exposes_consumer_readable_governance_context(current_response):
    service = _service(current_response)
    source_trace = _source_trace(current_response)

    governance_context = __import__("asyncio").run(
        service.get_read_model_governance_context("1592", source_trace=source_trace)
    )
    consumer_view = __import__("asyncio").run(
        service.get_read_model_consumer_view("1592", source_trace=source_trace)
    )

    assert governance_context.source == current_response.metadata.source_name
    assert governance_context.availability_state == "partial"
    assert consumer_view.governance_context == governance_context
    assert consumer_view.governance_interpretation is not None
    assert consumer_view.governance_interpretation.source_trace_reference == governance_context.source_trace_reference
    assert consumer_view.consumer_guidance is not None
    assert consumer_view.consumer_guidance.source_trace_reference == governance_context.source_trace_reference


def test_ai_read_model_service_exposes_consumer_guidance(current_response):
    service = _service(current_response)
    source_trace = _source_trace(current_response)

    guidance = __import__("asyncio").run(
        service.get_read_model_consumer_guidance("1592", source_trace=source_trace)
    )

    assert guidance.availability_state == "partial"
    assert guidance.freshness_state == "partial"
    assert guidance.provenance_summary == (
        f"{current_response.metadata.source_name} / ccass_holdings / primary"
    )
    assert guidance.source_trace_reference == source_trace.request_id + " / " + source_trace.route + " / existing_service"
    assert guidance.usage_steps
    assert "trading signal" not in " ".join(guidance.usage_steps).lower()
    assert "recommendation" not in " ".join(guidance.usage_steps).lower()

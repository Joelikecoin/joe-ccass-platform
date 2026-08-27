from app.errors import ErrorCode, PlatformError
from app.services.ccass import CcassService
from app.services.data_gateway import (
    CcassDataGateway,
    CacheFirstSourceRouter,
    GatewayRequest,
    GatewaySourceCandidate,
)
from app.streamlit_ui import DEFAULT_LOCALE, PreparedReport, render_prepared_report
from ccass_core.source_trace import (
    CCASS_DATE_CONVENTION_REFERENCE,
    CCASS_SOURCE_DATE_TYPE,
    SourceDateGovernanceReference,
    SourceTraceIdentity,
    SourceTraceSelection,
    SourceTraceView,
    build_source_trace_markdown,
    build_source_trace_view,
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


class FixtureCache:
    def __init__(self, response=None):
        self.response = response
        self.calls = []

    async def get(self, request):
        self.calls.append(request)
        if self.response is None:
            return None
        return self.response.model_copy(deep=True)


def _request(stock_code="1592", *, selection_rule="priority_then_availability"):
    return GatewayRequest(
        stock_code=stock_code,
        holdings_limit=3,
        request_surface="api",
        selection_rule=selection_rule,
    )


async def test_source_trace_creation_preserves_source_identity_and_date_governance(current_response):
    source = FixtureSource(current_response)
    gateway = CcassDataGateway(source_backend=source)

    result = await gateway.get_holdings(_request())
    view = build_source_trace_view(result)

    assert view.source_identity.source_id == "offline_test_fixture"
    assert view.source_identity.source_name == current_response.metadata.source_name
    assert view.source_identity.source_url == current_response.metadata.source_url
    assert view.source_identity.source_status == "active"
    assert view.selection.selected_source_id == "existing_service"
    assert view.selection.attempted_sources == ("existing_service",)
    assert view.cache_usage_state == "miss"
    assert view.fetched_at == current_response.metadata.fetched_at
    assert view.data_as_of == current_response.metadata.data_as_of
    assert view.date_governance.source_date_type == CCASS_SOURCE_DATE_TYPE
    assert view.date_governance.date_convention_reference == CCASS_DATE_CONVENTION_REFERENCE


async def test_source_trace_fallback_records_attempted_sources_and_reason(current_response):
    failing = FixtureSource(
        current_response.model_copy(deep=True),
        error=PlatformError(
            ErrorCode.SOURCE_UNAVAILABLE,
            "Primary source unavailable.",
            retry_recommended=True,
            status_code=503,
        ),
    )
    fallback = FixtureSource(current_response.model_copy(deep=True))
    router = CacheFirstSourceRouter(
        source_candidates=(
            GatewaySourceCandidate(
                source_id="primary",
                source_name="Primary Source",
                priority=0,
                status="active",
                backend=failing,
            ),
            GatewaySourceCandidate(
                source_id="fallback",
                source_name="Fallback Source",
                priority=1,
                status="fallback",
                backend=fallback,
            ),
        )
    )

    result = await router.route(_request())
    view = build_source_trace_view(result)

    assert view.selection.selected_source_id == "fallback"
    assert view.selection.attempted_sources == ("primary", "fallback")
    assert view.selection.fallback_reason and "primary failed" in view.selection.fallback_reason.lower()
    assert view.source_identity.source_status == "fallback"
    assert failing.calls == [("01592", 10000)]
    assert fallback.calls == [("01592", 10000)]


async def test_source_trace_cache_hit_marks_cache_usage_and_preserves_identity(current_response):
    source = FixtureSource(current_response)
    cache = FixtureCache(current_response)
    gateway = CcassDataGateway(source_backend=source, cache_backend=cache)

    result = await gateway.get_holdings(_request())
    view = build_source_trace_view(result)

    assert view.cache_usage_state == "cached"
    assert view.selection.selected_source_id == "cache"
    assert view.selection.selected_source_status == "cached"
    assert view.source_identity.source_id == "offline_test_fixture"
    assert view.source_identity.source_status == "cached"
    assert source.calls == []
    assert len(cache.calls) == 1


async def test_source_trace_consumer_formatting_renders_governance_rows(current_response):
    source = FixtureSource(current_response)
    gateway = CcassDataGateway(source_backend=source)

    result = await gateway.get_holdings(_request())
    view = build_source_trace_view(result)
    markdown = build_source_trace_markdown(view)

    assert "### Source Trace" in markdown
    assert "Source identity" in markdown
    assert "Selected source" in markdown
    assert "Attempted sources" in markdown
    assert "Cache usage state" in markdown
    assert "Source date type" in markdown
    assert "Date convention reference" in markdown
    assert CCASS_DATE_CONVENTION_REFERENCE in markdown


async def test_ccass_service_regression_exposes_trace_without_changing_response_contract(current_response):
    source = FixtureSource(current_response)
    service = CcassService(client=source)

    gateway_response = await service.get_stock_gateway_response("1592", holdings_limit=2)
    response = await service.get_stock_data("1592", holdings_limit=2)
    trace = await service.get_stock_source_trace("1592", holdings_limit=2)

    assert gateway_response.normalized_response.metadata.code == "01592"
    assert response.metadata.code == "01592"
    assert len(response.holdings) == 2
    assert trace.selection.selected_source_id == "existing_service"
    assert trace.source_identity.source_name == current_response.metadata.source_name
    assert source.calls == [("01592", 10_000), ("01592", 10_000), ("01592", 10_000)]


def test_render_prepared_report_omits_source_trace_from_markdown_and_payload(current_response):
    source_trace = SourceTraceView(
        request_id="trace-001",
        request_surface="service",
        route="existing_service",
        cache_first=True,
        cache_usage_state="miss",
        source_identity=SourceTraceIdentity(
            source_id="offline_test_fixture",
            source_name=current_response.metadata.source_name,
            source_url=current_response.metadata.source_url,
            source_status="active",
        ),
        selection=SourceTraceSelection(
            selected_source_id="existing_service",
            selected_source_name="SuccessfulService",
            selected_source_status="active",
            attempted_sources=("existing_service",),
            attempted_statuses=("active",),
            source_candidates=("existing_service",),
        ),
        fetched_at=current_response.metadata.fetched_at,
        data_as_of=current_response.metadata.data_as_of,
        date_governance=SourceDateGovernanceReference(),
        authoritative=False,
        notes=("trace_ready",),
    )
    prepared = PreparedReport(
        code=current_response.metadata.code,
        markdown="base report",
        chatgpt_payload="base payload",
        filename="01592_ccass_report.md",
        response=current_response,
        source_trace=source_trace,
    )

    markdown, payload = render_prepared_report(prepared, locale=DEFAULT_LOCALE)

    assert "### Source Trace" not in markdown
    assert "### Source Trace" not in payload
    assert "trace_ready" not in markdown

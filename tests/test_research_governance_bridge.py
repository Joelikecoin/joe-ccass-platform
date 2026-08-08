from app.services.ccass import CcassService
from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.compute import compute_analysis
from ccass_core.research_context import build_research_context_package
from ccass_core.research_context_consumer import build_research_context_consumer_view
from ccass_core.research_governance_bridge import build_research_governance_context
from ccass_core.research_workflow import (
    build_research_workflow_session_from_result,
    load_research_context_into_workflow,
)
from ccass_core.research_workflow_consumer import build_research_workflow_consumer_view
from ccass_core.research_workflow_presentation import build_research_workflow_summary_markdown
from ccass_core.source_trace import build_source_trace_view
from ccass_core.report import DEFAULT_LOCALE


class FixtureSource:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def get_holdings(self, code, limit=15):
        self.calls.append((code, limit))
        return self.response.model_copy(deep=True)


def _build_context(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    ai_read_model = build_ai_read_model_v0_1(
        code=current_response.metadata.code,
        response=current_response,
        surface="ccass_ai_read_model",
        analysis=analysis,
        previous_response=previous_response,
        snapshot_id=101,
        previous_snapshot_id=100,
    )
    return build_research_context_package(ai_read_model=ai_read_model)


async def test_research_governance_bridge_combines_package_and_source_trace(current_response, previous_response):
    package = _build_context(current_response, previous_response)
    service = CcassService(client=FixtureSource(current_response))
    gateway_response = await service.get_stock_gateway_response("1592", holdings_limit=2)
    source_trace = build_source_trace_view(gateway_response)

    governance_context = build_research_governance_context(package, source_trace)

    assert governance_context.source_trace == source_trace
    assert governance_context.provenance_summary == (
        f"{package.quality_context.provenance.source} / "
        f"{package.quality_context.provenance.source_type} / "
        f"{package.quality_context.provenance.primary_or_fallback}"
    )
    assert package.quality_context.freshness_status in governance_context.freshness_summary
    assert source_trace.cache_usage_state in governance_context.freshness_summary
    assert governance_context.date_convention_status == "holdings_date / ccass_holdings_date_v1"
    assert source_trace.request_id in governance_context.source_trace_reference
    assert governance_context.warnings_summary == f"{len(package.quality_context.warnings)} warning(s)"
    assert "Governance context:" in governance_context.summary


async def test_research_context_consumer_view_includes_governance_context(current_response, previous_response):
    package = _build_context(current_response, previous_response)
    service = CcassService(client=FixtureSource(current_response))
    gateway_response = await service.get_stock_gateway_response("1592", holdings_limit=2)
    source_trace = build_source_trace_view(gateway_response)

    consumer_view = build_research_context_consumer_view(package, source_trace=source_trace)

    assert consumer_view.governance_context is not None
    assert consumer_view.governance_context.source_trace == source_trace
    assert consumer_view.governance_context.date_convention_status == "holdings_date / ccass_holdings_date_v1"
    assert consumer_view.governance_context.summary.startswith("Governance context:")


async def test_research_workflow_consumer_and_presentation_surface_governance_context(current_response, previous_response):
    package = _build_context(current_response, previous_response)
    service = CcassService(client=FixtureSource(current_response))
    gateway_response = await service.get_stock_gateway_response("1592", holdings_limit=2)
    source_trace = build_source_trace_view(gateway_response)

    workflow = build_research_workflow_session_from_result(
        code=current_response.metadata.code,
        response=current_response,
        previous_response=previous_response,
        snapshot_id=101,
        previous_snapshot_id=100,
        session_id="workflow-bridge-001",
    )
    loaded = load_research_context_into_workflow(workflow, package)
    consumer_view = build_research_workflow_consumer_view(loaded, source_trace=source_trace)
    markdown = build_research_workflow_summary_markdown(loaded, source_trace=source_trace, locale=DEFAULT_LOCALE)

    assert consumer_view.governance_context is not None
    assert consumer_view.governance_context.source_trace_reference in markdown
    assert "Governance summary" in markdown
    assert "Date convention status" in markdown

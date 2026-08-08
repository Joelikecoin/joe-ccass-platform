from app.services.ccass import CcassService
from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.compute import compute_analysis
from ccass_core.research_context import build_research_context_package
from ccass_core.research_context_consumer import build_research_context_consumer_view
from ccass_core.research_governance_bridge import build_research_governance_context
from ccass_core.research_governance_interpretation import build_research_governance_interpretation
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


async def test_research_governance_interpretation_reflects_existing_metadata(current_response, previous_response):
    package = _build_context(current_response, previous_response)
    service = CcassService(client=FixtureSource(current_response))
    gateway_response = await service.get_stock_gateway_response("1592", holdings_limit=2)
    source_trace = build_source_trace_view(gateway_response)
    governance_context = build_research_governance_context(package, source_trace)
    consumer_view = build_research_context_consumer_view(package, source_trace=source_trace)

    interpretation = build_research_governance_interpretation(consumer_view, governance_context)

    assert interpretation.data_availability_state == "available"
    assert interpretation.freshness_state == package.quality_context.freshness_status
    assert interpretation.provenance_summary == governance_context.provenance_summary
    assert interpretation.warning_summary == governance_context.warnings_summary
    assert interpretation.source_trace_reference == governance_context.source_trace_reference
    assert "Governance interpretation:" in interpretation.summary
    assert "availability=available" in interpretation.summary
    assert "freshness=" in interpretation.summary
    assert "limitations=" in interpretation.summary


async def test_research_context_consumer_view_exposes_governance_interpretation(current_response, previous_response):
    package = _build_context(current_response, previous_response)
    service = CcassService(client=FixtureSource(current_response))
    gateway_response = await service.get_stock_gateway_response("1592", holdings_limit=2)
    source_trace = build_source_trace_view(gateway_response)

    consumer_view = build_research_context_consumer_view(package, source_trace=source_trace)

    assert consumer_view.governance_interpretation is not None
    assert consumer_view.governance_interpretation.data_availability_state == "available"
    assert consumer_view.governance_interpretation.provenance_summary == consumer_view.governance_context.provenance_summary
    assert consumer_view.governance_interpretation.warning_summary == consumer_view.governance_context.warnings_summary


async def test_research_workflow_consumer_and_presentation_include_governance_interpretation(current_response, previous_response):
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
        session_id="workflow-interpretation-001",
    )
    loaded = load_research_context_into_workflow(workflow, package)
    consumer_view = build_research_workflow_consumer_view(loaded, source_trace=source_trace)
    markdown = build_research_workflow_summary_markdown(
        loaded,
        source_trace=source_trace,
        locale=DEFAULT_LOCALE,
    )

    assert consumer_view.governance_interpretation is not None
    assert consumer_view.governance_interpretation.source_trace_reference in markdown
    assert "Data availability state" in markdown
    assert "Freshness state" in markdown
    assert "Governance limitation summary" in markdown

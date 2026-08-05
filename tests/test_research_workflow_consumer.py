from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.compute import compute_analysis
from ccass_core.research_context import build_research_context_package
from ccass_core.research_workflow import (
    ResearchWorkflowState,
    create_research_workflow_session,
    load_research_context_into_workflow,
    mark_research_workflow_ready,
)
from ccass_core.research_workflow_consumer import build_research_workflow_consumer_view


def _build_research_context_package(current_response, previous_response):
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


def test_research_workflow_consumer_creation_access():
    workflow = create_research_workflow_session(stock_code="01592", session_id="session-001")

    consumer_view = build_research_workflow_consumer_view(workflow)

    assert consumer_view.available is True
    assert consumer_view.workflow_state == ResearchWorkflowState.CREATED
    assert consumer_view.session_metadata.session_id == "session-001"
    assert consumer_view.session_metadata.stock_code == "01592"
    assert consumer_view.context_available is False
    assert consumer_view.research_context_package is None
    assert consumer_view.summary == "Research workflow created for 01592. Research context is not yet available."


def test_research_workflow_consumer_loaded_workflow(current_response, previous_response):
    package = _build_research_context_package(current_response, previous_response)
    workflow = create_research_workflow_session(stock_code=current_response.metadata.code, session_id="session-002")
    loaded = load_research_context_into_workflow(workflow, package)

    consumer_view = build_research_workflow_consumer_view(loaded)

    assert consumer_view.workflow_state == ResearchWorkflowState.LOADED
    assert consumer_view.context_available is True
    assert consumer_view.research_context_package == package
    assert consumer_view.research_context_consumer_view is not None
    assert consumer_view.quality_context == package.quality_context
    assert consumer_view.warnings == package.quality_context.warnings
    assert consumer_view.summary == "Research workflow loaded for 01592. Research context is available with fresh quality."


def test_research_workflow_consumer_missing_context():
    workflow = create_research_workflow_session(stock_code="01592", session_id="session-003")

    consumer_view = build_research_workflow_consumer_view(workflow)

    assert consumer_view.available is True
    assert consumer_view.workflow_state == ResearchWorkflowState.CREATED
    assert consumer_view.context_available is False
    assert consumer_view.research_context_package is None
    assert consumer_view.research_context_consumer_view is None
    assert consumer_view.quality_context is None
    assert consumer_view.warnings == []


def test_research_workflow_consumer_quality_freshness_provenance_preserved(current_response, previous_response):
    package = _build_research_context_package(current_response, previous_response)
    workflow = create_research_workflow_session(stock_code=current_response.metadata.code, session_id="session-004")
    loaded = load_research_context_into_workflow(workflow, package)
    ready = mark_research_workflow_ready(loaded)

    consumer_view = build_research_workflow_consumer_view(ready)

    assert consumer_view.workflow_state == ResearchWorkflowState.READY
    assert consumer_view.quality_context.provenance == package.quality_context.provenance
    assert consumer_view.quality_context.freshness_status == package.quality_context.freshness_status
    assert consumer_view.quality_context.error_state == package.quality_context.error_state
    assert consumer_view.warnings == package.quality_context.warnings
    assert consumer_view.contract_meta == ready.contract_meta


def test_research_workflow_consumer_regression_compatibility(current_response, previous_response):
    package = _build_research_context_package(current_response, previous_response)
    workflow = create_research_workflow_session(stock_code=current_response.metadata.code, session_id="session-005")
    loaded = load_research_context_into_workflow(workflow, package)
    ready = mark_research_workflow_ready(loaded)

    consumer_view = build_research_workflow_consumer_view(ready)

    assert consumer_view.available is True
    assert consumer_view.workflow_state == ResearchWorkflowState.READY
    assert consumer_view.session_metadata.research_context_package_version == package.contract_meta.version
    assert consumer_view.session_metadata.research_context_package_surface == package.contract_meta.surface
    assert consumer_view.research_context_consumer_view.identity == package.identity
    assert consumer_view.research_context_consumer_view.ownership_context == package.ownership_context

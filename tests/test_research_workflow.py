from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.compute import compute_analysis
from ccass_core.research_context import build_research_context_package
from ccass_core.research_workflow import (
    ResearchWorkflowState,
    create_research_workflow_session,
    load_research_context_into_workflow,
    mark_research_workflow_ready,
)


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


def test_research_workflow_creation():
    workflow = create_research_workflow_session(stock_code="01592", session_id="session-001")

    assert workflow.state == ResearchWorkflowState.CREATED
    assert workflow.metadata.session_id == "session-001"
    assert workflow.metadata.stock_code == "01592"
    assert workflow.metadata.loaded_at is None
    assert workflow.metadata.ready_at is None
    assert workflow.research_context_package is None
    assert workflow.consumer_view is None


def test_research_workflow_context_loading(current_response, previous_response):
    package = _build_research_context_package(current_response, previous_response)
    workflow = create_research_workflow_session(stock_code=current_response.metadata.code, session_id="session-002")

    loaded = load_research_context_into_workflow(workflow, package)

    assert loaded.state == ResearchWorkflowState.LOADED
    assert loaded.research_context_package == package
    assert loaded.consumer_view is not None
    assert loaded.consumer_view.available is True
    assert loaded.metadata.loaded_at is not None
    assert loaded.metadata.research_context_package_version == package.contract_meta.version
    assert loaded.metadata.research_context_package_surface == package.contract_meta.surface


def test_research_workflow_handles_missing_context():
    workflow = create_research_workflow_session(stock_code="01592", session_id="session-003")

    loaded = load_research_context_into_workflow(workflow, None)

    assert loaded.state == ResearchWorkflowState.CREATED
    assert loaded.research_context_package is None
    assert loaded.consumer_view is None
    assert loaded.metadata.loaded_at is None
    assert loaded.metadata.ready_at is None
    assert loaded.metadata.research_context_package_version is None
    assert loaded.metadata.research_context_package_surface is None


def test_research_workflow_ready_preserves_context_and_quality(current_response, previous_response):
    package = _build_research_context_package(current_response, previous_response)
    workflow = create_research_workflow_session(stock_code=current_response.metadata.code, session_id="session-004")
    loaded = load_research_context_into_workflow(workflow, package)

    ready = mark_research_workflow_ready(loaded)

    assert ready.state == ResearchWorkflowState.READY
    assert ready.research_context_package == package
    assert ready.consumer_view is not None
    assert ready.consumer_view.quality_context == package.quality_context
    assert ready.consumer_view.warnings == package.quality_context.warnings
    assert ready.consumer_view.quality_context.provenance == package.quality_context.provenance
    assert ready.consumer_view.quality_context.freshness_status == package.quality_context.freshness_status
    assert ready.metadata.loaded_at == loaded.metadata.loaded_at
    assert ready.metadata.ready_at is not None


def test_research_workflow_handles_empty_data():
    ai_read_model = build_ai_read_model_v0_1(
        code="01592",
        response=None,
        surface="ccass_ai_read_model",
    )
    package = build_research_context_package(ai_read_model=ai_read_model)
    workflow = create_research_workflow_session(stock_code="01592", session_id="session-005")

    loaded = load_research_context_into_workflow(workflow, package)
    ready = mark_research_workflow_ready(loaded)

    assert loaded.state == ResearchWorkflowState.LOADED
    assert loaded.consumer_view is not None
    assert loaded.consumer_view.available is True
    assert loaded.consumer_view.quality_context.freshness_status == "unavailable"
    assert ready.state == ResearchWorkflowState.READY
    assert ready.research_context_package == package
    assert ready.consumer_view is not None
    assert package.quality_context.freshness_status == "unavailable"

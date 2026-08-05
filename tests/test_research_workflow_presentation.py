from ccass_core.compute import compute_analysis
from ccass_core.research_workflow import build_research_workflow_session_from_result
from ccass_core.research_workflow_presentation import build_research_workflow_summary_markdown
from ccass_core.report import DEFAULT_LOCALE, translate_text


def _build_workflow(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    return build_research_workflow_session_from_result(
        code=current_response.metadata.code,
        response=current_response,
        analysis=analysis,
        previous_response=previous_response,
        session_id="workflow-001",
    )


def test_research_workflow_summary_renders_ready_workflow(current_response, previous_response):
    workflow = _build_workflow(current_response, previous_response)
    markdown = build_research_workflow_summary_markdown(workflow, locale=DEFAULT_LOCALE)

    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_caption") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_state") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_state_ready") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_session_id") in markdown
    assert "workflow-001" in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_stock_code") in markdown
    assert current_response.metadata.code in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_context_availability") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_context_available") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_package_reference") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_quality_reference") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_freshness_reference") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_provenance_reference") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_warnings_summary") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_warnings_none") not in markdown
    assert "warning(s)" in markdown


def test_research_workflow_summary_handles_missing_workflow():
    markdown = build_research_workflow_summary_markdown(None, locale=DEFAULT_LOCALE)

    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_workflow_unavailable") in markdown


def test_research_workflow_summary_preserves_quality_freshness_provenance(current_response, previous_response):
    workflow = _build_workflow(current_response, previous_response)
    markdown = build_research_workflow_summary_markdown(workflow, locale=DEFAULT_LOCALE)

    assert workflow.consumer_view.quality_context.freshness_status in markdown
    assert workflow.consumer_view.quality_context.provenance.source in markdown
    assert workflow.consumer_view.quality_context.provenance.source_type in markdown
    assert workflow.consumer_view.quality_context.provenance.primary_or_fallback in markdown
    assert workflow.consumer_view.warnings[0] in markdown

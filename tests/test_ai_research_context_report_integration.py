from __future__ import annotations

from ccass_core.compute import compute_analysis
from ccass_core.ai_research_context_entry import AIResearchContextConsumerEntry
from ccass_core.research_workflow import build_research_workflow_session_from_result
from app.streamlit_ui import DEFAULT_LOCALE, PreparedReport, render_prepared_report


def test_render_prepared_report_includes_ai_research_context_consumer_entry(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response)
    workflow = build_research_workflow_session_from_result(
        code=current_response.metadata.code,
        response=current_response,
        analysis=analysis,
        previous_response=previous_response,
        session_id="research-entry-001",
    )
    prepared = PreparedReport(
        code=current_response.metadata.code,
        markdown="base report",
        chatgpt_payload="base payload",
        filename="01592_ccass_report.md",
        response=current_response,
        previous_response=previous_response,
        analysis=analysis,
        workflow=workflow,
        research_context_entry=AIResearchContextConsumerEntry(),
    )

    markdown, payload = render_prepared_report(prepared, locale=DEFAULT_LOCALE)

    assert "AI Research Context Consumer Entry" in markdown
    assert "AI Research Context Handoff" in markdown
    assert "Coverage state" in markdown
    assert "Required contexts" in markdown
    assert "Coverage" in markdown
    assert "Raw context summary" in markdown
    assert "Interpreted context summary" in markdown
    assert "Limitation summary" in markdown
    assert "AI Research Context Consumer Entry" in payload
    assert "recommendation" not in markdown.lower()
    assert "trading signal" not in markdown.lower()

from __future__ import annotations

from ccass_core.compute import compute_analysis
from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.research_context import build_research_context_package
from ccass_core.research_context_handoff import (
    build_research_context_handoff,
    build_research_context_handoff_markdown,
)


def test_research_context_handoff_builds_structured_context(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response)
    ai_read_model = build_ai_read_model_v0_1(
        code=current_response.metadata.code,
        response=current_response,
        previous_response=previous_response,
        analysis=analysis,
        surface="ccass_ai_read_model",
    )
    package = build_research_context_package(
        ai_read_model=ai_read_model,
    )

    handoff = build_research_context_handoff(
        package,
        analysis=analysis,
        report_reference="01592_ccass_report.md",
    )

    assert handoff.available is True
    assert handoff.identity is not None
    assert handoff.identity.stock_code == "01592"
    assert handoff.snapshot_reference is not None
    assert handoff.ownership_overview is not None
    assert handoff.ownership_overview.available is True
    assert handoff.holder_change_overview is not None
    assert handoff.holder_change_overview.available is True
    assert handoff.concentration_overview is not None
    assert handoff.concentration_overview.available is True
    assert handoff.report_reference == "01592_ccass_report.md"
    assert "freshness=" in handoff.quality_reference
    assert "warnings=" in handoff.quality_reference
    assert handoff.summary.startswith("AI research context handoff:")


def test_research_context_handoff_markdown_includes_summary_and_reference(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response)
    ai_read_model = build_ai_read_model_v0_1(
        code=current_response.metadata.code,
        response=current_response,
        previous_response=previous_response,
        analysis=analysis,
        surface="ccass_ai_read_model",
    )
    package = build_research_context_package(
        ai_read_model=ai_read_model,
    )
    handoff = build_research_context_handoff(
        package,
        analysis=analysis,
        report_reference="01592_ccass_report.md",
    )

    markdown = build_research_context_handoff_markdown(handoff)

    assert "AI Research Context Handoff" in markdown
    assert "Stock identity" in markdown
    assert "Snapshot reference" in markdown
    assert "Ownership overview" in markdown
    assert "Holder change overview" in markdown
    assert "Concentration overview" in markdown
    assert "Report reference" in markdown
    assert "Handoff contract" in markdown

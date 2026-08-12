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
        governance_reference="governance-ref-001",
    )

    assert handoff.available is True
    assert handoff.identity is not None
    assert handoff.identity.stock_code == "01592"
    assert handoff.snapshot_reference is not None
    assert handoff.coverage is not None
    assert handoff.coverage.coverage_state == "complete"
    assert handoff.coverage.required_contexts == [
        "identity",
        "snapshot",
        "ownership",
        "holder_change",
        "concentration",
        "report_reference",
        "governance_reference",
    ]
    assert handoff.confidence is not None
    assert handoff.confidence.completeness_state == "complete"
    assert handoff.confidence.traceability_state == "strong"
    assert handoff.confidence.confidence_state in {"high", "moderate"}
    assert handoff.readiness is not None
    assert handoff.readiness.readiness_status == "ready"
    assert handoff.readiness.validation_state == "consistent"
    assert handoff.readiness.coverage_state == "complete"
    assert handoff.readiness.confidence_state in {"high", "moderate"}
    assert handoff.readiness.traceability_state == "strong"
    assert "readiness=" in handoff.summary
    assert "confidence=" in handoff.summary
    assert "traceability=" in handoff.summary
    assert "identity" in handoff.coverage.available_contexts
    assert "ownership" in handoff.coverage.available_contexts
    assert "holder_change" in handoff.coverage.available_contexts
    assert "concentration" in handoff.coverage.available_contexts
    assert handoff.ownership_overview is not None
    assert handoff.ownership_overview.available is True
    assert handoff.ownership_overview.source_component == "ownership_context"
    assert handoff.ownership_overview.evidence_reference != "not available"
    assert handoff.ownership_overview.provenance_reference.startswith("source=")
    assert "top holder list" in handoff.ownership_overview.evidence_summary.lower()
    assert handoff.holder_change_overview is not None
    assert handoff.holder_change_overview.available is True
    assert handoff.holder_change_overview.source_component == "historical_context"
    assert " -> " in handoff.holder_change_overview.evidence_reference
    assert handoff.holder_change_overview.provenance_reference.startswith("source=")
    assert handoff.concentration_overview is not None
    assert handoff.concentration_overview.available is True
    assert handoff.concentration_overview.source_component == "ownership_context"
    assert " -> " in handoff.concentration_overview.evidence_reference
    assert handoff.concentration_overview.provenance_reference.startswith("source=")
    assert handoff.report_reference == "01592_ccass_report.md"
    assert handoff.governance_reference == "governance-ref-001"
    assert "traceability=" in handoff.summary
    assert "ownership[" in handoff.traceability_summary
    assert "coverage=" in handoff.raw_context_summary
    assert "interpreted=" in handoff.interpreted_context_summary
    assert "freshness=" in handoff.quality_reference
    assert "warnings=" in handoff.quality_reference
    assert (
        "missing=" in handoff.limitation_summary
        or "warnings=" in handoff.limitation_summary
        or handoff.limitation_summary == "No material limitations detected."
    )
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
        governance_reference="governance-ref-001",
    )

    markdown = build_research_context_handoff_markdown(handoff)

    assert "AI Research Context Handoff" in markdown
    assert "Stock identity" in markdown
    assert "Snapshot reference" in markdown
    assert "Coverage state" in markdown
    assert "Confidence state" in markdown
    assert "Readiness status" in markdown
    assert "Readiness validation" in markdown
    assert "Required contexts" in markdown
    assert "Available contexts" in markdown
    assert "Missing contexts" in markdown
    assert "Uncertainty summary" in markdown
    assert "Readiness summary" in markdown
    assert "Limitation categories" in markdown
    assert "Traceability summary" in markdown
    assert "Ownership overview" in markdown
    assert "Holder change overview" in markdown
    assert "Concentration overview" in markdown
    assert "Coverage" in markdown
    assert "Raw context summary" in markdown
    assert "Interpreted context summary" in markdown
    assert "Report reference" in markdown
    assert "Governance reference" in markdown
    assert "Limitation summary" in markdown
    assert "Handoff contract" in markdown


def test_research_context_handoff_marks_missing_holder_change_context(current_response):
    analysis = compute_analysis(current_response, None)
    ai_read_model = build_ai_read_model_v0_1(
        code=current_response.metadata.code,
        response=current_response,
        previous_response=None,
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
        governance_reference="governance-ref-001",
    )

    assert handoff.coverage is not None
    assert handoff.coverage.coverage_state == "partial"
    assert "holder_change" in handoff.coverage.required_contexts
    assert "holder_change" in handoff.coverage.missing_contexts
    assert handoff.confidence is not None
    assert handoff.confidence.completeness_state == "partial"
    assert handoff.confidence.confidence_state == "limited"
    assert "missing_contexts" in handoff.confidence.limitation_categories
    assert handoff.readiness is not None
    assert handoff.readiness.readiness_status == "partial"
    assert handoff.readiness.validation_state == "partial"
    assert handoff.readiness.coverage_state == "partial"
    assert "warnings" in handoff.readiness.limitation_categories
    assert handoff.holder_change_overview is not None
    assert handoff.holder_change_overview.available is False
    assert handoff.holder_change_overview.evidence_summary.startswith("Previous snapshot data")
    assert "holder change" in handoff.limitation_summary.lower()


def test_research_context_handoff_exposes_unavailable_coverage_when_package_missing():
    handoff = build_research_context_handoff(
        None,
        report_reference="01592_ccass_report.md",
        governance_reference="governance-ref-001",
    )

    assert handoff.available is False
    assert handoff.coverage is not None
    assert handoff.coverage.coverage_state == "unavailable"
    assert "identity" in handoff.coverage.required_contexts
    assert "identity" in handoff.coverage.missing_contexts
    assert handoff.confidence is not None
    assert handoff.confidence.confidence_state == "unavailable"
    assert handoff.confidence.completeness_state == "unavailable"
    assert "context_unavailable" in handoff.confidence.limitation_categories
    assert handoff.readiness is not None
    assert handoff.readiness.readiness_status == "unavailable"
    assert handoff.readiness.validation_state == "unavailable"
    assert handoff.readiness.coverage_state == "unavailable"
    assert "Traceability summary is unavailable." == handoff.traceability_summary
    assert handoff.report_reference == "01592_ccass_report.md"
    assert handoff.governance_reference == "governance-ref-001"

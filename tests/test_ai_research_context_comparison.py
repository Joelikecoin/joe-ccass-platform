from __future__ import annotations

from ccass_core.ai_read_model import AIReadModelSnapshotReference, build_ai_read_model_v0_1
from ccass_core.ai_research_context_comparison import (
    build_ai_research_context_comparison,
    build_ai_research_context_comparison_markdown,
)
from ccass_core.compute import compute_analysis
from app.models import CcassResponse


def _build_read_model(current_response: CcassResponse, previous_response: CcassResponse):
    analysis = compute_analysis(current_response, previous_response)
    return build_ai_read_model_v0_1(
        code=current_response.metadata.code,
        response=current_response,
        surface="ccass_ai_read_model",
        analysis=analysis,
        previous_response=previous_response,
        snapshot_id=101,
        previous_snapshot_id=100,
    )


def _current_snapshot_reference(read_model) -> AIReadModelSnapshotReference | None:
    return AIReadModelSnapshotReference(
        snapshot_id=read_model.history.snapshot_id,
        snapshot_date=read_model.timing.data_as_of,
        data_as_of=read_model.timing.data_as_of,
        fetched_at=read_model.timing.fetched_at,
        source=read_model.provenance.source,
    )


def test_ai_research_context_comparison_captures_snapshot_references(
    current_response, previous_response
):
    read_model = _build_read_model(current_response, previous_response)
    comparison = build_ai_research_context_comparison(
        current_snapshot_reference=_current_snapshot_reference(read_model),
        previous_snapshot_reference=read_model.history.previous_snapshot,
        comparison_metadata=read_model.history.comparison_context,
        audit_trail_reference="trace-001 / audit",
        provenance_reference=read_model.provenance.source,
        governance_reference="governance summary",
        quality_summary_reference="quality summary",
        warning_summary=f"{len(read_model.quality.warnings)} warning(s)",
    )

    assert comparison.available is True
    assert comparison.current_snapshot_reference is not None
    assert comparison.current_snapshot_reference.snapshot_id == 101
    assert comparison.previous_snapshot_reference is not None
    assert comparison.previous_snapshot_reference.snapshot_id == 100
    assert comparison.comparison_metadata is not None
    assert comparison.comparison_metadata.previous_available is True
    assert "change_count=" in comparison.changed_context_reference
    assert "snapshot continuity" in comparison.unchanged_context_reference or "unchanged context" in comparison.unchanged_context_reference
    assert comparison.audit_trail_reference == "trace-001 / audit"
    assert comparison.provenance_reference == read_model.provenance.source
    assert comparison.warning_summary == f"{len(read_model.quality.warnings)} warning(s)"
    assert "AI research context comparison:" in comparison.summary
    assert "current_snapshot=" in comparison.summary
    assert "previous_snapshot=" in comparison.summary


def test_ai_research_context_comparison_markdown_handles_unavailable_state():
    markdown = build_ai_research_context_comparison_markdown(None)

    assert "AI Research Context Comparison" in markdown
    assert "unavailable" in markdown.lower()

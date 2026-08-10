from __future__ import annotations

from ccass_core.ai_read_model import AIReadModelSnapshotReference, build_ai_read_model_v0_1
from ccass_core.ai_research_context_change_summary import (
    build_ai_research_context_change_summary,
    build_ai_research_context_change_summary_markdown,
)
from ccass_core.ai_research_context_comparison import build_ai_research_context_comparison
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


def _comparison(read_model):
    return build_ai_research_context_comparison(
        current_snapshot_reference=_current_snapshot_reference(read_model),
        previous_snapshot_reference=read_model.history.previous_snapshot,
        comparison_metadata=read_model.history.comparison_context,
        audit_trail_reference="trace-001 / audit",
        provenance_reference=read_model.provenance.source,
        governance_reference="governance summary",
        quality_summary_reference="quality summary",
        warning_summary=f"{len(read_model.quality.warnings)} warning(s)",
    )


def test_ai_research_context_change_summary_captures_structural_comparison(
    current_response, previous_response
):
    read_model = _build_read_model(current_response, previous_response)
    change_summary = build_ai_research_context_change_summary(
        _comparison(read_model),
        audit_trail_reference="trace-001 / audit",
        provenance_reference=read_model.provenance.source,
        governance_reference="governance summary",
        quality_summary_reference="quality summary",
        warning_summary=f"{len(read_model.quality.warnings)} warning(s)",
    )

    assert change_summary.available is True
    assert "snapshot_id=101" in change_summary.current_snapshot_summary
    assert "snapshot_id=100" in change_summary.previous_snapshot_summary
    assert "change_count=" in change_summary.changed_items_summary
    assert "unchanged items" in change_summary.unchanged_items_summary or "snapshot continuity" in change_summary.unchanged_items_summary
    assert "previous_available=True" in change_summary.comparison_metadata_summary
    assert change_summary.audit_trail_reference == "trace-001 / audit"
    assert change_summary.provenance_reference == read_model.provenance.source
    assert change_summary.warning_summary == f"{len(read_model.quality.warnings)} warning(s)"
    assert "AI research context change summary:" in change_summary.summary
    assert "current_snapshot=" in change_summary.summary
    assert "changed_items=" in change_summary.summary


def test_ai_research_context_change_summary_markdown_handles_unavailable_state():
    markdown = build_ai_research_context_change_summary_markdown(None)

    assert "AI Research Context Change Summary" in markdown
    assert "unavailable" in markdown.lower()

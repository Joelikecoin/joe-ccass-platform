from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_read_model import (
    AIReadModelComparisonContext,
    AIReadModelSnapshotReference,
)

AI_RESEARCH_CONTEXT_COMPARISON_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_COMPARISON_SURFACE = "ai_research_context_comparison"


class AIResearchContextComparisonContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_COMPARISON_VERSION
    surface: str = AI_RESEARCH_CONTEXT_COMPARISON_SURFACE


class AIResearchContextComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    current_snapshot_reference: AIReadModelSnapshotReference | None = None
    previous_snapshot_reference: AIReadModelSnapshotReference | None = None
    changed_context_reference: str = "not available"
    unchanged_context_reference: str = "not available"
    comparison_metadata: AIReadModelComparisonContext | None = None
    audit_trail_reference: str = "not available"
    provenance_reference: str = "not available"
    governance_reference: str = "unavailable"
    quality_summary_reference: str = "unavailable"
    warning_summary: str = "0 warning(s)"
    summary: str = "AI research context comparison is unavailable."
    comparison_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    contract_meta: AIResearchContextComparisonContractMeta = Field(
        default_factory=AIResearchContextComparisonContractMeta
    )


def build_ai_research_context_comparison(
    *,
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    previous_snapshot_reference: AIReadModelSnapshotReference | None,
    comparison_metadata: AIReadModelComparisonContext | None,
    audit_trail_reference: str,
    provenance_reference: str,
    governance_reference: str,
    quality_summary_reference: str,
    warning_summary: str,
    surface: str = AI_RESEARCH_CONTEXT_COMPARISON_SURFACE,
) -> AIResearchContextComparison:
    available = current_snapshot_reference is not None or previous_snapshot_reference is not None
    comparison_state = _comparison_state(
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        comparison_metadata=comparison_metadata,
    )
    changed_context_reference = _changed_context_reference(comparison_metadata)
    unchanged_context_reference = _unchanged_context_reference(
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        comparison_metadata=comparison_metadata,
    )
    summary = _summary_text(
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        changed_context_reference=changed_context_reference,
        unchanged_context_reference=unchanged_context_reference,
        audit_trail_reference=audit_trail_reference,
        provenance_reference=provenance_reference,
        governance_reference=governance_reference,
        quality_summary_reference=quality_summary_reference,
        warning_summary=warning_summary,
    )
    return AIResearchContextComparison(
        available=available,
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        changed_context_reference=changed_context_reference,
        unchanged_context_reference=unchanged_context_reference,
        comparison_metadata=comparison_metadata,
        audit_trail_reference=audit_trail_reference,
        provenance_reference=provenance_reference,
        governance_reference=governance_reference,
        quality_summary_reference=quality_summary_reference,
        warning_summary=warning_summary,
        summary=summary,
        comparison_state=comparison_state,
        contract_meta=AIResearchContextComparisonContractMeta(surface=surface),
    )


def build_ai_research_context_comparison_markdown(
    comparison: AIResearchContextComparison | None,
) -> str:
    if comparison is None or not comparison.available:
        return "\n".join(
            [
                "### AI Research Context Comparison",
                "",
                "AI research context comparison is unavailable.",
            ]
        )

    rows = [
        ("Current snapshot", _snapshot_reference_text(comparison.current_snapshot_reference)),
        ("Previous snapshot", _snapshot_reference_text(comparison.previous_snapshot_reference)),
        ("Changed context reference", comparison.changed_context_reference),
        ("Unchanged context reference", comparison.unchanged_context_reference),
        (
            "Comparison metadata",
            _comparison_metadata_text(comparison.comparison_metadata),
        ),
        ("Comparison state", comparison.comparison_state),
        ("Audit trail reference", comparison.audit_trail_reference),
        ("Provenance reference", comparison.provenance_reference),
        ("Governance reference", comparison.governance_reference),
        ("Quality summary reference", comparison.quality_summary_reference),
        ("Warning summary", comparison.warning_summary),
        ("Comparison contract", f"{comparison.contract_meta.version} / {comparison.contract_meta.surface}"),
    ]
    lines = [
        "### AI Research Context Comparison",
        "",
        f"*{comparison.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    if comparison.current_snapshot_reference is not None or comparison.previous_snapshot_reference is not None:
        lines.extend(
            [
                "",
                "Snapshot references:",
                f"- current: {_snapshot_reference_text(comparison.current_snapshot_reference)}",
                f"- previous: {_snapshot_reference_text(comparison.previous_snapshot_reference)}",
            ]
        )
    return "\n".join(lines)


def _snapshot_reference_text(snapshot_reference: AIReadModelSnapshotReference | None) -> str:
    if snapshot_reference is None:
        return "not available"
    return (
        f"snapshot_id={snapshot_reference.snapshot_id if snapshot_reference.snapshot_id is not None else 'not available'}; "
        f"snapshot_date={snapshot_reference.snapshot_date if snapshot_reference.snapshot_date is not None else 'not available'}; "
        f"data_as_of={snapshot_reference.data_as_of if snapshot_reference.data_as_of is not None else 'not available'}; "
        f"fetched_at={snapshot_reference.fetched_at if snapshot_reference.fetched_at is not None else 'not available'}; "
        f"source={snapshot_reference.source if snapshot_reference.source is not None else 'not available'}"
    )


def _comparison_metadata_text(comparison_metadata: AIReadModelComparisonContext | None) -> str:
    if comparison_metadata is None:
        return "not available"
    return (
        f"previous_available={comparison_metadata.previous_available}; "
        f"previous_snapshot_id={comparison_metadata.previous_snapshot_id if comparison_metadata.previous_snapshot_id is not None else 'not available'}; "
        f"previous_snapshot_date={comparison_metadata.previous_snapshot_date if comparison_metadata.previous_snapshot_date is not None else 'not available'}; "
        f"change_count={comparison_metadata.change_count if comparison_metadata.change_count is not None else 'not available'}; "
        f"big_change_count={comparison_metadata.big_change_count if comparison_metadata.big_change_count is not None else 'not available'}; "
        f"note={comparison_metadata.note if comparison_metadata.note is not None else 'not available'}"
    )


def _changed_context_reference(comparison_metadata: AIReadModelComparisonContext | None) -> str:
    if comparison_metadata is None:
        return "not available"
    return (
        f"change_count={comparison_metadata.change_count if comparison_metadata.change_count is not None else 'not available'}; "
        f"big_change_count={comparison_metadata.big_change_count if comparison_metadata.big_change_count is not None else 'not available'}; "
        f"previous_available={comparison_metadata.previous_available}"
    )


def _unchanged_context_reference(
    *,
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    previous_snapshot_reference: AIReadModelSnapshotReference | None,
    comparison_metadata: AIReadModelComparisonContext | None,
) -> str:
    if current_snapshot_reference is None:
        return "not available"
    if previous_snapshot_reference is None or comparison_metadata is None:
        return "unchanged context is not enumerated by this layer."
    if comparison_metadata.previous_available:
        return "snapshot continuity is preserved; unchanged context is not enumerated by this layer."
    return "previous snapshot is unavailable; unchanged context is not enumerated by this layer."


def _comparison_state(
    *,
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    previous_snapshot_reference: AIReadModelSnapshotReference | None,
    comparison_metadata: AIReadModelComparisonContext | None,
) -> Literal["available", "partial", "unavailable", "unknown"]:
    if current_snapshot_reference is None:
        return "unavailable"
    if previous_snapshot_reference is None or comparison_metadata is None:
        return "partial"
    if comparison_metadata.previous_available:
        return "available"
    return "partial"


def _summary_text(
    *,
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    previous_snapshot_reference: AIReadModelSnapshotReference | None,
    changed_context_reference: str,
    unchanged_context_reference: str,
    audit_trail_reference: str,
    provenance_reference: str,
    governance_reference: str,
    quality_summary_reference: str,
    warning_summary: str,
) -> str:
    return (
        "AI research context comparison: "
        f"current_snapshot={_snapshot_reference_text(current_snapshot_reference)}; "
        f"previous_snapshot={_snapshot_reference_text(previous_snapshot_reference)}; "
        f"changed_context={changed_context_reference}; "
        f"unchanged_context={unchanged_context_reference}; "
        f"audit={audit_trail_reference}; "
        f"provenance={provenance_reference}; "
        f"governance={governance_reference}; "
        f"quality={quality_summary_reference}; "
        f"warnings={warning_summary}"
    )

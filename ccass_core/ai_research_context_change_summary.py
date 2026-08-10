from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_read_model import AIReadModelComparisonContext, AIReadModelSnapshotReference
from ccass_core.ai_research_context_comparison import AIResearchContextComparison

AI_RESEARCH_CONTEXT_CHANGE_SUMMARY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CHANGE_SUMMARY_SURFACE = "ai_research_context_change_summary"


class AIResearchContextChangeSummaryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CHANGE_SUMMARY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CHANGE_SUMMARY_SURFACE


class AIResearchContextChangeSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    current_snapshot_summary: str = "not available"
    previous_snapshot_summary: str = "not available"
    changed_items_summary: str = "not available"
    unchanged_items_summary: str = "not available"
    comparison_metadata_summary: str = "not available"
    audit_trail_reference: str = "not available"
    provenance_reference: str = "not available"
    governance_reference: str = "unavailable"
    quality_summary_reference: str = "unavailable"
    warning_summary: str = "0 warning(s)"
    summary: str = "AI research context change summary is unavailable."
    comparison_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    contract_meta: AIResearchContextChangeSummaryContractMeta = Field(
        default_factory=AIResearchContextChangeSummaryContractMeta
    )


def build_ai_research_context_change_summary(
    comparison: AIResearchContextComparison | None,
    *,
    audit_trail_reference: str,
    provenance_reference: str,
    governance_reference: str,
    quality_summary_reference: str,
    warning_summary: str,
    surface: str = AI_RESEARCH_CONTEXT_CHANGE_SUMMARY_SURFACE,
) -> AIResearchContextChangeSummary:
    current_snapshot_reference = (
        comparison.current_snapshot_reference if comparison is not None else None
    )
    previous_snapshot_reference = (
        comparison.previous_snapshot_reference if comparison is not None else None
    )
    comparison_metadata = comparison.comparison_metadata if comparison is not None else None
    available = current_snapshot_reference is not None
    comparison_state = _comparison_state(
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        comparison_metadata=comparison_metadata,
    )
    current_snapshot_summary = _snapshot_summary(current_snapshot_reference)
    previous_snapshot_summary = _snapshot_summary(previous_snapshot_reference)
    changed_items_summary = _changed_items_summary(comparison_metadata)
    unchanged_items_summary = _unchanged_items_summary(
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        comparison_metadata=comparison_metadata,
    )
    comparison_metadata_summary = _comparison_metadata_summary(comparison_metadata)
    summary = _summary_text(
        current_snapshot_summary=current_snapshot_summary,
        previous_snapshot_summary=previous_snapshot_summary,
        changed_items_summary=changed_items_summary,
        unchanged_items_summary=unchanged_items_summary,
        comparison_metadata_summary=comparison_metadata_summary,
        audit_trail_reference=audit_trail_reference,
        provenance_reference=provenance_reference,
        governance_reference=governance_reference,
        quality_summary_reference=quality_summary_reference,
        warning_summary=warning_summary,
    )
    return AIResearchContextChangeSummary(
        available=available,
        current_snapshot_summary=current_snapshot_summary,
        previous_snapshot_summary=previous_snapshot_summary,
        changed_items_summary=changed_items_summary,
        unchanged_items_summary=unchanged_items_summary,
        comparison_metadata_summary=comparison_metadata_summary,
        audit_trail_reference=audit_trail_reference,
        provenance_reference=provenance_reference,
        governance_reference=governance_reference,
        quality_summary_reference=quality_summary_reference,
        warning_summary=warning_summary,
        summary=summary,
        comparison_state=comparison_state,
        contract_meta=AIResearchContextChangeSummaryContractMeta(surface=surface),
    )


def build_ai_research_context_change_summary_markdown(
    change_summary: AIResearchContextChangeSummary | None,
) -> str:
    if change_summary is None or not change_summary.available:
        return "\n".join(
            [
                "### AI Research Context Change Summary",
                "",
                "AI research context change summary is unavailable.",
            ]
        )

    rows = [
        ("Current snapshot summary", change_summary.current_snapshot_summary),
        ("Previous snapshot summary", change_summary.previous_snapshot_summary),
        ("Changed items summary", change_summary.changed_items_summary),
        ("Unchanged items summary", change_summary.unchanged_items_summary),
        ("Comparison metadata summary", change_summary.comparison_metadata_summary),
        ("Comparison state", change_summary.comparison_state),
        ("Audit trail reference", change_summary.audit_trail_reference),
        ("Provenance reference", change_summary.provenance_reference),
        ("Governance reference", change_summary.governance_reference),
        ("Quality summary reference", change_summary.quality_summary_reference),
        ("Warning summary", change_summary.warning_summary),
        (
            "Change summary contract",
            f"{change_summary.contract_meta.version} / {change_summary.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Change Summary",
        "",
        f"*{change_summary.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _snapshot_summary(snapshot_reference: AIReadModelSnapshotReference | None) -> str:
    if snapshot_reference is None:
        return "not available"
    return (
        f"snapshot_id={snapshot_reference.snapshot_id if snapshot_reference.snapshot_id is not None else 'not available'}; "
        f"snapshot_date={snapshot_reference.snapshot_date if snapshot_reference.snapshot_date is not None else 'not available'}; "
        f"data_as_of={snapshot_reference.data_as_of if snapshot_reference.data_as_of is not None else 'not available'}; "
        f"fetched_at={snapshot_reference.fetched_at if snapshot_reference.fetched_at is not None else 'not available'}; "
        f"source={snapshot_reference.source if snapshot_reference.source is not None else 'not available'}"
    )


def _comparison_metadata_summary(
    comparison_metadata: AIReadModelComparisonContext | None,
) -> str:
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


def _changed_items_summary(comparison_metadata: AIReadModelComparisonContext | None) -> str:
    if comparison_metadata is None:
        return "not available"
    return (
        f"change_count={comparison_metadata.change_count if comparison_metadata.change_count is not None else 'not available'}; "
        f"big_change_count={comparison_metadata.big_change_count if comparison_metadata.big_change_count is not None else 'not available'}; "
        f"previous_available={comparison_metadata.previous_available}"
    )


def _unchanged_items_summary(
    *,
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    previous_snapshot_reference: AIReadModelSnapshotReference | None,
    comparison_metadata: AIReadModelComparisonContext | None,
) -> str:
    if current_snapshot_reference is None:
        return "not available"
    if previous_snapshot_reference is None or comparison_metadata is None:
        return "unchanged items are not enumerated by this layer."
    if comparison_metadata.previous_available:
        return "snapshot continuity is preserved; unchanged items are not enumerated by this layer."
    return "previous snapshot is unavailable; unchanged items are not enumerated by this layer."


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
    current_snapshot_summary: str,
    previous_snapshot_summary: str,
    changed_items_summary: str,
    unchanged_items_summary: str,
    comparison_metadata_summary: str,
    audit_trail_reference: str,
    provenance_reference: str,
    governance_reference: str,
    quality_summary_reference: str,
    warning_summary: str,
) -> str:
    return (
        "AI research context change summary: "
        f"current_snapshot={current_snapshot_summary}; "
        f"previous_snapshot={previous_snapshot_summary}; "
        f"changed_items={changed_items_summary}; "
        f"unchanged_items={unchanged_items_summary}; "
        f"comparison metadata={comparison_metadata_summary}; "
        f"audit={audit_trail_reference}; "
        f"provenance={provenance_reference}; "
        f"governance={governance_reference}; "
        f"quality={quality_summary_reference}; "
        f"warnings={warning_summary}"
    )

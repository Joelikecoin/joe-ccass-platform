from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_read_model import AIReadModelSnapshotReference
from ccass_core.ai_research_context_change_summary import AIResearchContextChangeSummary
from ccass_core.ai_research_context_comparison import AIResearchContextComparison

AI_RESEARCH_CONTEXT_TIMELINE_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_TIMELINE_SURFACE = "ai_research_context_timeline"


class AIResearchContextTimelineContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_TIMELINE_VERSION
    surface: str = AI_RESEARCH_CONTEXT_TIMELINE_SURFACE


class AIResearchContextTimelineItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    order: int
    role: Literal["historical", "previous", "current", "unknown"] = "unknown"
    snapshot_reference: AIReadModelSnapshotReference | None = None
    timeline_reference: str = "not available"
    comparison_reference: str = "not available"
    change_summary_reference: str = "not available"
    audit_trail_reference: str = "not available"


class AIResearchContextTimeline(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    current_snapshot_reference: AIReadModelSnapshotReference | None = None
    previous_snapshot_reference: AIReadModelSnapshotReference | None = None
    historical_snapshot_metadata: list[AIReadModelSnapshotReference] = Field(default_factory=list)
    timeline_items: list[AIResearchContextTimelineItem] = Field(default_factory=list)
    snapshot_ordering: list[str] = Field(default_factory=list)
    timeline_references: list[str] = Field(default_factory=list)
    linked_comparison_references: list[str] = Field(default_factory=list)
    linked_change_summary_references: list[str] = Field(default_factory=list)
    audit_trail_reference: str = "not available"
    provenance_reference: str = "not available"
    governance_reference: str = "unavailable"
    quality_summary_reference: str = "unavailable"
    warning_summary: str = "0 warning(s)"
    summary: str = "AI research context timeline is unavailable."
    timeline_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    contract_meta: AIResearchContextTimelineContractMeta = Field(
        default_factory=AIResearchContextTimelineContractMeta
    )


def build_ai_research_context_timeline(
    entry: Any,
    *,
    surface: str = AI_RESEARCH_CONTEXT_TIMELINE_SURFACE,
) -> AIResearchContextTimeline:
    if entry is None or not entry.available or entry.delivery is None or entry.delivery.assembly is None:
        return AIResearchContextTimeline(
            summary="AI research context timeline is unavailable.",
            contract_meta=AIResearchContextTimelineContractMeta(surface=surface),
        )

    comparison = entry.comparison
    change_summary = entry.change_summary
    current_snapshot_reference = (
        comparison.current_snapshot_reference if comparison is not None else None
    )
    previous_snapshot_reference = (
        comparison.previous_snapshot_reference if comparison is not None else None
    )
    historical_snapshot_metadata = _historical_snapshot_metadata(entry)
    timeline_items = _timeline_items(
        historical_snapshot_metadata=historical_snapshot_metadata,
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        comparison=comparison,
        change_summary=change_summary,
        audit_trail_reference=entry.audit_trail.creation_reference if entry.audit_trail is not None else "not available",
    )
    snapshot_ordering = [
        f"{item.order}. {item.role} -> {_snapshot_reference_text(item.snapshot_reference)}"
        for item in timeline_items
    ]
    timeline_references = [item.timeline_reference for item in timeline_items]
    linked_comparison_references = _linked_comparison_references(comparison)
    linked_change_summary_references = _linked_change_summary_references(change_summary)
    audit_trail_reference = (
        entry.audit_trail.creation_reference if entry.audit_trail is not None else "not available"
    )
    provenance_reference = entry.provenance_reference
    governance_reference = (
        entry.consumer_view.governance_summary
        if entry.consumer_view is not None
        else entry.limitation_summary
    )
    quality_summary_reference = (
        entry.quality_summary.summary if entry.quality_summary is not None else "unavailable"
    )
    warning_summary = entry.warning_summary
    timeline_state = _timeline_state(
        current_snapshot_reference=current_snapshot_reference,
        historical_snapshot_metadata=historical_snapshot_metadata,
    )
    summary = _summary_text(
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        snapshot_ordering=snapshot_ordering,
        timeline_references=timeline_references,
        linked_comparison_references=linked_comparison_references,
        linked_change_summary_references=linked_change_summary_references,
        audit_trail_reference=audit_trail_reference,
        provenance_reference=provenance_reference,
        governance_reference=governance_reference,
        quality_summary_reference=quality_summary_reference,
        warning_summary=warning_summary,
    )
    return AIResearchContextTimeline(
        available=True,
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        historical_snapshot_metadata=historical_snapshot_metadata,
        timeline_items=timeline_items,
        snapshot_ordering=snapshot_ordering,
        timeline_references=timeline_references,
        linked_comparison_references=linked_comparison_references,
        linked_change_summary_references=linked_change_summary_references,
        audit_trail_reference=audit_trail_reference,
        provenance_reference=provenance_reference,
        governance_reference=governance_reference,
        quality_summary_reference=quality_summary_reference,
        warning_summary=warning_summary,
        summary=summary,
        timeline_state=timeline_state,
        contract_meta=AIResearchContextTimelineContractMeta(surface=surface),
    )


def build_ai_research_context_timeline_markdown(
    timeline: AIResearchContextTimeline | None,
) -> str:
    if timeline is None or not timeline.available:
        return "\n".join(
            [
                "### AI Research Context Timeline",
                "",
                "AI research context timeline is unavailable.",
            ]
        )

    rows = [
        ("Current snapshot", _snapshot_reference_text(timeline.current_snapshot_reference)),
        ("Previous snapshot", _snapshot_reference_text(timeline.previous_snapshot_reference)),
        ("Timeline state", timeline.timeline_state),
        ("Snapshot ordering", _join_list(timeline.snapshot_ordering)),
        ("Timeline references", _join_list(timeline.timeline_references)),
        ("Historical snapshot metadata", str(len(timeline.historical_snapshot_metadata))),
        ("Linked comparison references", _join_list(timeline.linked_comparison_references)),
        ("Linked change summary references", _join_list(timeline.linked_change_summary_references)),
        ("Audit trail reference", timeline.audit_trail_reference),
        ("Provenance reference", timeline.provenance_reference),
        ("Governance reference", timeline.governance_reference),
        ("Quality summary reference", timeline.quality_summary_reference),
        ("Warning summary", timeline.warning_summary),
        ("Timeline contract", f"{timeline.contract_meta.version} / {timeline.contract_meta.surface}"),
    ]
    lines = [
        "### AI Research Context Timeline",
        "",
        f"*{timeline.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    if timeline.timeline_items:
        lines.extend(["", "Timeline items:", "| Order | Role | Snapshot | Comparison | Change summary | Audit trail |", "|---|---|---|---|---|---|"])
        for item in timeline.timeline_items:
            lines.append(
                "| {order} | {role} | {snapshot} | {comparison} | {change_summary} | {audit} |".format(
                    order=item.order,
                    role=item.role,
                    snapshot=_snapshot_reference_text(item.snapshot_reference),
                    comparison=item.comparison_reference,
                    change_summary=item.change_summary_reference,
                    audit=item.audit_trail_reference,
                )
            )
    return "\n".join(lines)


def _historical_snapshot_metadata(entry: Any) -> list[AIReadModelSnapshotReference]:
    references: list[AIReadModelSnapshotReference] = []
    historical_context = (
        entry.delivery.assembly.research_context_consumer_view.historical_context
        if entry.delivery is not None
        and entry.delivery.assembly is not None
        and entry.delivery.assembly.research_context_consumer_view is not None
        else None
    )
    if historical_context is not None:
        references.extend(
            snapshot
            for snapshot in historical_context.history_snapshots
            if snapshot is not None
        )
    if entry.comparison is not None and entry.comparison.previous_snapshot_reference is not None:
        references.append(entry.comparison.previous_snapshot_reference)
    if entry.comparison is not None and entry.comparison.current_snapshot_reference is not None:
        references.append(entry.comparison.current_snapshot_reference)
    return _dedupe_snapshot_references(references)


def _timeline_items(
    *,
    historical_snapshot_metadata: list[AIReadModelSnapshotReference],
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    previous_snapshot_reference: AIReadModelSnapshotReference | None,
    comparison: AIResearchContextComparison | None,
    change_summary,
    audit_trail_reference: str,
) -> list[AIResearchContextTimelineItem]:
    items: list[AIResearchContextTimelineItem] = []
    for index, snapshot_reference in enumerate(historical_snapshot_metadata, start=1):
        role = _role_for_snapshot(
            snapshot_reference,
            current_snapshot_reference=current_snapshot_reference,
            previous_snapshot_reference=previous_snapshot_reference,
        )
        comparison_reference = (
            comparison.summary
            if comparison is not None and role in {"current", "previous"}
            else "not available"
        )
        change_summary_reference = (
            change_summary.summary
            if change_summary is not None and role in {"current", "previous"}
            else "not available"
        )
        items.append(
            AIResearchContextTimelineItem(
                order=index,
                role=role,
                snapshot_reference=snapshot_reference,
                timeline_reference=f"{index}. {_snapshot_reference_text(snapshot_reference)}",
                comparison_reference=comparison_reference,
                change_summary_reference=change_summary_reference,
                audit_trail_reference=audit_trail_reference if role in {"current", "previous"} else "not available",
            )
        )
    return items


def _role_for_snapshot(
    snapshot_reference: AIReadModelSnapshotReference,
    *,
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    previous_snapshot_reference: AIReadModelSnapshotReference | None,
) -> Literal["historical", "previous", "current", "unknown"]:
    if _snapshot_reference_key(snapshot_reference) == _snapshot_reference_key(current_snapshot_reference):
        return "current"
    if _snapshot_reference_key(snapshot_reference) == _snapshot_reference_key(previous_snapshot_reference):
        return "previous"
    return "historical"


def _timeline_state(
    *,
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    historical_snapshot_metadata: list[AIReadModelSnapshotReference],
) -> Literal["available", "partial", "unavailable", "unknown"]:
    if current_snapshot_reference is None:
        return "unavailable"
    if len(historical_snapshot_metadata) >= 2:
        return "available"
    return "partial"


def _linked_comparison_references(
    comparison: AIResearchContextComparison | None,
) -> list[str]:
    if comparison is None:
        return []
    return [
        comparison.summary,
        comparison.changed_context_reference,
        comparison.unchanged_context_reference,
    ]


def _linked_change_summary_references(
    change_summary,
) -> list[str]:
    if change_summary is None:
        return []
    return [
        change_summary.summary,
        change_summary.current_snapshot_summary,
        change_summary.previous_snapshot_summary,
        change_summary.changed_items_summary,
        change_summary.unchanged_items_summary,
        change_summary.comparison_metadata_summary,
    ]


def _dedupe_snapshot_references(
    snapshots: list[AIReadModelSnapshotReference],
) -> list[AIReadModelSnapshotReference]:
    seen: set[tuple[object, ...]] = set()
    ordered: list[AIReadModelSnapshotReference] = []
    for snapshot in snapshots:
        key = _snapshot_reference_key(snapshot)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(snapshot)
    return ordered


def _snapshot_reference_key(
    snapshot_reference: AIReadModelSnapshotReference | None,
) -> tuple[object, ...]:
    if snapshot_reference is None:
        return ("none",)
    return (
        snapshot_reference.snapshot_id,
        snapshot_reference.snapshot_date,
        snapshot_reference.data_as_of,
        snapshot_reference.fetched_at,
        snapshot_reference.source,
    )


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


def _join_list(values: list[str]) -> str:
    if not values:
        return "not available"
    return " | ".join(values)


def _summary_text(
    *,
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    previous_snapshot_reference: AIReadModelSnapshotReference | None,
    snapshot_ordering: list[str],
    timeline_references: list[str],
    linked_comparison_references: list[str],
    linked_change_summary_references: list[str],
    audit_trail_reference: str,
    provenance_reference: str,
    governance_reference: str,
    quality_summary_reference: str,
    warning_summary: str,
) -> str:
    return (
        "AI research context timeline: "
        f"current_snapshot={_snapshot_reference_text(current_snapshot_reference)}; "
        f"previous_snapshot={_snapshot_reference_text(previous_snapshot_reference)}; "
        f"snapshot_ordering={_join_list(snapshot_ordering)}; "
        f"timeline_references={_join_list(timeline_references)}; "
        f"comparison_references={_join_list(linked_comparison_references)}; "
        f"change_summary_references={_join_list(linked_change_summary_references)}; "
        f"audit={audit_trail_reference}; "
        f"provenance={provenance_reference}; "
        f"governance={governance_reference}; "
        f"quality={quality_summary_reference}; "
        f"warnings={warning_summary}"
    )

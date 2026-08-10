from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_read_model import AIReadModelSnapshotReference
from ccass_core.ai_research_context_timeline import AIResearchContextTimeline

AI_RESEARCH_CONTEXT_HISTORICAL_QUERY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_HISTORICAL_QUERY_SURFACE = "ai_research_context_historical_query"


class AIResearchContextHistoricalQueryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_HISTORICAL_QUERY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_HISTORICAL_QUERY_SURFACE


class AIResearchContextHistoricalQueryItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    order: int
    role: Literal["historical", "previous", "current", "unknown"] = "unknown"
    snapshot_reference: AIReadModelSnapshotReference | None = None
    historical_snapshot_lookup_reference: str = "not available"
    timeline_position_reference: str = "not available"
    comparison_reference_lookup: str = "not available"


class AIResearchContextHistoricalQuery(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    latest_snapshot_reference: AIReadModelSnapshotReference | None = None
    historical_snapshot_lookup_references: list[AIReadModelSnapshotReference] = Field(default_factory=list)
    timeline_position_references: list[str] = Field(default_factory=list)
    comparison_reference_lookups: list[str] = Field(default_factory=list)
    query_items: list[AIResearchContextHistoricalQueryItem] = Field(default_factory=list)
    timeline_reference: str = "not available"
    summary: str = "AI research context historical query is unavailable."
    query_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    contract_meta: AIResearchContextHistoricalQueryContractMeta = Field(
        default_factory=AIResearchContextHistoricalQueryContractMeta
    )


def build_ai_research_context_historical_query(
    timeline: AIResearchContextTimeline | None,
    *,
    surface: str = AI_RESEARCH_CONTEXT_HISTORICAL_QUERY_SURFACE,
) -> AIResearchContextHistoricalQuery:
    if timeline is None or not timeline.available:
        return AIResearchContextHistoricalQuery(
            summary="AI research context historical query is unavailable.",
            contract_meta=AIResearchContextHistoricalQueryContractMeta(surface=surface),
        )

    query_items = _query_items(timeline)
    latest_snapshot_reference = timeline.current_snapshot_reference
    historical_snapshot_lookup_references = _historical_snapshot_lookup_references(timeline)
    timeline_position_references = _timeline_position_references(query_items)
    comparison_reference_lookups = _comparison_reference_lookups(query_items)
    timeline_reference = _timeline_reference(timeline)
    query_state = _query_state(
        latest_snapshot_reference=latest_snapshot_reference,
        query_items=query_items,
    )
    summary = _summary_text(
        latest_snapshot_reference=latest_snapshot_reference,
        historical_snapshot_lookup_references=historical_snapshot_lookup_references,
        timeline_position_references=timeline_position_references,
        comparison_reference_lookups=comparison_reference_lookups,
        timeline_reference=timeline_reference,
    )
    return AIResearchContextHistoricalQuery(
        available=True,
        latest_snapshot_reference=latest_snapshot_reference,
        historical_snapshot_lookup_references=historical_snapshot_lookup_references,
        timeline_position_references=timeline_position_references,
        comparison_reference_lookups=comparison_reference_lookups,
        query_items=query_items,
        timeline_reference=timeline_reference,
        summary=summary,
        query_state=query_state,
        contract_meta=AIResearchContextHistoricalQueryContractMeta(surface=surface),
    )


def build_ai_research_context_historical_query_markdown(
    historical_query: AIResearchContextHistoricalQuery | None,
) -> str:
    if historical_query is None or not historical_query.available:
        return "\n".join(
            [
                "### AI Research Context Historical Query",
                "",
                "AI research context historical query is unavailable.",
            ]
        )

    rows = [
        ("Latest snapshot reference", _snapshot_reference_text(historical_query.latest_snapshot_reference)),
        ("Historical snapshot lookup reference", _join_snapshot_references(historical_query.historical_snapshot_lookup_references)),
        ("Timeline position reference", _join_list(historical_query.timeline_position_references)),
        ("Comparison reference lookup", _join_list(historical_query.comparison_reference_lookups)),
        ("Timeline reference", historical_query.timeline_reference),
        ("Query state", historical_query.query_state),
        (
            "Historical query contract",
            f"{historical_query.contract_meta.version} / {historical_query.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Historical Query",
        "",
        f"*{historical_query.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    if historical_query.query_items:
        lines.extend(
            [
                "",
                "Query items:",
                "| Order | Role | Snapshot | Timeline position | Comparison reference |",
                "|---|---|---|---|---|",
            ]
        )
        for item in historical_query.query_items:
            lines.append(
                "| {order} | {role} | {snapshot} | {timeline} | {comparison} |".format(
                    order=item.order,
                    role=item.role,
                    snapshot=_snapshot_reference_text(item.snapshot_reference),
                    timeline=item.timeline_position_reference,
                    comparison=item.comparison_reference_lookup,
                )
            )
    return "\n".join(lines)


def lookup_historical_snapshot_reference(
    historical_query: AIResearchContextHistoricalQuery | None,
    snapshot_id: int | None,
) -> AIReadModelSnapshotReference | None:
    if historical_query is None or snapshot_id is None:
        return None
    for snapshot_reference in historical_query.historical_snapshot_lookup_references:
        if snapshot_reference.snapshot_id == snapshot_id:
            return snapshot_reference
    return None


def lookup_timeline_position_reference(
    historical_query: AIResearchContextHistoricalQuery | None,
    position: int | None,
) -> str:
    if historical_query is None or position is None:
        return "not available"
    if position < 1 or position > len(historical_query.query_items):
        return "not available"
    return historical_query.query_items[position - 1].timeline_position_reference


def lookup_comparison_reference(
    historical_query: AIResearchContextHistoricalQuery | None,
    snapshot_id: int | None,
) -> str:
    if historical_query is None or snapshot_id is None:
        return "not available"
    for item in historical_query.query_items:
        if item.snapshot_reference is not None and item.snapshot_reference.snapshot_id == snapshot_id:
            return item.comparison_reference_lookup
    return "not available"


def _query_items(timeline: AIResearchContextTimeline) -> list[AIResearchContextHistoricalQueryItem]:
    items: list[AIResearchContextHistoricalQueryItem] = []
    for item in timeline.timeline_items:
        items.append(
            AIResearchContextHistoricalQueryItem(
                order=item.order,
                role=item.role,
                snapshot_reference=item.snapshot_reference,
                historical_snapshot_lookup_reference=_snapshot_reference_text(item.snapshot_reference),
                timeline_position_reference=_timeline_position_reference(item),
                comparison_reference_lookup=item.comparison_reference,
            )
        )
    return items


def _historical_snapshot_lookup_references(
    timeline: AIResearchContextTimeline,
) -> list[AIReadModelSnapshotReference]:
    return list(timeline.historical_snapshot_metadata)


def _timeline_position_references(
    query_items: list[AIResearchContextHistoricalQueryItem],
) -> list[str]:
    return [item.timeline_position_reference for item in query_items]


def _comparison_reference_lookups(
    query_items: list[AIResearchContextHistoricalQueryItem],
) -> list[str]:
    references = [item.comparison_reference_lookup for item in query_items]
    references = [reference for reference in references if reference and reference != "not available"]
    if not references:
        return ["not available"]
    return list(dict.fromkeys(references))


def _timeline_reference(timeline: AIResearchContextTimeline) -> str:
    return f"{timeline.contract_meta.version} / {timeline.contract_meta.surface}"


def _timeline_position_reference(item: AIResearchContextHistoricalQueryItem) -> str:
    return (
        f"position={item.order}; "
        f"role={item.role}; "
        f"snapshot={_snapshot_reference_text(item.snapshot_reference)}"
    )


def _query_state(
    *,
    latest_snapshot_reference: AIReadModelSnapshotReference | None,
    query_items: list[AIResearchContextHistoricalQueryItem],
) -> Literal["available", "partial", "unavailable", "unknown"]:
    if latest_snapshot_reference is None:
        return "unavailable"
    if len(query_items) >= 2:
        return "available"
    return "partial"


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


def _join_snapshot_references(values: list[AIReadModelSnapshotReference]) -> str:
    if not values:
        return "not available"
    return " | ".join(_snapshot_reference_text(value) for value in values)


def _summary_text(
    *,
    latest_snapshot_reference: AIReadModelSnapshotReference | None,
    historical_snapshot_lookup_references: list[AIReadModelSnapshotReference],
    timeline_position_references: list[str],
    comparison_reference_lookups: list[str],
    timeline_reference: str,
) -> str:
    return (
        "AI research context historical query: "
        f"latest_snapshot={_snapshot_reference_text(latest_snapshot_reference)}; "
        f"historical_snapshot_lookup={_join_snapshot_references(historical_snapshot_lookup_references)}; "
        f"timeline_position={_join_list(timeline_position_references)}; "
        f"comparison_reference_lookup={_join_list(comparison_reference_lookups)}; "
        f"timeline_reference={timeline_reference}"
    )

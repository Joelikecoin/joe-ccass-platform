from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_read_model import AIReadModelSnapshotReference
from ccass_core.ai_research_context_change_summary import AIResearchContextChangeSummary
from ccass_core.ai_research_context_comparison import AIResearchContextComparison
from ccass_core.ai_research_context_timeline import AIResearchContextTimeline

AI_RESEARCH_CONTEXT_HISTORICAL_COMPARISON_QUERY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_HISTORICAL_COMPARISON_QUERY_SURFACE = (
    "ai_research_context_historical_comparison_query"
)


class AIResearchContextHistoricalComparisonQueryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_HISTORICAL_COMPARISON_QUERY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_HISTORICAL_COMPARISON_QUERY_SURFACE


class AIResearchContextHistoricalComparisonQueryItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    order: int = 1
    current_snapshot_reference: AIReadModelSnapshotReference | None = None
    previous_snapshot_reference: AIReadModelSnapshotReference | None = None
    snapshot_pair_reference: str = "not available"
    snapshot_pair_comparison_reference: str = "not available"
    linked_change_summary_reference: str = "not available"


class AIResearchContextHistoricalComparisonQuery(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    current_snapshot_reference: AIReadModelSnapshotReference | None = None
    previous_snapshot_reference: AIReadModelSnapshotReference | None = None
    snapshot_pair_reference: str = "not available"
    snapshot_pair_comparison_reference: str = "not available"
    linked_change_summary_reference: str = "not available"
    query_items: list[AIResearchContextHistoricalComparisonQueryItem] = Field(default_factory=list)
    timeline_reference: str = "not available"
    summary: str = "AI research context historical comparison query is unavailable."
    query_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    contract_meta: AIResearchContextHistoricalComparisonQueryContractMeta = Field(
        default_factory=AIResearchContextHistoricalComparisonQueryContractMeta
    )


def build_ai_research_context_historical_comparison_query(
    comparison: AIResearchContextComparison | None,
    change_summary: AIResearchContextChangeSummary | None,
    timeline: AIResearchContextTimeline | None,
    *,
    surface: str = AI_RESEARCH_CONTEXT_HISTORICAL_COMPARISON_QUERY_SURFACE,
) -> AIResearchContextHistoricalComparisonQuery:
    current_snapshot_reference = (
        comparison.current_snapshot_reference if comparison is not None else None
    )
    previous_snapshot_reference = (
        comparison.previous_snapshot_reference if comparison is not None else None
    )
    snapshot_pair_reference = _snapshot_pair_reference(
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
    )
    snapshot_pair_comparison_reference = (
        comparison.summary if comparison is not None else "not available"
    )
    linked_change_summary_reference = (
        change_summary.summary if change_summary is not None else "not available"
    )
    timeline_reference = _timeline_reference(timeline)
    query_items = [
        AIResearchContextHistoricalComparisonQueryItem(
            order=1,
            current_snapshot_reference=current_snapshot_reference,
            previous_snapshot_reference=previous_snapshot_reference,
            snapshot_pair_reference=snapshot_pair_reference,
            snapshot_pair_comparison_reference=snapshot_pair_comparison_reference,
            linked_change_summary_reference=linked_change_summary_reference,
        )
    ]
    query_state = _query_state(
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        comparison=comparison,
        change_summary=change_summary,
        timeline=timeline,
    )
    summary = _summary_text(
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        snapshot_pair_reference=snapshot_pair_reference,
        snapshot_pair_comparison_reference=snapshot_pair_comparison_reference,
        linked_change_summary_reference=linked_change_summary_reference,
        timeline_reference=timeline_reference,
    )
    available = current_snapshot_reference is not None or previous_snapshot_reference is not None
    if not available and (timeline is None or not timeline.available):
        return AIResearchContextHistoricalComparisonQuery(
            summary="AI research context historical comparison query is unavailable.",
            contract_meta=AIResearchContextHistoricalComparisonQueryContractMeta(surface=surface),
        )
    return AIResearchContextHistoricalComparisonQuery(
        available=available,
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        snapshot_pair_reference=snapshot_pair_reference,
        snapshot_pair_comparison_reference=snapshot_pair_comparison_reference,
        linked_change_summary_reference=linked_change_summary_reference,
        query_items=query_items,
        timeline_reference=timeline_reference,
        summary=summary,
        query_state=query_state,
        contract_meta=AIResearchContextHistoricalComparisonQueryContractMeta(surface=surface),
    )


def build_ai_research_context_historical_comparison_query_markdown(
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
) -> str:
    if historical_comparison_query is None or not historical_comparison_query.available:
        return "\n".join(
            [
                "### AI Research Context Historical Comparison Query",
                "",
                "AI research context historical comparison query is unavailable.",
            ]
        )

    rows = [
        (
            "Current snapshot reference lookup",
            _snapshot_reference_text(historical_comparison_query.current_snapshot_reference),
        ),
        (
            "Previous snapshot reference lookup",
            _snapshot_reference_text(historical_comparison_query.previous_snapshot_reference),
        ),
        ("Snapshot pair reference", historical_comparison_query.snapshot_pair_reference),
        (
            "Snapshot pair comparison reference",
            historical_comparison_query.snapshot_pair_comparison_reference,
        ),
        (
            "Linked change summary reference",
            historical_comparison_query.linked_change_summary_reference,
        ),
        ("Timeline reference", historical_comparison_query.timeline_reference),
        ("Query state", historical_comparison_query.query_state),
        (
            "Historical comparison query contract",
            (
                f"{historical_comparison_query.contract_meta.version} / "
                f"{historical_comparison_query.contract_meta.surface}"
            ),
        ),
    ]
    lines = [
        "### AI Research Context Historical Comparison Query",
        "",
        f"*{historical_comparison_query.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    if historical_comparison_query.query_items:
        lines.extend(
            [
                "",
                "Query items:",
                "| Order | Current snapshot | Previous snapshot | Pair reference | Comparison reference | Change summary reference |",
                "|---|---|---|---|---|---|",
            ]
        )
        for item in historical_comparison_query.query_items:
            lines.append(
                "| {order} | {current} | {previous} | {pair} | {comparison} | {change_summary} |".format(
                    order=item.order,
                    current=_snapshot_reference_text(item.current_snapshot_reference),
                    previous=_snapshot_reference_text(item.previous_snapshot_reference),
                    pair=item.snapshot_pair_reference,
                    comparison=item.snapshot_pair_comparison_reference,
                    change_summary=item.linked_change_summary_reference,
                )
            )
    return "\n".join(lines)


def lookup_current_snapshot_reference(
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
    snapshot_id: int | None,
) -> AIReadModelSnapshotReference | None:
    if historical_comparison_query is None or snapshot_id is None:
        return None
    current_snapshot_reference = historical_comparison_query.current_snapshot_reference
    if current_snapshot_reference is not None and current_snapshot_reference.snapshot_id == snapshot_id:
        return current_snapshot_reference
    return None


def lookup_previous_snapshot_reference(
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
    snapshot_id: int | None,
) -> AIReadModelSnapshotReference | None:
    if historical_comparison_query is None or snapshot_id is None:
        return None
    previous_snapshot_reference = historical_comparison_query.previous_snapshot_reference
    if previous_snapshot_reference is not None and previous_snapshot_reference.snapshot_id == snapshot_id:
        return previous_snapshot_reference
    return None


def lookup_snapshot_pair_comparison_reference(
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
    *,
    current_snapshot_id: int | None,
    previous_snapshot_id: int | None,
) -> str:
    if historical_comparison_query is None:
        return "not available"
    if not _pair_matches(
        historical_comparison_query,
        current_snapshot_id=current_snapshot_id,
        previous_snapshot_id=previous_snapshot_id,
    ):
        return "not available"
    return historical_comparison_query.snapshot_pair_comparison_reference


def lookup_linked_change_summary_reference(
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
    *,
    current_snapshot_id: int | None,
    previous_snapshot_id: int | None,
) -> str:
    if historical_comparison_query is None:
        return "not available"
    if not _pair_matches(
        historical_comparison_query,
        current_snapshot_id=current_snapshot_id,
        previous_snapshot_id=previous_snapshot_id,
    ):
        return "not available"
    return historical_comparison_query.linked_change_summary_reference


def _pair_matches(
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery,
    *,
    current_snapshot_id: int | None,
    previous_snapshot_id: int | None,
) -> bool:
    current_snapshot_reference = historical_comparison_query.current_snapshot_reference
    previous_snapshot_reference = historical_comparison_query.previous_snapshot_reference
    if current_snapshot_reference is None or previous_snapshot_reference is None:
        return False
    return (
        current_snapshot_reference.snapshot_id == current_snapshot_id
        and previous_snapshot_reference.snapshot_id == previous_snapshot_id
    )


def _timeline_reference(timeline: AIResearchContextTimeline | None) -> str:
    if timeline is None:
        return "not available"
    return f"{timeline.contract_meta.version} / {timeline.contract_meta.surface}"


def _snapshot_pair_reference(
    *,
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    previous_snapshot_reference: AIReadModelSnapshotReference | None,
) -> str:
    return (
        "current="
        + _snapshot_reference_text(current_snapshot_reference)
        + "; previous="
        + _snapshot_reference_text(previous_snapshot_reference)
    )


def _query_state(
    *,
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    previous_snapshot_reference: AIReadModelSnapshotReference | None,
    comparison: AIResearchContextComparison | None,
    change_summary: AIResearchContextChangeSummary | None,
    timeline: AIResearchContextTimeline | None,
) -> Literal["available", "partial", "unavailable", "unknown"]:
    if current_snapshot_reference is None and previous_snapshot_reference is None:
        return "unavailable" if timeline is None or not timeline.available else "partial"
    if comparison is None or change_summary is None:
        return "partial"
    return "available"


def _summary_text(
    *,
    current_snapshot_reference: AIReadModelSnapshotReference | None,
    previous_snapshot_reference: AIReadModelSnapshotReference | None,
    snapshot_pair_reference: str,
    snapshot_pair_comparison_reference: str,
    linked_change_summary_reference: str,
    timeline_reference: str,
) -> str:
    return (
        "AI research context historical comparison query: "
        f"current_snapshot={_snapshot_reference_text(current_snapshot_reference)}; "
        f"previous_snapshot={_snapshot_reference_text(previous_snapshot_reference)}; "
        f"snapshot_pair={snapshot_pair_reference}; "
        f"snapshot_pair_comparison={snapshot_pair_comparison_reference}; "
        f"linked_change_summary={linked_change_summary_reference}; "
        f"timeline_reference={timeline_reference}"
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

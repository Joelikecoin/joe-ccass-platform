from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_read_model import AIReadModelSnapshotReference
from ccass_core.ai_research_context_change_summary import AIResearchContextChangeSummary
from ccass_core.ai_research_context_historical_comparison_query import (
    AIResearchContextHistoricalComparisonQuery,
)
from ccass_core.ai_research_context_historical_query import AIResearchContextHistoricalQuery
from ccass_core.ai_research_context_timeline_summary import AIResearchContextTimelineSummary

AI_RESEARCH_CONTEXT_HISTORICAL_SUMMARY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_HISTORICAL_SUMMARY_SURFACE = "ai_research_context_historical_summary"


class AIResearchContextHistoricalSummaryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_HISTORICAL_SUMMARY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_HISTORICAL_SUMMARY_SURFACE


class AIResearchContextHistoricalSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    latest_snapshot_reference: AIReadModelSnapshotReference | None = None
    historical_snapshot_summary: str = "not available"
    timeline_summary_reference: str = "not available"
    comparison_summary_reference: str = "not available"
    change_history_reference: str = "not available"
    historical_query_reference: str = "not available"
    historical_comparison_query_reference: str = "not available"
    summary: str = "AI research context historical summary is unavailable."
    historical_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    contract_meta: AIResearchContextHistoricalSummaryContractMeta = Field(
        default_factory=AIResearchContextHistoricalSummaryContractMeta
    )


def build_ai_research_context_historical_summary(
    historical_query: AIResearchContextHistoricalQuery | None,
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
    timeline_summary: AIResearchContextTimelineSummary | None,
    change_summary: AIResearchContextChangeSummary | None,
    *,
    surface: str = AI_RESEARCH_CONTEXT_HISTORICAL_SUMMARY_SURFACE,
) -> AIResearchContextHistoricalSummary:
    latest_snapshot_reference = _latest_snapshot_reference(
        historical_query=historical_query,
        historical_comparison_query=historical_comparison_query,
    )
    historical_snapshot_summary = _historical_snapshot_summary(historical_query)
    timeline_summary_reference = _timeline_summary_reference(timeline_summary)
    comparison_summary_reference = _comparison_summary_reference(historical_comparison_query)
    change_history_reference = _change_history_reference(timeline_summary, change_summary)
    historical_query_reference = (
        historical_query.summary if historical_query is not None and historical_query.available else "not available"
    )
    historical_comparison_query_reference = (
        historical_comparison_query.summary
        if historical_comparison_query is not None and historical_comparison_query.available
        else "not available"
    )
    historical_state = _historical_state(
        latest_snapshot_reference=latest_snapshot_reference,
        historical_query=historical_query,
        historical_comparison_query=historical_comparison_query,
        timeline_summary=timeline_summary,
        change_summary=change_summary,
    )
    available = historical_state != "unavailable"
    if not available:
        return AIResearchContextHistoricalSummary(
            summary="AI research context historical summary is unavailable.",
            contract_meta=AIResearchContextHistoricalSummaryContractMeta(surface=surface),
        )

    summary = _summary_text(
        latest_snapshot_reference=latest_snapshot_reference,
        historical_snapshot_summary=historical_snapshot_summary,
        timeline_summary_reference=timeline_summary_reference,
        comparison_summary_reference=comparison_summary_reference,
        change_history_reference=change_history_reference,
        historical_query_reference=historical_query_reference,
        historical_comparison_query_reference=historical_comparison_query_reference,
    )
    return AIResearchContextHistoricalSummary(
        available=True,
        latest_snapshot_reference=latest_snapshot_reference,
        historical_snapshot_summary=historical_snapshot_summary,
        timeline_summary_reference=timeline_summary_reference,
        comparison_summary_reference=comparison_summary_reference,
        change_history_reference=change_history_reference,
        historical_query_reference=historical_query_reference,
        historical_comparison_query_reference=historical_comparison_query_reference,
        summary=summary,
        historical_state=historical_state,
        contract_meta=AIResearchContextHistoricalSummaryContractMeta(surface=surface),
    )


def build_ai_research_context_historical_summary_markdown(
    historical_summary: AIResearchContextHistoricalSummary | None,
) -> str:
    if historical_summary is None or not historical_summary.available:
        return "\n".join(
            [
                "### AI Research Context Historical Summary",
                "",
                "AI research context historical summary is unavailable.",
            ]
        )

    rows = [
        (
            "Latest snapshot reference",
            _snapshot_reference_text(historical_summary.latest_snapshot_reference),
        ),
        ("Historical snapshot summary", historical_summary.historical_snapshot_summary),
        ("Timeline summary reference", historical_summary.timeline_summary_reference),
        ("Comparison summary reference", historical_summary.comparison_summary_reference),
        ("Change history reference", historical_summary.change_history_reference),
        ("Historical query reference", historical_summary.historical_query_reference),
        (
            "Historical comparison query reference",
            historical_summary.historical_comparison_query_reference,
        ),
        ("Historical state", historical_summary.historical_state),
        (
            "Historical summary contract",
            f"{historical_summary.contract_meta.version} / {historical_summary.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Historical Summary",
        "",
        f"*{historical_summary.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _latest_snapshot_reference(
    *,
    historical_query: AIResearchContextHistoricalQuery | None,
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
) -> AIReadModelSnapshotReference | None:
    if historical_query is not None and historical_query.latest_snapshot_reference is not None:
        return historical_query.latest_snapshot_reference
    if (
        historical_comparison_query is not None
        and historical_comparison_query.current_snapshot_reference is not None
    ):
        return historical_comparison_query.current_snapshot_reference
    return None


def _historical_snapshot_summary(
    historical_query: AIResearchContextHistoricalQuery | None,
) -> str:
    if historical_query is None or not historical_query.available:
        return "not available"
    return (
        f"latest={_snapshot_reference_text(historical_query.latest_snapshot_reference)}; "
        f"historical_lookup={_join_snapshot_references(historical_query.historical_snapshot_lookup_references)}; "
        f"timeline_position={_join_list(historical_query.timeline_position_references)}"
    )


def _timeline_summary_reference(timeline_summary: AIResearchContextTimelineSummary | None) -> str:
    if timeline_summary is None or not timeline_summary.available:
        return "not available"
    return timeline_summary.summary


def _comparison_summary_reference(
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
) -> str:
    if historical_comparison_query is None or not historical_comparison_query.available:
        return "not available"
    return historical_comparison_query.snapshot_pair_comparison_reference


def _change_history_reference(
    timeline_summary: AIResearchContextTimelineSummary | None,
    change_summary: AIResearchContextChangeSummary | None,
) -> str:
    if timeline_summary is not None and timeline_summary.available:
        return timeline_summary.change_history_summary
    if change_summary is not None and change_summary.available:
        return change_summary.changed_items_summary
    return "not available"


def _historical_state(
    *,
    latest_snapshot_reference: AIReadModelSnapshotReference | None,
    historical_query: AIResearchContextHistoricalQuery | None,
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
    timeline_summary: AIResearchContextTimelineSummary | None,
    change_summary: AIResearchContextChangeSummary | None,
) -> Literal["available", "partial", "unavailable", "unknown"]:
    if latest_snapshot_reference is None:
        return "unavailable"

    references = [
        historical_query.available if historical_query is not None else False,
        historical_comparison_query.available if historical_comparison_query is not None else False,
        timeline_summary.available if timeline_summary is not None else False,
        change_summary.available if change_summary is not None else False,
    ]
    if all(references):
        return "available"
    if any(references):
        return "partial"
    return "partial"


def _summary_text(
    *,
    latest_snapshot_reference: AIReadModelSnapshotReference | None,
    historical_snapshot_summary: str,
    timeline_summary_reference: str,
    comparison_summary_reference: str,
    change_history_reference: str,
    historical_query_reference: str,
    historical_comparison_query_reference: str,
) -> str:
    return (
        "AI research context historical summary: "
        f"latest_snapshot={_snapshot_reference_text(latest_snapshot_reference)}; "
        f"historical_snapshot_summary={historical_snapshot_summary}; "
        f"timeline_summary_reference={timeline_summary_reference}; "
        f"comparison_summary_reference={comparison_summary_reference}; "
        f"change_history_reference={change_history_reference}; "
        f"historical_query_reference={historical_query_reference}; "
        f"historical_comparison_query_reference={historical_comparison_query_reference}"
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


def _join_snapshot_references(values: list[AIReadModelSnapshotReference]) -> str:
    if not values:
        return "not available"
    return " | ".join(_snapshot_reference_text(value) for value in values)

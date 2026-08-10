from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_historical_comparison_query import (
    AIResearchContextHistoricalComparisonQuery,
)
from ccass_core.ai_research_context_historical_query import AIResearchContextHistoricalQuery
from ccass_core.ai_research_context_historical_summary import AIResearchContextHistoricalSummary
from ccass_core.ai_research_context_timeline import AIResearchContextTimeline
from ccass_core.ai_research_context_timeline_summary import AIResearchContextTimelineSummary

AI_RESEARCH_CONTEXT_HISTORICAL_DELIVERY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_HISTORICAL_DELIVERY_SURFACE = "ai_research_context_historical_delivery"


class AIResearchContextHistoricalDeliveryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_HISTORICAL_DELIVERY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_HISTORICAL_DELIVERY_SURFACE


class AIResearchContextHistoricalDelivery(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    historical_summary: AIResearchContextHistoricalSummary | None = None
    historical_query: AIResearchContextHistoricalQuery | None = None
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None = None
    timeline: AIResearchContextTimeline | None = None
    timeline_summary: AIResearchContextTimelineSummary | None = None
    timeline_visible: bool = False
    snapshot_reference_visible: bool = False
    comparison_visible: bool = False
    summary_visible: bool = False
    historical_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    summary: str = "AI research context historical delivery is unavailable."
    delivery_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    contract_meta: AIResearchContextHistoricalDeliveryContractMeta = Field(
        default_factory=AIResearchContextHistoricalDeliveryContractMeta
    )


def build_ai_research_context_historical_delivery(
    historical_summary: AIResearchContextHistoricalSummary | None,
    historical_query: AIResearchContextHistoricalQuery | None,
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
    timeline: AIResearchContextTimeline | None,
    timeline_summary: AIResearchContextTimelineSummary | None,
    *,
    surface: str = AI_RESEARCH_CONTEXT_HISTORICAL_DELIVERY_SURFACE,
) -> AIResearchContextHistoricalDelivery:
    available = any(
        [
            historical_summary is not None and historical_summary.available,
            historical_query is not None and historical_query.available,
            historical_comparison_query is not None and historical_comparison_query.available,
            timeline is not None and timeline.available,
            timeline_summary is not None and timeline_summary.available,
        ]
    )
    if not available:
        return AIResearchContextHistoricalDelivery(
            summary="AI research context historical delivery is unavailable.",
            contract_meta=AIResearchContextHistoricalDeliveryContractMeta(surface=surface),
        )

    timeline_visible = timeline is not None and timeline.available
    snapshot_reference_visible = bool(
        (
            historical_query is not None and historical_query.available
        )
        or (
            historical_comparison_query is not None and historical_comparison_query.available
        )
    )
    comparison_visible = historical_comparison_query is not None and historical_comparison_query.available
    summary_visible = historical_summary is not None and historical_summary.available
    historical_state = _historical_state(
        historical_summary=historical_summary,
        historical_query=historical_query,
        historical_comparison_query=historical_comparison_query,
        timeline=timeline,
        timeline_summary=timeline_summary,
    )
    summary = _summary_text(
        historical_summary=historical_summary,
        historical_query=historical_query,
        historical_comparison_query=historical_comparison_query,
        timeline=timeline,
        timeline_summary=timeline_summary,
        timeline_visible=timeline_visible,
        snapshot_reference_visible=snapshot_reference_visible,
        comparison_visible=comparison_visible,
        summary_visible=summary_visible,
    )
    delivery_state = _delivery_state(
        historical_state=historical_state,
        historical_summary=historical_summary,
        historical_query=historical_query,
        historical_comparison_query=historical_comparison_query,
        timeline=timeline,
        timeline_summary=timeline_summary,
    )
    return AIResearchContextHistoricalDelivery(
        available=True,
        historical_summary=historical_summary,
        historical_query=historical_query,
        historical_comparison_query=historical_comparison_query,
        timeline=timeline,
        timeline_summary=timeline_summary,
        timeline_visible=timeline_visible,
        snapshot_reference_visible=snapshot_reference_visible,
        comparison_visible=comparison_visible,
        summary_visible=summary_visible,
        historical_state=historical_state,
        summary=summary,
        delivery_state=delivery_state,
        contract_meta=AIResearchContextHistoricalDeliveryContractMeta(surface=surface),
    )


def build_ai_research_context_historical_delivery_markdown(
    historical_delivery: AIResearchContextHistoricalDelivery | None,
) -> str:
    if historical_delivery is None or not historical_delivery.available:
        return "\n".join(
            [
                "### AI Research Context Historical Delivery",
                "",
                "AI research context historical delivery is unavailable.",
            ]
        )

    rows = [
        ("Timeline visible", "Yes" if historical_delivery.timeline_visible else "No"),
        (
            "Snapshot reference visible",
            "Yes" if historical_delivery.snapshot_reference_visible else "No",
        ),
        ("Comparison visible", "Yes" if historical_delivery.comparison_visible else "No"),
        ("Summary visible", "Yes" if historical_delivery.summary_visible else "No"),
        ("Historical state", historical_delivery.historical_state),
        ("Delivery state", historical_delivery.delivery_state),
        ("Timeline", "available" if historical_delivery.timeline is not None else "not available"),
        (
            "Timeline summary",
            "available" if historical_delivery.timeline_summary is not None else "not available",
        ),
        (
            "Historical summary",
            "available" if historical_delivery.historical_summary is not None else "not available",
        ),
        (
            "Historical query",
            "available" if historical_delivery.historical_query is not None else "not available",
        ),
        (
            "Historical comparison query",
            "available"
            if historical_delivery.historical_comparison_query is not None
            else "not available",
        ),
        (
            "Historical delivery contract",
            f"{historical_delivery.contract_meta.version} / {historical_delivery.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Historical Delivery",
        "",
        f"*{historical_delivery.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _historical_state(
    *,
    historical_summary: AIResearchContextHistoricalSummary | None,
    historical_query: AIResearchContextHistoricalQuery | None,
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
    timeline: AIResearchContextTimeline | None,
    timeline_summary: AIResearchContextTimelineSummary | None,
) -> Literal["available", "partial", "unavailable", "unknown"]:
    states = [
        historical_summary.available if historical_summary is not None else False,
        historical_query.available if historical_query is not None else False,
        historical_comparison_query.available if historical_comparison_query is not None else False,
        timeline.available if timeline is not None else False,
        timeline_summary.available if timeline_summary is not None else False,
    ]
    if all(states):
        return "available"
    if any(states):
        return "partial"
    return "partial"


def _delivery_state(
    *,
    historical_state: Literal["available", "partial", "unavailable", "unknown"],
    historical_summary: AIResearchContextHistoricalSummary | None,
    historical_query: AIResearchContextHistoricalQuery | None,
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
    timeline: AIResearchContextTimeline | None,
    timeline_summary: AIResearchContextTimelineSummary | None,
) -> Literal["available", "partial", "unavailable", "unknown"]:
    if historical_state == "unavailable":
        return "unavailable"
    states = [
        historical_summary.available if historical_summary is not None else False,
        historical_query.available if historical_query is not None else False,
        historical_comparison_query.available if historical_comparison_query is not None else False,
        timeline.available if timeline is not None else False,
        timeline_summary.available if timeline_summary is not None else False,
    ]
    if all(states):
        return "available"
    return "partial"


def _summary_text(
    *,
    historical_summary: AIResearchContextHistoricalSummary | None,
    historical_query: AIResearchContextHistoricalQuery | None,
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None,
    timeline: AIResearchContextTimeline | None,
    timeline_summary: AIResearchContextTimelineSummary | None,
    timeline_visible: bool,
    snapshot_reference_visible: bool,
    comparison_visible: bool,
    summary_visible: bool,
) -> str:
    return (
        "AI research context historical delivery: "
        f"timeline_visible={timeline_visible}; "
        f"snapshot_reference_visible={snapshot_reference_visible}; "
        f"comparison_visible={comparison_visible}; "
        f"summary_visible={summary_visible}; "
        f"historical_summary={(historical_summary.summary if historical_summary is not None else 'not available')}; "
        f"historical_query={(historical_query.summary if historical_query is not None else 'not available')}; "
        f"historical_comparison_query={(historical_comparison_query.summary if historical_comparison_query is not None else 'not available')}; "
        f"timeline={(timeline.summary if timeline is not None else 'not available')}; "
        f"timeline_summary={(timeline_summary.summary if timeline_summary is not None else 'not available')}"
    )

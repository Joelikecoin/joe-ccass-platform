from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_timeline import AIResearchContextTimeline

AI_RESEARCH_CONTEXT_TIMELINE_SUMMARY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_TIMELINE_SUMMARY_SURFACE = "ai_research_context_timeline_summary"


class AIResearchContextTimelineSummaryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_TIMELINE_SUMMARY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_TIMELINE_SUMMARY_SURFACE


class AIResearchContextTimelineSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    snapshot_count_summary: str = "not available"
    timeline_ordering_summary: str = "not available"
    change_history_summary: str = "not available"
    linked_reference_summary: str = "not available"
    timeline_reference: str = "not available"
    summary: str = "AI research context timeline summary is unavailable."
    timeline_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    contract_meta: AIResearchContextTimelineSummaryContractMeta = Field(
        default_factory=AIResearchContextTimelineSummaryContractMeta
    )


def build_ai_research_context_timeline_summary(
    timeline: AIResearchContextTimeline | None,
    *,
    surface: str = AI_RESEARCH_CONTEXT_TIMELINE_SUMMARY_SURFACE,
) -> AIResearchContextTimelineSummary:
    if timeline is None or not timeline.available:
        return AIResearchContextTimelineSummary(
            summary="AI research context timeline summary is unavailable.",
            contract_meta=AIResearchContextTimelineSummaryContractMeta(surface=surface),
        )

    snapshot_count_summary = _snapshot_count_summary(timeline)
    timeline_ordering_summary = _timeline_ordering_summary(timeline)
    change_history_summary = _change_history_summary(timeline)
    linked_reference_summary = _linked_reference_summary(timeline)
    timeline_reference = _timeline_reference(timeline)
    summary = _summary_text(
        snapshot_count_summary=snapshot_count_summary,
        timeline_ordering_summary=timeline_ordering_summary,
        change_history_summary=change_history_summary,
        linked_reference_summary=linked_reference_summary,
        timeline_reference=timeline_reference,
    )
    return AIResearchContextTimelineSummary(
        available=True,
        snapshot_count_summary=snapshot_count_summary,
        timeline_ordering_summary=timeline_ordering_summary,
        change_history_summary=change_history_summary,
        linked_reference_summary=linked_reference_summary,
        timeline_reference=timeline_reference,
        summary=summary,
        timeline_state=timeline.timeline_state,
        contract_meta=AIResearchContextTimelineSummaryContractMeta(surface=surface),
    )


def build_ai_research_context_timeline_summary_markdown(
    timeline_summary: AIResearchContextTimelineSummary | None,
) -> str:
    if timeline_summary is None or not timeline_summary.available:
        return "\n".join(
            [
                "### AI Research Context Timeline Summary",
                "",
                "AI research context timeline summary is unavailable.",
            ]
        )

    rows = [
        ("Snapshot count summary", timeline_summary.snapshot_count_summary),
        ("Timeline ordering summary", timeline_summary.timeline_ordering_summary),
        ("Change history summary", timeline_summary.change_history_summary),
        ("Linked reference summary", timeline_summary.linked_reference_summary),
        ("Timeline reference", timeline_summary.timeline_reference),
        ("Timeline state", timeline_summary.timeline_state),
        (
            "Timeline summary contract",
            f"{timeline_summary.contract_meta.version} / {timeline_summary.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Timeline Summary",
        "",
        f"*{timeline_summary.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _snapshot_count_summary(timeline: AIResearchContextTimeline) -> str:
    snapshot_count = len(timeline.historical_snapshot_metadata)
    return f"{snapshot_count} snapshot(s)"


def _timeline_ordering_summary(timeline: AIResearchContextTimeline) -> str:
    if not timeline.snapshot_ordering:
        return "not available"
    return " | ".join(timeline.snapshot_ordering)


def _change_history_summary(timeline: AIResearchContextTimeline) -> str:
    if not timeline.timeline_items:
        return "not available"
    return " | ".join(
        [
            f"{item.order}:{item.role}:{item.change_summary_reference}"
            for item in timeline.timeline_items
        ]
    )


def _linked_reference_summary(timeline: AIResearchContextTimeline) -> str:
    references = [
        *(timeline.linked_comparison_references or []),
        *(timeline.linked_change_summary_references or []),
        timeline.audit_trail_reference,
        timeline.provenance_reference,
    ]
    references = [reference for reference in references if reference and reference != "not available"]
    if not references:
        return "not available"
    return " | ".join(dict.fromkeys(references))


def _timeline_reference(timeline: AIResearchContextTimeline) -> str:
    return f"{timeline.contract_meta.version} / {timeline.contract_meta.surface}"


def _summary_text(
    *,
    snapshot_count_summary: str,
    timeline_ordering_summary: str,
    change_history_summary: str,
    linked_reference_summary: str,
    timeline_reference: str,
) -> str:
    return (
        "AI research context timeline summary: "
        f"snapshot_count={snapshot_count_summary}; "
        f"timeline_ordering={timeline_ordering_summary}; "
        f"change_history={change_history_summary}; "
        f"linked_references={linked_reference_summary}; "
        f"timeline_reference={timeline_reference}"
    )

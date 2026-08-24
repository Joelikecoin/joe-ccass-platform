from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_snapshot import (
    AIResearchContextConsumerGovernanceSnapshot,
)
from ccass_core.ai_research_context_consumer_governance_status import (
    AIResearchContextConsumerGovernanceStatus,
)
from ccass_core.ai_research_context_consumer_governance_timeline import (
    AIResearchContextConsumerGovernanceTimeline,
)
from ccass_core.ai_research_context_consumer_governance_timeline_validation import (
    AIResearchContextConsumerGovernanceTimelineValidation,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SUMMARY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SUMMARY_SURFACE = (
    "ai_research_context_consumer_governance_timeline_summary"
)


class AIResearchContextConsumerGovernanceTimelineSummaryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SUMMARY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SUMMARY_SURFACE


class AIResearchContextConsumerGovernanceTimelineSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_summary_state: Literal["complete", "partial", "unavailable", "unknown"] = "unknown"
    governance_timeline_summary_visible: bool = False
    governance_timeline_summary_reference: str = "not available"
    governance_timeline_reference: str = "not available"
    governance_timeline_validation_reference: str = "not available"
    governance_snapshot_reference: str = "not available"
    governance_status_reference: str = "not available"
    summary: str = "AI research context consumer governance timeline summary is unavailable."
    governance_timeline_summary: str = (
        "AI research context consumer governance timeline summary is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceTimelineSummaryContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSummaryContractMeta
    )


def build_ai_research_context_consumer_governance_timeline_summary(
    *,
    available: bool,
    governance_timeline: AIResearchContextConsumerGovernanceTimeline | None,
    governance_timeline_validation: AIResearchContextConsumerGovernanceTimelineValidation | None,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_status: AIResearchContextConsumerGovernanceStatus | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SUMMARY_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSummary:
    if not available:
        return AIResearchContextConsumerGovernanceTimelineSummary(
            summary="AI research context consumer governance timeline summary is unavailable.",
            governance_timeline_summary_state="unavailable",
            governance_timeline_summary_visible=False,
            governance_timeline_summary_reference="not available",
            governance_timeline_reference=_timeline_reference(governance_timeline),
            governance_timeline_validation_reference=_timeline_validation_reference(
                governance_timeline_validation
            ),
            governance_snapshot_reference=_snapshot_reference(governance_snapshot),
            governance_status_reference=_status_reference(governance_status),
            contract_meta=AIResearchContextConsumerGovernanceTimelineSummaryContractMeta(
                surface=surface
            ),
        )

    governance_timeline_summary_state = _summary_state(
        governance_timeline=governance_timeline,
        governance_timeline_validation=governance_timeline_validation,
        governance_snapshot=governance_snapshot,
        governance_status=governance_status,
    )
    governance_timeline_summary_visible = governance_timeline_summary_state in {
        "complete",
        "partial",
    }
    governance_timeline_reference = _timeline_reference(governance_timeline)
    governance_timeline_validation_reference = _timeline_validation_reference(
        governance_timeline_validation
    )
    governance_snapshot_reference = _snapshot_reference(governance_snapshot)
    governance_status_reference = _status_reference(governance_status)
    governance_timeline_summary_reference = _summary_reference(
        governance_timeline_summary_state=governance_timeline_summary_state,
        governance_timeline_reference=governance_timeline_reference,
        governance_timeline_validation_reference=governance_timeline_validation_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_status_reference=governance_status_reference,
    )
    summary = _summary_text(
        governance_timeline_summary_state=governance_timeline_summary_state,
        governance_timeline_summary_visible=governance_timeline_summary_visible,
        governance_timeline_summary_reference=governance_timeline_summary_reference,
        governance_timeline_reference=governance_timeline_reference,
        governance_timeline_validation_reference=governance_timeline_validation_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_status_reference=governance_status_reference,
    )
    return AIResearchContextConsumerGovernanceTimelineSummary(
        available=True,
        summary=summary,
        governance_timeline_summary_state=governance_timeline_summary_state,
        governance_timeline_summary_visible=governance_timeline_summary_visible,
        governance_timeline_summary_reference=governance_timeline_summary_reference,
        governance_timeline_reference=governance_timeline_reference,
        governance_timeline_validation_reference=governance_timeline_validation_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_status_reference=governance_status_reference,
        governance_timeline_summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSummaryContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_summary_markdown(
    governance_timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary | None,
) -> str:
    if governance_timeline_summary is None or not governance_timeline_summary.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Summary",
                "",
                "AI research context consumer governance timeline summary is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline summary state",
            governance_timeline_summary.governance_timeline_summary_state,
        ),
        (
            "Governance timeline summary visible",
            "Yes" if governance_timeline_summary.governance_timeline_summary_visible else "No",
        ),
        (
            "Governance timeline summary reference",
            governance_timeline_summary.governance_timeline_summary_reference,
        ),
        (
            "Governance timeline reference",
            governance_timeline_summary.governance_timeline_reference,
        ),
        (
            "Governance timeline validation reference",
            governance_timeline_summary.governance_timeline_validation_reference,
        ),
        (
            "Governance snapshot reference",
            governance_timeline_summary.governance_snapshot_reference,
        ),
        (
            "Governance status reference",
            governance_timeline_summary.governance_status_reference,
        ),
        (
            "Governance timeline summary contract",
            f"{governance_timeline_summary.contract_meta.version} / {governance_timeline_summary.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Summary",
        "",
        f"*{governance_timeline_summary.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _summary_state(
    *,
    governance_timeline: AIResearchContextConsumerGovernanceTimeline | None,
    governance_timeline_validation: AIResearchContextConsumerGovernanceTimelineValidation | None,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_status: AIResearchContextConsumerGovernanceStatus | None,
) -> Literal["complete", "partial", "unavailable", "unknown"]:
    if governance_timeline is None or not governance_timeline.available:
        return "unavailable"
    if governance_timeline_validation is not None and governance_timeline_validation.available:
        if governance_timeline_validation.validation_state == "consistent":
            return "complete"
        if governance_timeline_validation.validation_state in {"partial", "inconsistent"}:
            return "partial"
    if (
        governance_snapshot is not None
        and governance_snapshot.available
        and governance_status is not None
        and governance_status.available
    ):
        return "partial"
    return "unknown"


def _summary_reference(
    *,
    governance_timeline_summary_state: str,
    governance_timeline_reference: str,
    governance_timeline_validation_reference: str,
    governance_snapshot_reference: str,
    governance_status_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline summary: "
        f"state={governance_timeline_summary_state}; "
        "scope=timeline_summary"
    )


def _timeline_reference(timeline: AIResearchContextConsumerGovernanceTimeline | None) -> str:
    if timeline is None or not timeline.available:
        return "not available"
    return timeline.governance_timeline_reference


def _timeline_validation_reference(
    timeline_validation: AIResearchContextConsumerGovernanceTimelineValidation | None,
) -> str:
    if timeline_validation is None or not timeline_validation.available:
        return "not available"
    return timeline_validation.validation_reference


def _snapshot_reference(snapshot: AIResearchContextConsumerGovernanceSnapshot | None) -> str:
    if snapshot is None or not snapshot.available:
        return "not available"
    return snapshot.governance_snapshot_reference


def _status_reference(status: AIResearchContextConsumerGovernanceStatus | None) -> str:
    if status is None or not status.available:
        return "not available"
    return status.governance_reference


def _summary_text(
    *,
    governance_timeline_summary_state: str,
    governance_timeline_summary_visible: bool,
    governance_timeline_summary_reference: str,
    governance_timeline_reference: str,
    governance_timeline_validation_reference: str,
    governance_snapshot_reference: str,
    governance_status_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline summary: "
        f"state={governance_timeline_summary_state}; "
        f"visible={'yes' if governance_timeline_summary_visible else 'no'}; "
        "scope=timeline_summary"
    )

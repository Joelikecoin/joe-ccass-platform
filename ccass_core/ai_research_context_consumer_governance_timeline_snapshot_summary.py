from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_snapshot import (
    AIResearchContextConsumerGovernanceSnapshot,
)
from ccass_core.ai_research_context_consumer_governance_snapshot_validation import (
    AIResearchContextConsumerGovernanceSnapshotValidation,
)
from ccass_core.ai_research_context_consumer_governance_timeline import (
    AIResearchContextConsumerGovernanceTimeline,
)
from ccass_core.ai_research_context_consumer_governance_timeline_summary import (
    AIResearchContextConsumerGovernanceTimelineSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot import (
    AIResearchContextConsumerGovernanceTimelineSnapshot,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotValidation,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SUMMARY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SUMMARY_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot_summary"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotSummaryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SUMMARY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SUMMARY_SURFACE


class AIResearchContextConsumerGovernanceTimelineSnapshotSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_summary_state: Literal["complete", "partial", "unavailable", "unknown"] = "unknown"
    governance_timeline_snapshot_summary_visible: bool = False
    governance_timeline_snapshot_summary_reference: str = "not available"
    governance_timeline_snapshot_reference: str = "not available"
    governance_timeline_snapshot_visible: bool = False
    governance_timeline_snapshot_validation_reference: str = "not available"
    governance_timeline_snapshot_validation_visible: bool = False
    governance_timeline_summary_reference: str = "not available"
    governance_snapshot_reference: str = "not available"
    governance_snapshot_validation_reference: str = "not available"
    governance_continuity_reference: str = "not available"
    summary: str = (
        "AI research context consumer governance timeline snapshot summary is unavailable."
    )
    governance_timeline_snapshot_summary: str = (
        "AI research context consumer governance timeline snapshot summary is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceTimelineSnapshotSummaryContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotSummaryContractMeta
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_summary(
    *,
    available: bool,
    governance_timeline_snapshot: AIResearchContextConsumerGovernanceTimelineSnapshot | None,
    governance_timeline_snapshot_validation: AIResearchContextConsumerGovernanceTimelineSnapshotValidation | None,
    governance_timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary | None,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SUMMARY_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshotSummary:
    snapshot_available = bool(governance_timeline_snapshot is not None and governance_timeline_snapshot.available)
    snapshot_validation_available = bool(
        governance_timeline_snapshot_validation is not None
        and governance_timeline_snapshot_validation.available
    )
    timeline_summary_available = bool(
        governance_timeline_summary is not None and governance_timeline_summary.available
    )
    snapshot_reference = _snapshot_reference(governance_timeline_snapshot)
    snapshot_visible = bool(
        governance_timeline_snapshot is not None and governance_timeline_snapshot.governance_timeline_snapshot_visible
    )
    snapshot_validation_reference = _snapshot_validation_reference(
        governance_timeline_snapshot_validation
    )
    snapshot_validation_visible = bool(
        governance_timeline_snapshot_validation is not None
        and governance_timeline_snapshot_validation.governance_timeline_snapshot_visible
    )
    timeline_summary_reference = _timeline_summary_reference(governance_timeline_summary)
    governance_snapshot_reference = _governance_snapshot_reference(governance_snapshot)
    governance_snapshot_validation_reference = _governance_snapshot_validation_reference(
        governance_snapshot_validation
    )
    continuity_reference = _continuity_reference(governance_snapshot)

    if not available:
        return AIResearchContextConsumerGovernanceTimelineSnapshotSummary(
            governance_timeline_snapshot_summary_state="unavailable",
            governance_timeline_snapshot_summary_visible=False,
            governance_timeline_snapshot_summary_reference="not available",
            governance_timeline_snapshot_reference=snapshot_reference,
            governance_timeline_snapshot_visible=snapshot_visible,
            governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
            governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
            governance_timeline_summary_reference=timeline_summary_reference,
            governance_snapshot_reference=governance_snapshot_reference,
            governance_snapshot_validation_reference=governance_snapshot_validation_reference,
            governance_continuity_reference=continuity_reference,
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotSummaryContractMeta(
                surface=surface
            ),
        )

    governance_timeline_snapshot_summary_state = _summary_state(
        snapshot_available=snapshot_available,
        snapshot_validation_available=snapshot_validation_available,
        timeline_summary_available=timeline_summary_available,
        governance_timeline_snapshot=governance_timeline_snapshot,
        governance_timeline_snapshot_validation=governance_timeline_snapshot_validation,
        governance_timeline_summary=governance_timeline_summary,
        governance_snapshot=governance_snapshot,
        governance_snapshot_validation=governance_snapshot_validation,
    )
    governance_timeline_snapshot_summary_visible = governance_timeline_snapshot_summary_state in {
        "complete",
        "partial",
    }
    governance_timeline_snapshot_summary_reference = _summary_reference(
        governance_timeline_snapshot_summary_state=governance_timeline_snapshot_summary_state,
        governance_timeline_snapshot_reference=snapshot_reference,
        governance_timeline_snapshot_visible=snapshot_visible,
        governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
        governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
        governance_timeline_summary_reference=timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_continuity_reference=continuity_reference,
    )
    summary = _summary_text(
        governance_timeline_snapshot_summary_state=governance_timeline_snapshot_summary_state,
        governance_timeline_snapshot_summary_visible=governance_timeline_snapshot_summary_visible,
        governance_timeline_snapshot_summary_reference=governance_timeline_snapshot_summary_reference,
        governance_timeline_snapshot_reference=snapshot_reference,
        governance_timeline_snapshot_visible=snapshot_visible,
        governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
        governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
        governance_timeline_summary_reference=timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_continuity_reference=continuity_reference,
    )
    return AIResearchContextConsumerGovernanceTimelineSnapshotSummary(
        available=True,
        governance_timeline_snapshot_summary_state=governance_timeline_snapshot_summary_state,
        governance_timeline_snapshot_summary_visible=governance_timeline_snapshot_summary_visible,
        governance_timeline_snapshot_summary_reference=governance_timeline_snapshot_summary_reference,
        governance_timeline_snapshot_reference=snapshot_reference,
        governance_timeline_snapshot_visible=snapshot_visible,
        governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
        governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
        governance_timeline_summary_reference=timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_continuity_reference=continuity_reference,
        summary=summary,
        governance_timeline_snapshot_summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotSummaryContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_summary_markdown(
    governance_timeline_snapshot_summary: AIResearchContextConsumerGovernanceTimelineSnapshotSummary | None,
) -> str:
    if (
        governance_timeline_snapshot_summary is None
        or not governance_timeline_snapshot_summary.available
    ):
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot Summary",
                "",
                "AI research context consumer governance timeline snapshot summary is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline snapshot summary state",
            governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_state,
        ),
        (
            "Governance timeline snapshot summary visible",
            "Yes"
            if governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary reference",
            governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_reference,
        ),
        (
            "Governance timeline snapshot reference",
            governance_timeline_snapshot_summary.governance_timeline_snapshot_reference,
        ),
        (
            "Governance timeline snapshot visible",
            "Yes" if governance_timeline_snapshot_summary.governance_timeline_snapshot_visible else "No",
        ),
        (
            "Governance timeline snapshot validation reference",
            governance_timeline_snapshot_summary.governance_timeline_snapshot_validation_reference,
        ),
        (
            "Governance timeline snapshot validation visible",
            "Yes"
            if governance_timeline_snapshot_summary.governance_timeline_snapshot_validation_visible
            else "No",
        ),
        (
            "Governance timeline summary reference",
            governance_timeline_snapshot_summary.governance_timeline_summary_reference,
        ),
        (
            "Governance snapshot reference",
            governance_timeline_snapshot_summary.governance_snapshot_reference,
        ),
        (
            "Governance snapshot validation reference",
            governance_timeline_snapshot_summary.governance_snapshot_validation_reference,
        ),
        (
            "Governance continuity reference",
            governance_timeline_snapshot_summary.governance_continuity_reference,
        ),
        (
            "Governance timeline snapshot summary contract",
            f"{governance_timeline_snapshot_summary.contract_meta.version} / {governance_timeline_snapshot_summary.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot Summary",
        "",
        f"*{governance_timeline_snapshot_summary.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _summary_state(
    *,
    snapshot_available: bool,
    snapshot_validation_available: bool,
    timeline_summary_available: bool,
    governance_timeline_snapshot: AIResearchContextConsumerGovernanceTimelineSnapshot | None,
    governance_timeline_snapshot_validation: AIResearchContextConsumerGovernanceTimelineSnapshotValidation | None,
    governance_timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary | None,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
) -> Literal["complete", "partial", "unavailable", "unknown"]:
    if not snapshot_available:
        return "unavailable"
    if (
        snapshot_validation_available
        and timeline_summary_available
        and governance_timeline_snapshot_validation is not None
        and governance_timeline_snapshot_validation.validation_state == "consistent"
        and governance_timeline_summary is not None
        and governance_timeline_summary.available
        and governance_snapshot is not None
        and governance_snapshot.available
        and governance_snapshot_validation is not None
        and governance_snapshot_validation.available
        and governance_snapshot_validation.validation_state == "consistent"
    ):
        return "complete"
    if snapshot_validation_available or timeline_summary_available or (
        governance_snapshot is not None and governance_snapshot.available
    ):
        return "partial"
    if governance_timeline_snapshot is not None and governance_timeline_snapshot.available:
        return "unknown"
    return "unknown"


def _summary_reference(
    *,
    governance_timeline_snapshot_summary_state: str,
    governance_timeline_snapshot_reference: str,
    governance_timeline_snapshot_visible: bool,
    governance_timeline_snapshot_validation_reference: str,
    governance_timeline_snapshot_validation_visible: bool,
    governance_timeline_summary_reference: str,
    governance_snapshot_reference: str,
    governance_snapshot_validation_reference: str,
    governance_continuity_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot summary: "
        f"state={governance_timeline_snapshot_summary_state}; "
        f"snapshot={governance_timeline_snapshot_reference}; "
        f"snapshot_visible={'yes' if governance_timeline_snapshot_visible else 'no'}; "
        f"snapshot_validation={governance_timeline_snapshot_validation_reference}; "
        f"snapshot_validation_visible={'yes' if governance_timeline_snapshot_validation_visible else 'no'}; "
        f"timeline_summary={governance_timeline_summary_reference}; "
        f"snapshot_reference={governance_snapshot_reference}; "
        f"snapshot_validation_reference={governance_snapshot_validation_reference}; "
        f"continuity={governance_continuity_reference}"
    )


def _summary_text(
    *,
    governance_timeline_snapshot_summary_state: str,
    governance_timeline_snapshot_summary_visible: bool,
    governance_timeline_snapshot_summary_reference: str,
    governance_timeline_snapshot_reference: str,
    governance_timeline_snapshot_visible: bool,
    governance_timeline_snapshot_validation_reference: str,
    governance_timeline_snapshot_validation_visible: bool,
    governance_timeline_summary_reference: str,
    governance_snapshot_reference: str,
    governance_snapshot_validation_reference: str,
    governance_continuity_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot summary: "
        f"state={governance_timeline_snapshot_summary_state}; "
        f"visible={'yes' if governance_timeline_snapshot_summary_visible else 'no'}; "
        f"reference={governance_timeline_snapshot_summary_reference}; "
        f"snapshot={governance_timeline_snapshot_reference}; "
        f"snapshot_visible={'yes' if governance_timeline_snapshot_visible else 'no'}; "
        f"snapshot_validation={governance_timeline_snapshot_validation_reference}; "
        f"snapshot_validation_visible={'yes' if governance_timeline_snapshot_validation_visible else 'no'}; "
        f"timeline_summary={governance_timeline_summary_reference}; "
        f"snapshot_reference={governance_snapshot_reference}; "
        f"snapshot_validation_reference={governance_snapshot_validation_reference}; "
        f"continuity={governance_continuity_reference}"
    )


def _snapshot_reference(
    snapshot: AIResearchContextConsumerGovernanceTimelineSnapshot | None,
) -> str:
    if snapshot is None or not snapshot.available:
        return "not available"
    return snapshot.governance_timeline_snapshot_reference


def _snapshot_validation_reference(
    snapshot_validation: AIResearchContextConsumerGovernanceTimelineSnapshotValidation | None,
) -> str:
    if snapshot_validation is None or not snapshot_validation.available:
        return "not available"
    return snapshot_validation.validation_reference


def _timeline_summary_reference(
    timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary | None,
) -> str:
    if timeline_summary is None or not timeline_summary.available:
        return "not available"
    return timeline_summary.governance_timeline_summary_reference


def _governance_snapshot_reference(
    snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
) -> str:
    if snapshot is None or not snapshot.available:
        return "not available"
    return snapshot.governance_snapshot_reference


def _governance_snapshot_validation_reference(
    snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
) -> str:
    if snapshot_validation is None or not snapshot_validation.available:
        return "not available"
    return snapshot_validation.validation_reference


def _continuity_reference(snapshot: AIResearchContextConsumerGovernanceSnapshot | None) -> str:
    if snapshot is None or not snapshot.available:
        return "not available"
    return snapshot.governance_continuity_reference

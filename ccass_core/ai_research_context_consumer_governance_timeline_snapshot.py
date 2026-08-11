from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_snapshot import (
    AIResearchContextConsumerGovernanceSnapshot,
)
from ccass_core.ai_research_context_consumer_governance_snapshot_validation import (
    AIResearchContextConsumerGovernanceSnapshotValidation,
)
from ccass_core.ai_research_context_consumer_governance_summary import (
    AIResearchContextConsumerGovernanceSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline import (
    AIResearchContextConsumerGovernanceTimeline,
)
from ccass_core.ai_research_context_consumer_governance_timeline_summary import (
    AIResearchContextConsumerGovernanceTimelineSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline_validation import (
    AIResearchContextConsumerGovernanceTimelineValidation,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SURFACE


class AIResearchContextConsumerGovernanceTimelineSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_state: Literal["complete", "partial", "unavailable", "unknown"] = "unknown"
    governance_timeline_snapshot_visible: bool = False
    governance_timeline_snapshot_reference: str = "not available"
    governance_timeline_reference: str = "not available"
    governance_timeline_validation_reference: str = "not available"
    governance_timeline_summary_reference: str = "not available"
    governance_snapshot_reference: str = "not available"
    governance_snapshot_validation_reference: str = "not available"
    governance_continuity_reference: str = "not available"
    summary: str = (
        "AI research context consumer governance timeline snapshot is unavailable."
    )
    governance_timeline_snapshot_summary: str = (
        "AI research context consumer governance timeline snapshot is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceTimelineSnapshotContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotContractMeta
    )


def build_ai_research_context_consumer_governance_timeline_snapshot(
    *,
    available: bool,
    governance_timeline: AIResearchContextConsumerGovernanceTimeline | None,
    governance_timeline_validation: AIResearchContextConsumerGovernanceTimelineValidation | None,
    governance_timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary | None,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshot:
    timeline_available = bool(governance_timeline is not None and governance_timeline.available)
    timeline_validation_available = bool(
        governance_timeline_validation is not None and governance_timeline_validation.available
    )
    timeline_summary_available = bool(
        governance_timeline_summary is not None and governance_timeline_summary.available
    )
    snapshot_available = bool(governance_snapshot is not None and governance_snapshot.available)
    snapshot_validation_available = bool(
        governance_snapshot_validation is not None and governance_snapshot_validation.available
    )

    timeline_reference = _timeline_reference(governance_timeline)
    timeline_validation_reference = _timeline_validation_reference(governance_timeline_validation)
    timeline_summary_reference = _timeline_summary_reference(governance_timeline_summary)
    snapshot_reference = _snapshot_reference(governance_snapshot)
    snapshot_validation_reference = _snapshot_validation_reference(governance_snapshot_validation)
    continuity_reference = _continuity_reference(governance_snapshot)

    if not available:
        return AIResearchContextConsumerGovernanceTimelineSnapshot(
            governance_timeline_snapshot_state="unavailable",
            governance_timeline_snapshot_visible=False,
            governance_timeline_snapshot_reference="not available",
            governance_timeline_reference=timeline_reference,
            governance_timeline_validation_reference=timeline_validation_reference,
            governance_timeline_summary_reference=timeline_summary_reference,
            governance_snapshot_reference=snapshot_reference,
            governance_snapshot_validation_reference=snapshot_validation_reference,
            governance_continuity_reference=continuity_reference,
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotContractMeta(
                surface=surface
            ),
        )

    governance_timeline_snapshot_state = _snapshot_state(
        timeline_available=timeline_available,
        timeline_validation_available=timeline_validation_available,
        timeline_summary_available=timeline_summary_available,
        snapshot_available=snapshot_available,
        snapshot_validation_available=snapshot_validation_available,
        governance_timeline=governance_timeline,
        governance_timeline_validation=governance_timeline_validation,
        governance_snapshot=governance_snapshot,
        governance_snapshot_validation=governance_snapshot_validation,
    )
    governance_timeline_snapshot_visible = governance_timeline_snapshot_state in {
        "complete",
        "partial",
    }
    governance_timeline_snapshot_reference = _snapshot_reference_text(
        governance_timeline_snapshot_state=governance_timeline_snapshot_state,
        governance_timeline_reference=timeline_reference,
        governance_timeline_validation_reference=timeline_validation_reference,
        governance_timeline_summary_reference=timeline_summary_reference,
        governance_snapshot_reference=snapshot_reference,
        governance_snapshot_validation_reference=snapshot_validation_reference,
        governance_continuity_reference=continuity_reference,
    )
    governance_timeline_snapshot_summary = _summary_text(
        governance_timeline_snapshot_state=governance_timeline_snapshot_state,
        governance_timeline_snapshot_visible=governance_timeline_snapshot_visible,
        governance_timeline_snapshot_reference=governance_timeline_snapshot_reference,
        governance_timeline_reference=timeline_reference,
        governance_timeline_validation_reference=timeline_validation_reference,
        governance_timeline_summary_reference=timeline_summary_reference,
        governance_snapshot_reference=snapshot_reference,
        governance_snapshot_validation_reference=snapshot_validation_reference,
        governance_continuity_reference=continuity_reference,
    )
    return AIResearchContextConsumerGovernanceTimelineSnapshot(
        available=True,
        governance_timeline_snapshot_state=governance_timeline_snapshot_state,
        governance_timeline_snapshot_visible=governance_timeline_snapshot_visible,
        governance_timeline_snapshot_reference=governance_timeline_snapshot_reference,
        governance_timeline_reference=timeline_reference,
        governance_timeline_validation_reference=timeline_validation_reference,
        governance_timeline_summary_reference=timeline_summary_reference,
        governance_snapshot_reference=snapshot_reference,
        governance_snapshot_validation_reference=snapshot_validation_reference,
        governance_continuity_reference=continuity_reference,
        summary=governance_timeline_snapshot_summary,
        governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotContractMeta(surface=surface),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_markdown(
    governance_timeline_snapshot: AIResearchContextConsumerGovernanceTimelineSnapshot | None,
) -> str:
    if governance_timeline_snapshot is None or not governance_timeline_snapshot.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot",
                "",
                "AI research context consumer governance timeline snapshot is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline snapshot state",
            governance_timeline_snapshot.governance_timeline_snapshot_state,
        ),
        (
            "Governance timeline snapshot visible",
            "Yes" if governance_timeline_snapshot.governance_timeline_snapshot_visible else "No",
        ),
        (
            "Governance timeline snapshot reference",
            governance_timeline_snapshot.governance_timeline_snapshot_reference,
        ),
        ("Governance timeline reference", governance_timeline_snapshot.governance_timeline_reference),
        (
            "Governance timeline validation reference",
            governance_timeline_snapshot.governance_timeline_validation_reference,
        ),
        (
            "Governance timeline summary reference",
            governance_timeline_snapshot.governance_timeline_summary_reference,
        ),
        (
            "Governance snapshot reference",
            governance_timeline_snapshot.governance_snapshot_reference,
        ),
        (
            "Governance snapshot validation reference",
            governance_timeline_snapshot.governance_snapshot_validation_reference,
        ),
        (
            "Governance continuity reference",
            governance_timeline_snapshot.governance_continuity_reference,
        ),
        (
            "Governance timeline snapshot contract",
            f"{governance_timeline_snapshot.contract_meta.version} / {governance_timeline_snapshot.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot",
        "",
        f"*{governance_timeline_snapshot.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _snapshot_state(
    *,
    timeline_available: bool,
    timeline_validation_available: bool,
    timeline_summary_available: bool,
    snapshot_available: bool,
    snapshot_validation_available: bool,
    governance_timeline: AIResearchContextConsumerGovernanceTimeline | None,
    governance_timeline_validation: AIResearchContextConsumerGovernanceTimelineValidation | None,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
) -> Literal["complete", "partial", "unavailable", "unknown"]:
    if not timeline_available:
        return "unavailable"
    if (
        timeline_validation_available
        and snapshot_validation_available
        and governance_timeline_validation is not None
        and governance_snapshot_validation is not None
        and governance_timeline_validation.validation_state == "consistent"
        and governance_snapshot_validation.validation_state == "consistent"
        and snapshot_available
        and timeline_summary_available
    ):
        return "complete"
    if snapshot_available or timeline_summary_available or timeline_validation_available:
        return "partial"
    if governance_timeline is not None and governance_timeline.available:
        return "unknown"
    if governance_snapshot is not None and governance_snapshot.available:
        return "partial"
    return "unknown"


def _snapshot_reference_text(
    *,
    governance_timeline_snapshot_state: str,
    governance_timeline_reference: str,
    governance_timeline_validation_reference: str,
    governance_timeline_summary_reference: str,
    governance_snapshot_reference: str,
    governance_snapshot_validation_reference: str,
    governance_continuity_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot: "
        f"state={governance_timeline_snapshot_state}; "
        f"timeline={governance_timeline_reference}; "
        f"timeline_validation={governance_timeline_validation_reference}; "
        f"timeline_summary={governance_timeline_summary_reference}; "
        f"snapshot={governance_snapshot_reference}; "
        f"snapshot_validation={governance_snapshot_validation_reference}; "
        f"continuity={governance_continuity_reference}"
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


def _timeline_summary_reference(
    timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary | None,
) -> str:
    if timeline_summary is None or not timeline_summary.available:
        return "not available"
    return timeline_summary.governance_timeline_summary_reference


def _snapshot_reference(snapshot: AIResearchContextConsumerGovernanceSnapshot | None) -> str:
    if snapshot is None or not snapshot.available:
        return "not available"
    return snapshot.governance_snapshot_reference


def _snapshot_validation_reference(
    snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
) -> str:
    if snapshot_validation is None or not snapshot_validation.available:
        return "not available"
    return snapshot_validation.validation_reference


def _continuity_reference(snapshot: AIResearchContextConsumerGovernanceSnapshot | None) -> str:
    if snapshot is None or not snapshot.available:
        return "not available"
    return snapshot.governance_continuity_reference


def _summary_text(
    *,
    governance_timeline_snapshot_state: str,
    governance_timeline_snapshot_visible: bool,
    governance_timeline_snapshot_reference: str,
    governance_timeline_reference: str,
    governance_timeline_validation_reference: str,
    governance_timeline_summary_reference: str,
    governance_snapshot_reference: str,
    governance_snapshot_validation_reference: str,
    governance_continuity_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot: "
        f"state={governance_timeline_snapshot_state}; "
        f"visible={'yes' if governance_timeline_snapshot_visible else 'no'}; "
        f"reference={governance_timeline_snapshot_reference}; "
        f"timeline={governance_timeline_reference}; "
        f"timeline_validation={governance_timeline_validation_reference}; "
        f"timeline_summary={governance_timeline_summary_reference}; "
        f"snapshot={governance_snapshot_reference}; "
        f"snapshot_validation={governance_snapshot_validation_reference}; "
        f"continuity={governance_continuity_reference}"
    )

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_snapshot import (
    AIResearchContextConsumerGovernanceSnapshot,
)
from ccass_core.ai_research_context_consumer_governance_snapshot_validation import (
    AIResearchContextConsumerGovernanceSnapshotValidation,
)
from ccass_core.ai_research_context_consumer_governance_status import (
    AIResearchContextConsumerGovernanceStatus,
)
from ccass_core.ai_research_context_consumer_governance_status_validation import (
    AIResearchContextConsumerGovernanceStatusValidation,
)
from ccass_core.ai_research_context_consumer_governance_summary import (
    AIResearchContextConsumerGovernanceSummary,
)
from ccass_core.ai_research_context_consumer_health import (
    AIResearchContextConsumerHealthIndicator,
)
from ccass_core.ai_research_context_consumer_readiness import (
    AIResearchContextConsumerReadinessStatus,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SURFACE = (
    "ai_research_context_consumer_governance_timeline"
)


class AIResearchContextConsumerGovernanceTimelineContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SURFACE


class AIResearchContextConsumerGovernanceTimeline(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_state: Literal["complete", "partial", "unavailable", "unknown"] = "unknown"
    governance_timeline_visible: bool = False
    governance_continuity_visible: bool = False
    governance_timeline_reference: str = "not available"
    governance_state_sequence_reference: str = "not available"
    governance_continuity_reference: str = "not available"
    governance_summary_reference: str = "not available"
    governance_status_reference: str = "not available"
    governance_status_validation_reference: str = "not available"
    governance_snapshot_validation_reference: str = "not available"
    governance_snapshot_reference: str = "not available"
    readiness_reference: str = "not available"
    health_reference: str = "not available"
    version_reference: str = "not available"
    compatibility_reference: str = "not available"
    capability_reference: str = "not available"
    consumer_ready: bool = False
    timeline_continuity_consistent: bool = False
    readiness_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    health_status: Literal["healthy", "partial", "unavailable", "unknown"] = "unknown"
    summary: str = "AI research context consumer governance timeline is unavailable."
    contract_meta: AIResearchContextConsumerGovernanceTimelineContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineContractMeta
    )


def build_ai_research_context_consumer_governance_timeline(
    *,
    available: bool,
    governance_summary: AIResearchContextConsumerGovernanceSummary | None,
    governance_status: AIResearchContextConsumerGovernanceStatus | None,
    governance_status_validation: AIResearchContextConsumerGovernanceStatusValidation | None,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    readiness_status: AIResearchContextConsumerReadinessStatus | None,
    health_indicator: AIResearchContextConsumerHealthIndicator | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SURFACE,
) -> AIResearchContextConsumerGovernanceTimeline:
    governance_summary_available = bool(
        governance_summary is not None and governance_summary.available
    )
    governance_status_available = bool(
        governance_status is not None and governance_status.available
    )
    governance_status_validation_available = bool(
        governance_status_validation is not None and governance_status_validation.available
    )
    governance_snapshot_available = bool(
        governance_snapshot is not None and governance_snapshot.available
    )
    governance_snapshot_validation_available = bool(
        governance_snapshot_validation is not None and governance_snapshot_validation.available
    )
    readiness_reference = (
        readiness_status.readiness_reference if readiness_status is not None else "not available"
    )
    health_reference = (
        health_indicator.health_reference if health_indicator is not None else "not available"
    )
    consumer_ready = bool(readiness_status.consumer_ready if readiness_status is not None else False)
    readiness_state = (
        readiness_status.readiness_status if readiness_status is not None else "unknown"
    )
    health_state = health_indicator.health_status if health_indicator is not None else "unknown"

    governance_summary_reference = (
        governance_summary.summary if governance_summary_available else "not available"
    )
    governance_status_reference = (
        governance_status.governance_reference if governance_status_available else "not available"
    )
    governance_status_validation_reference = (
        governance_status_validation.validation_reference
        if governance_status_validation_available
        else "not available"
    )
    governance_snapshot_validation_reference = (
        governance_snapshot_validation.validation_reference
        if governance_snapshot_validation_available
        else "not available"
    )
    governance_snapshot_reference = (
        governance_snapshot.governance_snapshot_reference if governance_snapshot_available else "not available"
    )
    continuity_reference = (
        governance_snapshot.governance_continuity_reference if governance_snapshot_available else "not available"
    )

    if not available:
        return AIResearchContextConsumerGovernanceTimeline(
            governance_timeline_state="unavailable",
            governance_timeline_visible=False,
            governance_continuity_visible=False,
            governance_timeline_reference="not available",
            governance_state_sequence_reference="not available",
            governance_continuity_reference="not available",
            governance_summary_reference=governance_summary_reference,
            governance_status_reference=governance_status_reference,
            governance_status_validation_reference=governance_status_validation_reference,
            governance_snapshot_validation_reference=governance_snapshot_validation_reference,
            governance_snapshot_reference=governance_snapshot_reference,
            readiness_reference=readiness_reference,
            health_reference=health_reference,
            version_reference=version_reference,
            compatibility_reference=compatibility_reference,
            capability_reference=capability_reference,
            consumer_ready=consumer_ready,
            timeline_continuity_consistent=False,
            readiness_status=readiness_state,
            health_status=health_state,
            summary="AI research context consumer governance timeline is unavailable.",
            contract_meta=AIResearchContextConsumerGovernanceTimelineContractMeta(surface=surface),
        )

    timeline_continuity_consistent = bool(
        governance_status_validation_available
        and governance_snapshot_validation_available
        and governance_status_validation.governance_status_consistent
        and governance_snapshot_validation.governance_snapshot_consistent
    )
    sequence_reference = _state_sequence_reference(
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_snapshot_reference=governance_snapshot_reference,
    )
    governance_timeline_state = _timeline_state(
        governance_summary_available=governance_summary_available,
        governance_status_available=governance_status_available,
        governance_status_validation_available=governance_status_validation_available,
        governance_snapshot_available=governance_snapshot_available,
        governance_snapshot_validation_available=governance_snapshot_validation_available,
        timeline_continuity_consistent=timeline_continuity_consistent,
    )
    governance_timeline_visible = governance_timeline_state in {"complete", "partial"}
    governance_continuity_visible = bool(
        governance_snapshot_available or governance_snapshot_validation_available
    )
    governance_timeline_reference = _timeline_reference(
        governance_timeline_state=governance_timeline_state,
        governance_timeline_visible=governance_timeline_visible,
        governance_continuity_visible=governance_continuity_visible,
        governance_state_sequence_reference=sequence_reference,
        governance_continuity_reference=continuity_reference,
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        consumer_ready=consumer_ready,
        timeline_continuity_consistent=timeline_continuity_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
    )
    summary = _summary_text(
        governance_timeline_state=governance_timeline_state,
        governance_timeline_visible=governance_timeline_visible,
        governance_continuity_visible=governance_continuity_visible,
        governance_timeline_reference=governance_timeline_reference,
        governance_state_sequence_reference=sequence_reference,
        governance_continuity_reference=continuity_reference,
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        consumer_ready=consumer_ready,
        timeline_continuity_consistent=timeline_continuity_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
    )
    return AIResearchContextConsumerGovernanceTimeline(
        available=True,
        governance_timeline_state=governance_timeline_state,
        governance_timeline_visible=governance_timeline_visible,
        governance_continuity_visible=governance_continuity_visible,
        governance_timeline_reference=governance_timeline_reference,
        governance_state_sequence_reference=sequence_reference,
        governance_continuity_reference=continuity_reference,
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        consumer_ready=consumer_ready,
        timeline_continuity_consistent=timeline_continuity_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineContractMeta(surface=surface),
    )


def build_ai_research_context_consumer_governance_timeline_markdown(
    governance_timeline: AIResearchContextConsumerGovernanceTimeline | None,
) -> str:
    if governance_timeline is None or not governance_timeline.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline",
                "",
                "AI research context consumer governance timeline is unavailable.",
            ]
        )

    rows = [
        ("Governance timeline state", governance_timeline.governance_timeline_state),
        (
            "Governance timeline visible",
            "Yes" if governance_timeline.governance_timeline_visible else "No",
        ),
        (
            "Governance continuity visible",
            "Yes" if governance_timeline.governance_continuity_visible else "No",
        ),
        ("Governance timeline reference", governance_timeline.governance_timeline_reference),
        (
            "Governance state sequence reference",
            governance_timeline.governance_state_sequence_reference,
        ),
        ("Governance continuity reference", governance_timeline.governance_continuity_reference),
        ("Governance summary reference", governance_timeline.governance_summary_reference),
        ("Governance status reference", governance_timeline.governance_status_reference),
        (
            "Governance status validation reference",
            governance_timeline.governance_status_validation_reference,
        ),
        (
            "Governance snapshot validation reference",
            governance_timeline.governance_snapshot_validation_reference,
        ),
        ("Governance snapshot reference", governance_timeline.governance_snapshot_reference),
        ("Readiness reference", governance_timeline.readiness_reference),
        ("Health reference", governance_timeline.health_reference),
        ("Version reference", governance_timeline.version_reference),
        ("Compatibility reference", governance_timeline.compatibility_reference),
        ("Capability reference", governance_timeline.capability_reference),
        ("Consumer ready", "Yes" if governance_timeline.consumer_ready else "No"),
        (
            "Timeline continuity consistent",
            "Yes" if governance_timeline.timeline_continuity_consistent else "No",
        ),
        ("Readiness status", governance_timeline.readiness_status),
        ("Health status", governance_timeline.health_status),
        (
            "Governance timeline contract",
            f"{governance_timeline.contract_meta.version} / {governance_timeline.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline",
        "",
        f"*{governance_timeline.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _timeline_state(
    *,
    governance_summary_available: bool,
    governance_status_available: bool,
    governance_status_validation_available: bool,
    governance_snapshot_available: bool,
    governance_snapshot_validation_available: bool,
    timeline_continuity_consistent: bool,
) -> Literal["complete", "partial", "unavailable", "unknown"]:
    if not any(
        [
            governance_summary_available,
            governance_status_available,
            governance_status_validation_available,
            governance_snapshot_available,
            governance_snapshot_validation_available,
        ]
    ):
        return "unknown"
    if (
        timeline_continuity_consistent
        and governance_summary_available
        and governance_status_available
        and governance_status_validation_available
        and governance_snapshot_available
        and governance_snapshot_validation_available
    ):
        return "complete"
    if any(
        [
            governance_summary_available,
            governance_status_available,
            governance_status_validation_available,
            governance_snapshot_available,
            governance_snapshot_validation_available,
        ]
    ):
        return "partial"
    return "unknown"


def _state_sequence_reference(
    *,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    governance_snapshot_validation_reference: str,
    governance_snapshot_reference: str,
) -> str:
    return (
        "governance_summary="
        f"{governance_summary_reference}; "
        "governance_status="
        f"{governance_status_reference}; "
        "governance_status_validation="
        f"{governance_status_validation_reference}; "
        "governance_snapshot_validation="
        f"{governance_snapshot_validation_reference}; "
        "governance_snapshot="
        f"{governance_snapshot_reference}"
    )


def _timeline_reference(
    *,
    governance_timeline_state: str,
    governance_timeline_visible: bool,
    governance_continuity_visible: bool,
    governance_state_sequence_reference: str,
    governance_continuity_reference: str,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    governance_snapshot_validation_reference: str,
    governance_snapshot_reference: str,
    readiness_reference: str,
    health_reference: str,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    consumer_ready: bool,
    timeline_continuity_consistent: bool,
    readiness_status: str,
    health_status: str,
) -> str:
    return (
        "AI research context consumer governance timeline: "
        f"state={governance_timeline_state}; "
        f"visible={'yes' if governance_timeline_visible else 'no'}; "
        f"continuity_visible={'yes' if governance_continuity_visible else 'no'}; "
        f"sequence={governance_state_sequence_reference}; "
        f"continuity={governance_continuity_reference}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"governance_snapshot_validation={governance_snapshot_validation_reference}; "
        f"governance_snapshot={governance_snapshot_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"version={version_reference}; "
        f"compatibility={compatibility_reference}; "
        f"capability={capability_reference}; "
        f"ready={'yes' if consumer_ready else 'no'}; "
        f"continuity_consistent={'yes' if timeline_continuity_consistent else 'no'}; "
        f"readiness_status={readiness_status}; "
        f"health_status={health_status}"
    )


def _summary_text(
    *,
    governance_timeline_state: str,
    governance_timeline_visible: bool,
    governance_continuity_visible: bool,
    governance_timeline_reference: str,
    governance_state_sequence_reference: str,
    governance_continuity_reference: str,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    governance_snapshot_validation_reference: str,
    governance_snapshot_reference: str,
    readiness_reference: str,
    health_reference: str,
    consumer_ready: bool,
    timeline_continuity_consistent: bool,
    readiness_status: str,
    health_status: str,
) -> str:
    return (
        "AI research context consumer governance timeline: "
        f"state={governance_timeline_state}; "
        f"visible={'yes' if governance_timeline_visible else 'no'}; "
        f"continuity_visible={'yes' if governance_continuity_visible else 'no'}; "
        f"timeline={governance_timeline_reference}; "
        f"sequence={governance_state_sequence_reference}; "
        f"continuity={governance_continuity_reference}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"governance_snapshot_validation={governance_snapshot_validation_reference}; "
        f"governance_snapshot={governance_snapshot_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"ready={'yes' if consumer_ready else 'no'}; "
        f"continuity_consistent={'yes' if timeline_continuity_consistent else 'no'}; "
        f"readiness_status={readiness_status}; "
        f"health_status={health_status}"
    )


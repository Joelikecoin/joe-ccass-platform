from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SNAPSHOT_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SNAPSHOT_SURFACE = (
    "ai_research_context_consumer_governance_snapshot"
)


class AIResearchContextConsumerGovernanceSnapshotContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SNAPSHOT_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SNAPSHOT_SURFACE


class AIResearchContextConsumerGovernanceSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_snapshot_state: Literal["complete", "partial", "unavailable", "unknown"] = "unknown"
    governance_snapshot_visible: bool = False
    governance_snapshot_reference: str = "not available"
    governance_continuity_reference: str = "not available"
    governance_summary_reference: str = "not available"
    governance_status_reference: str = "not available"
    governance_status_validation_reference: str = "not available"
    readiness_reference: str = "not available"
    health_reference: str = "not available"
    version_reference: str = "not available"
    compatibility_reference: str = "not available"
    capability_reference: str = "not available"
    consumer_ready: bool = False
    snapshot_continuity_consistent: bool = False
    readiness_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    health_status: Literal["healthy", "partial", "unavailable", "unknown"] = "unknown"
    governance_snapshot_summary: str = (
        "AI research context consumer governance snapshot is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceSnapshotContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceSnapshotContractMeta
    )


def build_ai_research_context_consumer_governance_snapshot(
    *,
    available: bool,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    governance_summary: AIResearchContextConsumerGovernanceSummary | None,
    governance_status: AIResearchContextConsumerGovernanceStatus | None,
    governance_status_validation: AIResearchContextConsumerGovernanceStatusValidation | None,
    readiness_status: AIResearchContextConsumerReadinessStatus | None,
    health_indicator: AIResearchContextConsumerHealthIndicator | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SNAPSHOT_SURFACE,
) -> AIResearchContextConsumerGovernanceSnapshot:
    governance_summary_reference = (
        governance_summary.summary if governance_summary is not None else "not available"
    )
    governance_status_reference = (
        governance_status.governance_reference
        if governance_status is not None and governance_status.available
        else "not available"
    )
    governance_status_validation_reference = (
        governance_status_validation.validation_reference
        if governance_status_validation is not None and governance_status_validation.available
        else "not available"
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

    if not available:
        return AIResearchContextConsumerGovernanceSnapshot(
            governance_snapshot_state="unavailable",
            governance_snapshot_visible=False,
            governance_snapshot_reference="not available",
            governance_continuity_reference="not available",
            governance_summary_reference=governance_summary_reference,
            governance_status_reference=governance_status_reference,
            governance_status_validation_reference=governance_status_validation_reference,
            readiness_reference=readiness_reference,
            health_reference=health_reference,
            version_reference=version_reference,
            compatibility_reference=compatibility_reference,
            capability_reference=capability_reference,
            consumer_ready=consumer_ready,
            snapshot_continuity_consistent=False,
            readiness_status=readiness_state,
            health_status=health_state,
            governance_snapshot_summary=(
                "AI research context consumer governance snapshot is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceSnapshotContractMeta(
                surface=surface
            ),
        )

    governance_snapshot_state = _snapshot_state(
        governance_status=governance_status,
        governance_status_validation=governance_status_validation,
    )
    governance_snapshot_visible = governance_snapshot_state in {"complete", "partial"}
    snapshot_continuity_consistent = governance_snapshot_state == "complete"
    governance_snapshot_reference = _snapshot_reference(
        governance_snapshot_state=governance_snapshot_state,
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
    )
    governance_continuity_reference = _continuity_reference(
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
    )
    governance_snapshot_summary = _summary_text(
        governance_snapshot_state=governance_snapshot_state,
        governance_snapshot_visible=governance_snapshot_visible,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_continuity_reference=governance_continuity_reference,
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        consumer_ready=consumer_ready,
        snapshot_continuity_consistent=snapshot_continuity_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
    )
    return AIResearchContextConsumerGovernanceSnapshot(
        available=True,
        governance_snapshot_state=governance_snapshot_state,
        governance_snapshot_visible=governance_snapshot_visible,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_continuity_reference=governance_continuity_reference,
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        consumer_ready=consumer_ready,
        snapshot_continuity_consistent=snapshot_continuity_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
        governance_snapshot_summary=governance_snapshot_summary,
        contract_meta=AIResearchContextConsumerGovernanceSnapshotContractMeta(surface=surface),
    )


def build_ai_research_context_consumer_governance_snapshot_markdown(
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
) -> str:
    if governance_snapshot is None or not governance_snapshot.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Snapshot",
                "",
                "AI research context consumer governance snapshot is unavailable.",
            ]
        )

    rows = [
        ("Governance snapshot state", governance_snapshot.governance_snapshot_state),
        (
            "Governance snapshot visible",
            "Yes" if governance_snapshot.governance_snapshot_visible else "No",
        ),
        ("Governance snapshot reference", governance_snapshot.governance_snapshot_reference),
        ("Governance continuity reference", governance_snapshot.governance_continuity_reference),
        ("Governance summary reference", governance_snapshot.governance_summary_reference),
        ("Governance status reference", governance_snapshot.governance_status_reference),
        (
            "Governance status validation reference",
            governance_snapshot.governance_status_validation_reference,
        ),
        ("Readiness reference", governance_snapshot.readiness_reference),
        ("Health reference", governance_snapshot.health_reference),
        ("Version reference", governance_snapshot.version_reference),
        ("Compatibility reference", governance_snapshot.compatibility_reference),
        ("Capability reference", governance_snapshot.capability_reference),
        ("Consumer ready", "Yes" if governance_snapshot.consumer_ready else "No"),
        (
            "Snapshot continuity consistent",
            "Yes" if governance_snapshot.snapshot_continuity_consistent else "No",
        ),
        ("Readiness status", governance_snapshot.readiness_status),
        ("Health status", governance_snapshot.health_status),
        (
            "Governance snapshot contract",
            f"{governance_snapshot.contract_meta.version} / {governance_snapshot.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Snapshot",
        "",
        f"*{governance_snapshot.governance_snapshot_summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _snapshot_state(
    *,
    governance_status: AIResearchContextConsumerGovernanceStatus | None,
    governance_status_validation: AIResearchContextConsumerGovernanceStatusValidation | None,
) -> Literal["complete", "partial", "unavailable", "unknown"]:
    if governance_status is None or not governance_status.available:
        return "unavailable"
    if governance_status_validation is not None and governance_status_validation.available:
        if governance_status_validation.validation_state == "consistent":
            return "complete"
        return "partial"
    if governance_status.governance_status == "complete":
        return "complete"
    if governance_status.governance_status == "partial":
        return "partial"
    return "unknown"


def _snapshot_reference(
    *,
    governance_snapshot_state: str,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    readiness_reference: str,
    health_reference: str,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
) -> str:
    return (
        "AI research context consumer governance snapshot: "
        f"state={governance_snapshot_state}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"version={version_reference}; "
        f"compatibility={compatibility_reference}; "
        f"capability={capability_reference}"
    )


def _continuity_reference(
    *,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    readiness_reference: str,
    health_reference: str,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
) -> str:
    return (
        "AI research context consumer governance continuity: "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"version={version_reference}; "
        f"compatibility={compatibility_reference}; "
        f"capability={capability_reference}"
    )


def _summary_text(
    *,
    governance_snapshot_state: str,
    governance_snapshot_visible: bool,
    governance_snapshot_reference: str,
    governance_continuity_reference: str,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    readiness_reference: str,
    health_reference: str,
    consumer_ready: bool,
    snapshot_continuity_consistent: bool,
    readiness_status: str,
    health_status: str,
) -> str:
    return (
        "AI research context consumer governance snapshot: "
        f"state={governance_snapshot_state}; "
        f"visible={'yes' if governance_snapshot_visible else 'no'}; "
        f"snapshot={governance_snapshot_reference}; "
        f"continuity={governance_continuity_reference}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"ready={'yes' if consumer_ready else 'no'}; "
        f"continuity_consistent={'yes' if snapshot_continuity_consistent else 'no'}; "
        f"readiness_status={readiness_status}; "
        f"health_status={health_status}"
    )

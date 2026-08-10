from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_capability_validation import (
    AIResearchContextConsumerCapabilityValidation,
)
from ccass_core.ai_research_context_consumer_governance_summary import (
    AIResearchContextConsumerGovernanceSummary,
)
from ccass_core.ai_research_context_consumer_governance_validation import (
    AIResearchContextConsumerGovernanceValidation,
)
from ccass_core.ai_research_context_consumer_health import (
    AIResearchContextConsumerHealthIndicator,
)
from ccass_core.ai_research_context_consumer_readiness import (
    AIResearchContextConsumerReadinessStatus,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_STATUS_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_STATUS_SURFACE = (
    "ai_research_context_consumer_governance_status"
)


class AIResearchContextConsumerGovernanceStatusContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_STATUS_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_STATUS_SURFACE


class AIResearchContextConsumerGovernanceStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_status: Literal["complete", "partial", "unavailable", "unknown"] = "unknown"
    governance_visible: bool = False
    availability_indication: str = (
        "AI research context consumer governance status is unavailable."
    )
    governance_reference: str = "not available"
    governance_summary_reference: str = "not available"
    governance_validation_reference: str = "not available"
    capability_validation_reference: str = "not available"
    readiness_reference: str = "not available"
    health_reference: str = "not available"
    version_reference: str = "not available"
    compatibility_reference: str = "not available"
    capability_reference: str = "not available"
    consumer_ready: bool = False
    capability_consistent: bool = False
    readiness_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    health_status: Literal["healthy", "partial", "unavailable", "unknown"] = "unknown"
    governance_status_summary: str = (
        "AI research context consumer governance status is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceStatusContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceStatusContractMeta
    )


def build_ai_research_context_consumer_governance_status(
    *,
    available: bool,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    capability_validation: AIResearchContextConsumerCapabilityValidation | None,
    governance_summary: AIResearchContextConsumerGovernanceSummary | None,
    governance_validation: AIResearchContextConsumerGovernanceValidation | None,
    readiness_status: AIResearchContextConsumerReadinessStatus | None,
    health_indicator: AIResearchContextConsumerHealthIndicator | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_STATUS_SURFACE,
) -> AIResearchContextConsumerGovernanceStatus:
    if not available:
        return AIResearchContextConsumerGovernanceStatus(
            governance_status="unavailable",
            governance_visible=False,
            availability_indication=(
                "AI research context consumer governance status is unavailable."
            ),
            governance_reference="not available",
            governance_summary_reference=(
                governance_summary.summary if governance_summary is not None else "not available"
            ),
            governance_validation_reference=(
                governance_validation.summary if governance_validation is not None else "not available"
            ),
            capability_validation_reference=(
                capability_validation.summary if capability_validation is not None else "not available"
            ),
            readiness_reference=(
                readiness_status.readiness_reference if readiness_status is not None else "not available"
            ),
            health_reference=(
                health_indicator.health_reference if health_indicator is not None else "not available"
            ),
            version_reference=version_reference,
            compatibility_reference=compatibility_reference,
            capability_reference=capability_reference,
            consumer_ready=bool(readiness_status.consumer_ready if readiness_status is not None else False),
            capability_consistent=bool(
                capability_validation.capability_consistent if capability_validation is not None else False
            ),
            readiness_status=(
                readiness_status.readiness_status if readiness_status is not None else "unknown"
            ),
            health_status=health_indicator.health_status if health_indicator is not None else "unknown",
            governance_status_summary=(
                "AI research context consumer governance status is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceStatusContractMeta(surface=surface),
        )

    governance_status = (
        governance_summary.governance_status
        if governance_summary is not None and governance_summary.available
        else "unknown"
    )
    governance_visible = (
        governance_summary.governance_visible
        if governance_summary is not None and governance_summary.available
        else False
    )
    availability_indication = (
        governance_summary.availability_indication
        if governance_summary is not None and governance_summary.available
        else "AI research context consumer governance status is unknown."
    )
    governance_reference = (
        governance_summary.governance_reference
        if governance_summary is not None and governance_summary.available
        else "not available"
    )
    governance_summary_reference = (
        governance_summary.summary if governance_summary is not None else "not available"
    )
    governance_validation_reference = (
        governance_validation.summary if governance_validation is not None else "not available"
    )
    capability_validation_reference = (
        capability_validation.summary if capability_validation is not None else "not available"
    )
    readiness_reference = (
        readiness_status.readiness_reference if readiness_status is not None else "not available"
    )
    health_reference = (
        health_indicator.health_reference if health_indicator is not None else "not available"
    )
    consumer_ready = bool(readiness_status.consumer_ready if readiness_status is not None else False)
    capability_consistent = bool(
        capability_validation.capability_consistent if capability_validation is not None else False
    )
    readiness_state = (
        readiness_status.readiness_status if readiness_status is not None else "unknown"
    )
    health_state = health_indicator.health_status if health_indicator is not None else "unknown"
    governance_status_summary = _summary_text(
        governance_status=governance_status,
        governance_visible=governance_visible,
        availability_indication=availability_indication,
        governance_reference=governance_reference,
        governance_summary_reference=governance_summary_reference,
        governance_validation_reference=governance_validation_reference,
        capability_validation_reference=capability_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        consumer_ready=consumer_ready,
        capability_consistent=capability_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
    )
    return AIResearchContextConsumerGovernanceStatus(
        available=True,
        governance_status=governance_status,
        governance_visible=governance_visible,
        availability_indication=availability_indication,
        governance_reference=governance_reference,
        governance_summary_reference=governance_summary_reference,
        governance_validation_reference=governance_validation_reference,
        capability_validation_reference=capability_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        consumer_ready=consumer_ready,
        capability_consistent=capability_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
        governance_status_summary=governance_status_summary,
        contract_meta=AIResearchContextConsumerGovernanceStatusContractMeta(surface=surface),
    )


def build_ai_research_context_consumer_governance_status_markdown(
    governance_status: AIResearchContextConsumerGovernanceStatus | None,
) -> str:
    if governance_status is None or not governance_status.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Status",
                "",
                "AI research context consumer governance status is unavailable.",
            ]
        )

    rows = [
        ("Governance status", governance_status.governance_status),
        ("Governance visible", "Yes" if governance_status.governance_visible else "No"),
        ("Availability indication", governance_status.availability_indication),
        ("Consumer ready", "Yes" if governance_status.consumer_ready else "No"),
        ("Capability consistent", "Yes" if governance_status.capability_consistent else "No"),
        ("Readiness status", governance_status.readiness_status),
        ("Health status", governance_status.health_status),
        ("Governance reference", governance_status.governance_reference),
        ("Governance summary reference", governance_status.governance_summary_reference),
        ("Governance validation reference", governance_status.governance_validation_reference),
        ("Capability validation reference", governance_status.capability_validation_reference),
        ("Readiness reference", governance_status.readiness_reference),
        ("Health reference", governance_status.health_reference),
        ("Version reference", governance_status.version_reference),
        ("Compatibility reference", governance_status.compatibility_reference),
        ("Capability reference", governance_status.capability_reference),
        (
            "Governance status contract",
            f"{governance_status.contract_meta.version} / {governance_status.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Status",
        "",
        f"*{governance_status.governance_status_summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _summary_text(
    *,
    governance_status: str,
    governance_visible: bool,
    availability_indication: str,
    governance_reference: str,
    governance_summary_reference: str,
    governance_validation_reference: str,
    capability_validation_reference: str,
    readiness_reference: str,
    health_reference: str,
    consumer_ready: bool,
    capability_consistent: bool,
    readiness_status: str,
    health_status: str,
) -> str:
    return (
        "AI research context consumer governance status: "
        f"status={governance_status}; "
        f"visible={'yes' if governance_visible else 'no'}; "
        f"availability={availability_indication}; "
        f"reference={governance_reference}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_validation={governance_validation_reference}; "
        f"capability_validation={capability_validation_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"ready={'yes' if consumer_ready else 'no'}; "
        f"capability_consistent={'yes' if capability_consistent else 'no'}; "
        f"readiness_status={readiness_status}; "
        f"health_status={health_status}"
    )

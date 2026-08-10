from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_capability_validation import (
    AIResearchContextConsumerCapabilityValidation,
)
from ccass_core.ai_research_context_consumer_health import (
    AIResearchContextConsumerHealthIndicator,
)
from ccass_core.ai_research_context_consumer_readiness import (
    AIResearchContextConsumerReadinessStatus,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SUMMARY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SUMMARY_SURFACE = (
    "ai_research_context_consumer_governance_summary"
)


class AIResearchContextConsumerGovernanceSummaryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SUMMARY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SUMMARY_SURFACE


class AIResearchContextConsumerGovernanceSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_status: Literal["complete", "partial", "unavailable", "unknown"] = "unknown"
    governance_visible: bool = False
    availability_indication: str = (
        "AI research context consumer governance summary is unavailable."
    )
    governance_reference: str = "not available"
    version_reference: str = "not available"
    compatibility_reference: str = "not available"
    capability_reference: str = "not available"
    validation_reference: str = "not available"
    readiness_reference: str = "not available"
    health_reference: str = "not available"
    consumer_ready: bool = False
    capability_consistent: bool = False
    readiness_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    health_status: Literal["healthy", "partial", "unavailable", "unknown"] = "unknown"
    summary: str = "AI research context consumer governance summary is unavailable."
    contract_meta: AIResearchContextConsumerGovernanceSummaryContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceSummaryContractMeta
    )


def build_ai_research_context_consumer_governance_summary(
    *,
    available: bool,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    capability_validation: AIResearchContextConsumerCapabilityValidation | None,
    readiness_status: AIResearchContextConsumerReadinessStatus | None,
    health_indicator: AIResearchContextConsumerHealthIndicator | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SUMMARY_SURFACE,
) -> AIResearchContextConsumerGovernanceSummary:
    capability_consistent = bool(
        capability_validation.capability_consistent if capability_validation is not None else False
    )
    readiness_state = (
        readiness_status.readiness_status if readiness_status is not None else "unknown"
    )
    health_state = health_indicator.health_status if health_indicator is not None else "unknown"
    consumer_ready = bool(readiness_status.consumer_ready if readiness_status is not None else False)
    validation_reference = (
        capability_validation.summary if capability_validation is not None else "not available"
    )
    readiness_reference = (
        readiness_status.readiness_reference if readiness_status is not None else "not available"
    )
    health_reference = (
        health_indicator.health_reference if health_indicator is not None else "not available"
    )

    if not available:
        return AIResearchContextConsumerGovernanceSummary(
            governance_status="unavailable",
            governance_visible=False,
            availability_indication=(
                "AI research context consumer governance summary is unavailable."
            ),
            governance_reference="not available",
            version_reference=version_reference,
            compatibility_reference=compatibility_reference,
            capability_reference=capability_reference,
            validation_reference=validation_reference,
            readiness_reference=readiness_reference,
            health_reference=health_reference,
            consumer_ready=consumer_ready,
            capability_consistent=capability_consistent,
            readiness_status=readiness_state,
            health_status=health_state,
            summary="AI research context consumer governance summary is unavailable.",
            contract_meta=AIResearchContextConsumerGovernanceSummaryContractMeta(surface=surface),
        )

    if capability_consistent and readiness_state == "ready" and health_state == "healthy":
        governance_status: Literal["complete", "partial", "unavailable", "unknown"] = "complete"
    elif health_state in {"partial", "unavailable"} or readiness_state in {
        "partial",
        "unavailable",
    }:
        governance_status = "partial"
    elif not capability_consistent:
        governance_status = "partial"
    else:
        governance_status = "unknown"

    governance_visible = governance_status in {"complete", "partial"}
    availability_indication = _availability_indication(governance_status)
    governance_reference = _governance_reference(
        governance_status=governance_status,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        validation_reference=validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
    )
    summary = _summary_text(
        governance_status=governance_status,
        availability_indication=availability_indication,
        governance_reference=governance_reference,
        consumer_ready=consumer_ready,
        capability_consistent=capability_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
    )
    return AIResearchContextConsumerGovernanceSummary(
        available=True,
        governance_status=governance_status,
        governance_visible=governance_visible,
        availability_indication=availability_indication,
        governance_reference=governance_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        validation_reference=validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        consumer_ready=consumer_ready,
        capability_consistent=capability_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceSummaryContractMeta(surface=surface),
    )


def build_ai_research_context_consumer_governance_summary_markdown(
    governance_summary: AIResearchContextConsumerGovernanceSummary | None,
) -> str:
    if governance_summary is None or not governance_summary.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Summary",
                "",
                "AI research context consumer governance summary is unavailable.",
            ]
        )

    rows = [
        ("Governance status", governance_summary.governance_status),
        ("Governance visible", "Yes" if governance_summary.governance_visible else "No"),
        ("Availability indication", governance_summary.availability_indication),
        ("Consumer ready", "Yes" if governance_summary.consumer_ready else "No"),
        ("Capability consistent", "Yes" if governance_summary.capability_consistent else "No"),
        ("Readiness status", governance_summary.readiness_status),
        ("Health status", governance_summary.health_status),
        ("Governance reference", governance_summary.governance_reference),
        ("Version reference", governance_summary.version_reference),
        ("Compatibility reference", governance_summary.compatibility_reference),
        ("Capability reference", governance_summary.capability_reference),
        ("Validation reference", governance_summary.validation_reference),
        ("Readiness reference", governance_summary.readiness_reference),
        ("Health reference", governance_summary.health_reference),
        (
            "Governance contract",
            f"{governance_summary.contract_meta.version} / {governance_summary.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Summary",
        "",
        f"*{governance_summary.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _availability_indication(
    governance_status: Literal["complete", "partial", "unavailable", "unknown"],
) -> str:
    if governance_status == "complete":
        return "Consumer governance summary is complete."
    if governance_status == "partial":
        return "Consumer governance summary is partial."
    if governance_status == "unavailable":
        return "Consumer governance summary is unavailable."
    return "Consumer governance summary is unknown."


def _governance_reference(
    *,
    governance_status: str,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    validation_reference: str,
    readiness_reference: str,
    health_reference: str,
) -> str:
    return (
        f"{governance_status} / "
        f"{version_reference} / "
        f"{compatibility_reference} / "
        f"{capability_reference} / "
        f"{validation_reference} / "
        f"{readiness_reference} / "
        f"{health_reference}"
    )


def _summary_text(
    *,
    governance_status: str,
    availability_indication: str,
    governance_reference: str,
    consumer_ready: bool,
    capability_consistent: bool,
    readiness_status: str,
    health_status: str,
) -> str:
    return (
        "AI research context consumer governance summary: "
        f"status={governance_status}; "
        f"availability={availability_indication}; "
        f"ready={'yes' if consumer_ready else 'no'}; "
        f"capability_consistent={'yes' if capability_consistent else 'no'}; "
        f"readiness={readiness_status}; "
        f"health={health_status}; "
        f"reference={governance_reference}"
    )

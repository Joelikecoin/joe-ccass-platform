from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_capability_validation import (
    AIResearchContextConsumerCapabilityValidation,
)
from ccass_core.ai_research_context_consumer_readiness import (
    AIResearchContextConsumerReadinessStatus,
)

AI_RESEARCH_CONTEXT_CONSUMER_HEALTH_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_HEALTH_SURFACE = "ai_research_context_consumer_health"


class AIResearchContextConsumerHealthContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_HEALTH_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_HEALTH_SURFACE


class AIResearchContextConsumerHealthIndicator(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    health_status: Literal["healthy", "partial", "unavailable", "unknown"] = "unknown"
    health_visible: bool = False
    availability_indication: str = "AI research context consumer health is unavailable."
    health_reference: str = "not available"
    readiness_reference: str = "not available"
    capability_validation_reference: str = "not available"
    consumer_ready: bool = False
    capability_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
    health_summary: str = "AI research context consumer health is unavailable."
    contract_meta: AIResearchContextConsumerHealthContractMeta = Field(
        default_factory=AIResearchContextConsumerHealthContractMeta
    )


def build_ai_research_context_consumer_health_indicator(
    *,
    available: bool,
    consumer_ready: bool,
    readiness_status: AIResearchContextConsumerReadinessStatus | None,
    capability_validation: AIResearchContextConsumerCapabilityValidation | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_HEALTH_SURFACE,
) -> AIResearchContextConsumerHealthIndicator:
    capability_consistent = bool(
        capability_validation.capability_consistent if capability_validation is not None else False
    )
    validation_state = (
        capability_validation.validation_state if capability_validation is not None else "unknown"
    )
    readiness_state = (
        readiness_status.readiness_status if readiness_status is not None else "unknown"
    )

    if not available:
        return AIResearchContextConsumerHealthIndicator(
            health_status="unavailable",
            health_visible=False,
            availability_indication="AI research context consumer health is unavailable.",
            health_reference="not available",
            readiness_reference=(
                readiness_status.readiness_reference if readiness_status is not None else "not available"
            ),
            capability_validation_reference=(
                capability_validation.summary if capability_validation is not None else "not available"
            ),
            consumer_ready=consumer_ready,
            capability_consistent=capability_consistent,
            validation_state=validation_state,
            health_summary="AI research context consumer health is unavailable.",
            contract_meta=AIResearchContextConsumerHealthContractMeta(surface=surface),
        )

    if readiness_state == "ready" and capability_consistent:
        health_status: Literal["healthy", "partial", "unavailable", "unknown"] = "healthy"
    elif readiness_state == "unavailable":
        health_status = "unavailable"
    elif readiness_state in {"partial", "unknown"} or validation_state in {"partial", "inconsistent"}:
        health_status = "partial"
    else:
        health_status = "unknown"

    health_visible = health_status in {"healthy", "partial"}
    availability_indication = _availability_indication(health_status)
    health_reference = _health_reference(
        health_status=health_status,
        readiness_status=readiness_state,
        capability_validation=capability_validation,
        readiness_reference=(
            readiness_status.readiness_reference if readiness_status is not None else "not available"
        ),
    )
    health_summary = _summary_text(
        health_status=health_status,
        readiness_status=readiness_state,
        capability_consistent=capability_consistent,
        validation_state=validation_state,
        consumer_ready=consumer_ready,
        availability_indication=availability_indication,
        health_reference=health_reference,
    )
    return AIResearchContextConsumerHealthIndicator(
        available=True,
        health_status=health_status,
        health_visible=health_visible,
        availability_indication=availability_indication,
        health_reference=health_reference,
        readiness_reference=(
            readiness_status.readiness_reference if readiness_status is not None else "not available"
        ),
        capability_validation_reference=(
            capability_validation.summary if capability_validation is not None else "not available"
        ),
        consumer_ready=consumer_ready,
        capability_consistent=capability_consistent,
        validation_state=validation_state,
        health_summary=health_summary,
        contract_meta=AIResearchContextConsumerHealthContractMeta(surface=surface),
    )


def build_ai_research_context_consumer_health_indicator_markdown(
    health_indicator: AIResearchContextConsumerHealthIndicator | None,
) -> str:
    if health_indicator is None or not health_indicator.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Health",
                "",
                "AI research context consumer health is unavailable.",
            ]
        )

    rows = [
        ("Health status", health_indicator.health_status),
        ("Health visible", "Yes" if health_indicator.health_visible else "No"),
        ("Availability indication", health_indicator.availability_indication),
        ("Consumer ready", "Yes" if health_indicator.consumer_ready else "No"),
        ("Capability consistent", "Yes" if health_indicator.capability_consistent else "No"),
        ("Validation state", health_indicator.validation_state),
        ("Health reference", health_indicator.health_reference),
        ("Readiness reference", health_indicator.readiness_reference),
        (
            "Capability validation reference",
            health_indicator.capability_validation_reference,
        ),
        (
            "Health contract",
            f"{health_indicator.contract_meta.version} / {health_indicator.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Health",
        "",
        f"*{health_indicator.health_summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _availability_indication(
    health_status: Literal["healthy", "partial", "unavailable", "unknown"],
) -> str:
    if health_status == "healthy":
        return "Consumer surface governance health is healthy."
    if health_status == "partial":
        return "Consumer surface governance health is partial."
    if health_status == "unavailable":
        return "Consumer surface governance health is unavailable."
    return "Consumer surface governance health is unknown."


def _health_reference(
    *,
    health_status: str,
    readiness_status: str,
    capability_validation: AIResearchContextConsumerCapabilityValidation | None,
    readiness_reference: str,
) -> str:
    validation_reference = (
        capability_validation.summary if capability_validation is not None else "not available"
    )
    return (
        f"{health_status} / "
        f"{readiness_status} / "
        f"{readiness_reference} / "
        f"{validation_reference}"
    )


def _summary_text(
    *,
    health_status: str,
    readiness_status: str,
    capability_consistent: bool,
    validation_state: str,
    consumer_ready: bool,
    availability_indication: str,
    health_reference: str,
) -> str:
    return (
        "AI research context consumer health: "
        f"status={health_status}; "
        f"readiness={readiness_status}; "
        f"ready={'yes' if consumer_ready else 'no'}; "
        f"capability_consistent={'yes' if capability_consistent else 'no'}; "
        f"validation_state={validation_state}; "
        f"availability={availability_indication}; "
        f"reference={health_reference}"
    )

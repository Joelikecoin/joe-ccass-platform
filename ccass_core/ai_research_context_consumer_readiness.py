from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_capability_validation import (
    AIResearchContextConsumerCapabilityValidation,
)

AI_RESEARCH_CONTEXT_CONSUMER_READINESS_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_READINESS_SURFACE = "ai_research_context_consumer_readiness"


class AIResearchContextConsumerReadinessContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_READINESS_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_READINESS_SURFACE


class AIResearchContextConsumerReadinessStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    readiness_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    availability_indication: str = "AI research context consumer readiness is unavailable."
    readiness_reference: str = "not available"
    readiness_visible: bool = False
    consumer_ready: bool = False
    capability_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
    capability_validation_reference: str = "not available"
    capability_reference: str = "not available"
    compatibility_reference: str = "not available"
    consumer_surface_declaration: str = "not available"
    readiness_summary: str = "AI research context consumer readiness is unavailable."
    contract_meta: AIResearchContextConsumerReadinessContractMeta = Field(
        default_factory=AIResearchContextConsumerReadinessContractMeta
    )


def build_ai_research_context_consumer_readiness_status(
    *,
    available: bool,
    consumer_ready: bool,
    capability_validation: AIResearchContextConsumerCapabilityValidation | None,
    capability_reference: str,
    compatibility_reference: str,
    consumer_surface_declaration: str,
    surface_version_reference: str,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_READINESS_SURFACE,
) -> AIResearchContextConsumerReadinessStatus:
    if not available:
        return AIResearchContextConsumerReadinessStatus(
            readiness_status="unavailable",
            availability_indication="AI research context consumer readiness is unavailable.",
            readiness_reference="not available",
            readiness_visible=False,
            consumer_ready=False,
            capability_consistent=False,
            validation_state="unknown",
            capability_validation_reference="not available",
            capability_reference=capability_reference,
            compatibility_reference=compatibility_reference,
            consumer_surface_declaration=consumer_surface_declaration,
            readiness_summary="AI research context consumer readiness is unavailable.",
            contract_meta=AIResearchContextConsumerReadinessContractMeta(surface=surface),
        )

    validation_state = (
        capability_validation.validation_state
        if capability_validation is not None
        else "unknown"
    )
    capability_consistent = bool(
        capability_validation.capability_consistent if capability_validation is not None else False
    )
    if consumer_ready and capability_consistent:
        readiness_status: Literal["ready", "partial", "unavailable", "unknown"] = "ready"
    elif validation_state == "inconsistent":
        readiness_status = "partial"
    elif validation_state == "partial":
        readiness_status = "partial"
    elif consumer_ready:
        readiness_status = "partial"
    else:
        readiness_status = "unknown"

    readiness_visible = readiness_status in {"ready", "partial"}
    availability_indication = _availability_indication(readiness_status)
    readiness_reference = _readiness_reference(
        readiness_status=readiness_status,
        surface_version_reference=surface_version_reference,
        capability_reference=capability_reference,
        compatibility_reference=compatibility_reference,
        capability_validation=capability_validation,
    )
    summary = _summary_text(
        readiness_status=readiness_status,
        availability_indication=availability_indication,
        readiness_reference=readiness_reference,
        capability_consistent=capability_consistent,
        validation_state=validation_state,
        consumer_ready=consumer_ready,
    )
    return AIResearchContextConsumerReadinessStatus(
        available=True,
        readiness_status=readiness_status,
        availability_indication=availability_indication,
        readiness_reference=readiness_reference,
        readiness_visible=readiness_visible,
        consumer_ready=consumer_ready,
        capability_consistent=capability_consistent,
        validation_state=validation_state,
        capability_validation_reference=(
            capability_validation.summary if capability_validation is not None else "not available"
        ),
        capability_reference=capability_reference,
        compatibility_reference=compatibility_reference,
        consumer_surface_declaration=consumer_surface_declaration,
        readiness_summary=summary,
        contract_meta=AIResearchContextConsumerReadinessContractMeta(surface=surface),
    )


def build_ai_research_context_consumer_readiness_status_markdown(
    readiness_status: AIResearchContextConsumerReadinessStatus | None,
) -> str:
    if readiness_status is None or not readiness_status.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Readiness",
                "",
                "AI research context consumer readiness is unavailable.",
            ]
        )

    rows = [
        ("Readiness status", readiness_status.readiness_status),
        ("Availability indication", readiness_status.availability_indication),
        ("Readiness visible", "Yes" if readiness_status.readiness_visible else "No"),
        ("Consumer ready", "Yes" if readiness_status.consumer_ready else "No"),
        ("Capability consistent", "Yes" if readiness_status.capability_consistent else "No"),
        ("Validation state", readiness_status.validation_state),
        ("Readiness reference", readiness_status.readiness_reference),
        ("Capability validation reference", readiness_status.capability_validation_reference),
        ("Capability reference", readiness_status.capability_reference),
        ("Compatibility reference", readiness_status.compatibility_reference),
        ("Consumer surface declaration", readiness_status.consumer_surface_declaration),
        (
            "Readiness contract",
            f"{readiness_status.contract_meta.version} / {readiness_status.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Readiness",
        "",
        f"*{readiness_status.readiness_summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _availability_indication(
    readiness_status: Literal["ready", "partial", "unavailable", "unknown"],
) -> str:
    if readiness_status == "ready":
        return "Consumer surface is ready for use."
    if readiness_status == "partial":
        return "Consumer surface is available with partial readiness."
    if readiness_status == "unavailable":
        return "Consumer surface is unavailable."
    return "Consumer surface readiness is unknown."


def _readiness_reference(
    *,
    readiness_status: str,
    surface_version_reference: str,
    capability_reference: str,
    compatibility_reference: str,
    capability_validation: AIResearchContextConsumerCapabilityValidation | None,
) -> str:
    validation_reference = (
        capability_validation.summary if capability_validation is not None else "not available"
    )
    return (
        f"{readiness_status} / "
        f"{surface_version_reference} / "
        f"{capability_reference} / "
        f"{compatibility_reference} / "
        f"{validation_reference}"
    )


def _summary_text(
    *,
    readiness_status: str,
    availability_indication: str,
    readiness_reference: str,
    capability_consistent: bool,
    validation_state: str,
    consumer_ready: bool,
) -> str:
    return (
        "AI research context consumer readiness: "
        f"status={readiness_status}; "
        f"availability={availability_indication}; "
        f"ready={'yes' if consumer_ready else 'no'}; "
        f"capability_consistent={'yes' if capability_consistent else 'no'}; "
        f"validation_state={validation_state}; "
        f"reference={readiness_reference}"
    )

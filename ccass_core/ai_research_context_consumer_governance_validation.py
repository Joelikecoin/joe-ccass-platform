from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_capability_validation import (
    AIResearchContextConsumerCapabilityValidation,
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

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_VALIDATION_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_VALIDATION_SURFACE = (
    "ai_research_context_consumer_governance_validation"
)


class AIResearchContextConsumerGovernanceValidationContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_VALIDATION_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_VALIDATION_SURFACE


class AIResearchContextConsumerGovernanceValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
    governance_visible: bool = False
    validation_reference: str = "not available"
    version_reference: str = "not available"
    compatibility_reference: str = "not available"
    capability_reference: str = "not available"
    capability_validation_reference: str = "not available"
    readiness_reference: str = "not available"
    health_reference: str = "not available"
    governance_reference: str = "not available"
    governance_summary_reference: str = "not available"
    missing_governance_references: list[str] = Field(default_factory=list)
    consistency_warnings: list[str] = Field(default_factory=list)
    summary: str = "AI research context consumer governance validation is unavailable."
    contract_meta: AIResearchContextConsumerGovernanceValidationContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceValidationContractMeta
    )


def build_ai_research_context_consumer_governance_validation(
    *,
    available: bool,
    governance_summary: AIResearchContextConsumerGovernanceSummary | None,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    capability_validation: AIResearchContextConsumerCapabilityValidation | None,
    readiness_status: AIResearchContextConsumerReadinessStatus | None,
    health_indicator: AIResearchContextConsumerHealthIndicator | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_VALIDATION_SURFACE,
) -> AIResearchContextConsumerGovernanceValidation:
    governance_summary_available = bool(
        governance_summary is not None and governance_summary.available
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
    governance_summary_reference = (
        governance_summary.summary if governance_summary_available else "not available"
    )

    if not available:
        return AIResearchContextConsumerGovernanceValidation(
            governance_consistent=False,
            validation_state="unknown",
            governance_visible=False,
            validation_reference="not available",
            version_reference=version_reference,
            compatibility_reference=compatibility_reference,
            capability_reference=capability_reference,
            capability_validation_reference=capability_validation_reference,
            readiness_reference=readiness_reference,
            health_reference=health_reference,
            governance_reference="not available",
            governance_summary_reference=governance_summary_reference,
            summary="AI research context consumer governance validation is unavailable.",
            contract_meta=AIResearchContextConsumerGovernanceValidationContractMeta(
                surface=surface
            ),
        )

    missing_governance_references: list[str] = []
    if not _reference_present(version_reference):
        missing_governance_references.append("version_reference")
    if not _reference_present(compatibility_reference):
        missing_governance_references.append("compatibility_reference")
    if not _reference_present(capability_reference):
        missing_governance_references.append("capability_reference")
    if not _reference_present(capability_validation_reference):
        missing_governance_references.append("capability_validation_reference")
    if not _reference_present(readiness_reference):
        missing_governance_references.append("readiness_reference")
    if not _reference_present(health_reference):
        missing_governance_references.append("health_reference")
    if not _reference_present(governance_summary_reference):
        missing_governance_references.append("governance_summary_reference")
    if governance_summary is None or not governance_summary.available:
        missing_governance_references.append("governance_summary")

    consistency_warnings: list[str] = []
    if governance_summary is not None and governance_summary.available:
        if governance_summary.version_reference != version_reference:
            consistency_warnings.append("Governance summary version reference mismatch.")
        if governance_summary.compatibility_reference != compatibility_reference:
            consistency_warnings.append("Governance summary compatibility reference mismatch.")
        if governance_summary.capability_reference != capability_reference:
            consistency_warnings.append("Governance summary capability reference mismatch.")
        if governance_summary.validation_reference != capability_validation_reference:
            consistency_warnings.append("Governance summary validation reference mismatch.")
        if governance_summary.readiness_reference != readiness_reference:
            consistency_warnings.append("Governance summary readiness reference mismatch.")
        if governance_summary.health_reference != health_reference:
            consistency_warnings.append("Governance summary health reference mismatch.")

    governance_consistent = (
        governance_summary_available
        and not missing_governance_references
        and not consistency_warnings
    )

    if governance_consistent:
        validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "consistent"
    elif consistency_warnings:
        validation_state = "inconsistent"
    elif missing_governance_references:
        validation_state = "partial"
    else:
        validation_state = "unknown"

    governance_visible = validation_state in {"consistent", "partial"}
    validation_reference = _validation_reference(
        validation_state=validation_state,
        governance_reference=governance_summary.governance_reference
        if governance_summary is not None
        else "not available",
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        capability_validation_reference=capability_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
    )
    summary = _summary_text(
        validation_state=validation_state,
        governance_visible=governance_visible,
        governance_consistent=governance_consistent,
        validation_reference=validation_reference,
        missing_governance_references=missing_governance_references,
        consistency_warnings=consistency_warnings,
    )
    return AIResearchContextConsumerGovernanceValidation(
        available=True,
        governance_consistent=governance_consistent,
        validation_state=validation_state,
        governance_visible=governance_visible,
        validation_reference=validation_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        capability_validation_reference=capability_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        governance_reference=governance_summary.governance_reference
        if governance_summary is not None
        else "not available",
        governance_summary_reference=governance_summary_reference,
        missing_governance_references=missing_governance_references,
        consistency_warnings=consistency_warnings,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceValidationContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_validation_markdown(
    governance_validation: AIResearchContextConsumerGovernanceValidation | None,
) -> str:
    if governance_validation is None or not governance_validation.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Validation",
                "",
                "AI research context consumer governance validation is unavailable.",
            ]
        )

    rows = [
        ("Validation state", governance_validation.validation_state),
        ("Governance visible", "Yes" if governance_validation.governance_visible else "No"),
        (
            "Governance consistent",
            "Yes" if governance_validation.governance_consistent else "No",
        ),
        ("Validation reference", governance_validation.validation_reference),
        ("Version reference", governance_validation.version_reference),
        ("Compatibility reference", governance_validation.compatibility_reference),
        ("Capability reference", governance_validation.capability_reference),
        (
            "Capability validation reference",
            governance_validation.capability_validation_reference,
        ),
        ("Readiness reference", governance_validation.readiness_reference),
        ("Health reference", governance_validation.health_reference),
        ("Governance reference", governance_validation.governance_reference),
        (
            "Governance summary reference",
            governance_validation.governance_summary_reference,
        ),
        (
            "Missing governance references",
            _join_list(governance_validation.missing_governance_references),
        ),
        (
            "Consistency warnings",
            _join_list(governance_validation.consistency_warnings),
        ),
        (
            "Governance validation contract",
            f"{governance_validation.contract_meta.version} / {governance_validation.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Validation",
        "",
        f"*{governance_validation.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _validation_reference(
    *,
    validation_state: str,
    governance_reference: str,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    capability_validation_reference: str,
    readiness_reference: str,
    health_reference: str,
) -> str:
    return (
        f"{validation_state} / "
        f"{governance_reference} / "
        f"{version_reference} / "
        f"{compatibility_reference} / "
        f"{capability_reference} / "
        f"{capability_validation_reference} / "
        f"{readiness_reference} / "
        f"{health_reference}"
    )


def _summary_text(
    *,
    validation_state: str,
    governance_visible: bool,
    governance_consistent: bool,
    validation_reference: str,
    missing_governance_references: list[str],
    consistency_warnings: list[str],
) -> str:
    return (
        "AI research context consumer governance validation: "
        f"state={validation_state}; "
        f"governance_visible={'yes' if governance_visible else 'no'}; "
        f"governance_consistent={'yes' if governance_consistent else 'no'}; "
        f"missing_governance_references={_join_list(missing_governance_references)}; "
        f"consistency_warnings={_join_list(consistency_warnings)}; "
        f"reference={validation_reference}"
    )


def _reference_present(value: object | None) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text not in {"not available", "unavailable", "unknown"}


def _join_list(values: list[str]) -> str:
    if not values:
        return "none"
    return " | ".join(values)

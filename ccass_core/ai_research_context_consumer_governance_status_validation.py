from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_capability_validation import (
    AIResearchContextConsumerCapabilityValidation,
)
from ccass_core.ai_research_context_consumer_governance_status import (
    AIResearchContextConsumerGovernanceStatus,
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

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_STATUS_VALIDATION_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_STATUS_VALIDATION_SURFACE = (
    "ai_research_context_consumer_governance_status_validation"
)


class AIResearchContextConsumerGovernanceStatusValidationContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_STATUS_VALIDATION_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_STATUS_VALIDATION_SURFACE


class AIResearchContextConsumerGovernanceStatusValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_status_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
    governance_visible: bool = False
    validation_reference: str = "not available"
    governance_status_reference: str = "not available"
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
    missing_governance_status_references: list[str] = Field(default_factory=list)
    consistency_warnings: list[str] = Field(default_factory=list)
    summary: str = (
        "AI research context consumer governance status validation is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceStatusValidationContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceStatusValidationContractMeta
    )


def build_ai_research_context_consumer_governance_status_validation(
    *,
    available: bool,
    governance_status: AIResearchContextConsumerGovernanceStatus | None,
    governance_summary: AIResearchContextConsumerGovernanceSummary | None,
    governance_validation: AIResearchContextConsumerGovernanceValidation | None,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    capability_validation: AIResearchContextConsumerCapabilityValidation | None,
    readiness_status: AIResearchContextConsumerReadinessStatus | None,
    health_indicator: AIResearchContextConsumerHealthIndicator | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_STATUS_VALIDATION_SURFACE,
) -> AIResearchContextConsumerGovernanceStatusValidation:
    governance_status_available = bool(
        governance_status is not None and governance_status.available
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
        governance_summary.summary if governance_summary is not None else "not available"
    )
    governance_validation_reference = (
        governance_validation.summary if governance_validation is not None else "not available"
    )
    status_reference = (
        governance_status.governance_reference
        if governance_status is not None and governance_status.available
        else "not available"
    )

    if not available:
        return AIResearchContextConsumerGovernanceStatusValidation(
            governance_status_consistent=False,
            validation_state="unknown",
            governance_visible=False,
            validation_reference="not available",
            governance_status_reference=status_reference,
            governance_reference=(
                governance_status.governance_reference
                if governance_status is not None
                else "not available"
            ),
            governance_summary_reference=governance_summary_reference,
            governance_validation_reference=governance_validation_reference,
            capability_validation_reference=capability_validation_reference,
            readiness_reference=readiness_reference,
            health_reference=health_reference,
            version_reference=version_reference,
            compatibility_reference=compatibility_reference,
            capability_reference=capability_reference,
            consumer_ready=bool(
                readiness_status.consumer_ready if readiness_status is not None else False
            ),
            capability_consistent=bool(
                capability_validation.capability_consistent
                if capability_validation is not None
                else False
            ),
            readiness_status=(
                readiness_status.readiness_status if readiness_status is not None else "unknown"
            ),
            health_status=health_indicator.health_status
            if health_indicator is not None
            else "unknown",
            summary=(
                "AI research context consumer governance status validation is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceStatusValidationContractMeta(
                surface=surface
            ),
        )

    missing_governance_status_references: list[str] = []
    if not _reference_present(status_reference):
        missing_governance_status_references.append("governance_status_reference")
    if not _reference_present(
        governance_status.governance_status if governance_status is not None else None
    ):
        missing_governance_status_references.append("governance_status")
    if not _reference_present(
        governance_status.governance_visible if governance_status is not None else None
    ):
        missing_governance_status_references.append("governance_visible")
    if not _reference_present(
        governance_status.governance_summary_reference if governance_status is not None else None
    ):
        missing_governance_status_references.append("governance_summary_reference")
    if not _reference_present(
        governance_status.governance_validation_reference if governance_status is not None else None
    ):
        missing_governance_status_references.append("governance_validation_reference")
    if not _reference_present(
        governance_status.capability_validation_reference if governance_status is not None else None
    ):
        missing_governance_status_references.append("capability_validation_reference")
    if not _reference_present(
        governance_status.readiness_reference if governance_status is not None else None
    ):
        missing_governance_status_references.append("readiness_reference")
    if not _reference_present(governance_status.health_reference if governance_status is not None else None):
        missing_governance_status_references.append("health_reference")
    if not _reference_present(
        governance_status.version_reference if governance_status is not None else None
    ):
        missing_governance_status_references.append("version_reference")
    if not _reference_present(
        governance_status.compatibility_reference if governance_status is not None else None
    ):
        missing_governance_status_references.append("compatibility_reference")
    if not _reference_present(
        governance_status.capability_reference if governance_status is not None else None
    ):
        missing_governance_status_references.append("capability_reference")
    if governance_status is None or not governance_status.available:
        missing_governance_status_references.append("governance_status")

    consistency_warnings: list[str] = []
    if governance_status is not None and governance_status.available:
        if governance_status.governance_status != (
            governance_summary.governance_status
            if governance_summary is not None and governance_summary.available
            else "unknown"
        ):
            consistency_warnings.append("Governance status value mismatch.")
        if governance_status.governance_visible != (
            governance_summary.governance_visible
            if governance_summary is not None and governance_summary.available
            else False
        ):
            consistency_warnings.append("Governance status visibility mismatch.")
        if governance_status.governance_reference != (
            governance_summary.governance_reference
            if governance_summary is not None and governance_summary.available
            else "not available"
        ):
            consistency_warnings.append("Governance status reference mismatch.")
        if governance_status.governance_summary_reference != governance_summary_reference:
            consistency_warnings.append("Governance status summary reference mismatch.")
        if governance_status.governance_validation_reference != governance_validation_reference:
            consistency_warnings.append("Governance status validation reference mismatch.")
        if governance_status.capability_validation_reference != capability_validation_reference:
            consistency_warnings.append("Governance status capability validation reference mismatch.")
        if governance_status.readiness_reference != readiness_reference:
            consistency_warnings.append("Governance status readiness reference mismatch.")
        if governance_status.health_reference != health_reference:
            consistency_warnings.append("Governance status health reference mismatch.")
        if governance_status.version_reference != version_reference:
            consistency_warnings.append("Governance status version reference mismatch.")
        if governance_status.compatibility_reference != compatibility_reference:
            consistency_warnings.append("Governance status compatibility reference mismatch.")
        if governance_status.capability_reference != capability_reference:
            consistency_warnings.append("Governance status capability reference mismatch.")
        if governance_status.consumer_ready != bool(
            readiness_status.consumer_ready if readiness_status is not None else False
        ):
            consistency_warnings.append("Governance status consumer ready mismatch.")
        if governance_status.capability_consistent != bool(
            capability_validation.capability_consistent
            if capability_validation is not None
            else False
        ):
            consistency_warnings.append("Governance status capability consistency mismatch.")
        if governance_status.readiness_status != (
            readiness_status.readiness_status if readiness_status is not None else "unknown"
        ):
            consistency_warnings.append("Governance status readiness state mismatch.")
        if governance_status.health_status != (
            health_indicator.health_status if health_indicator is not None else "unknown"
        ):
            consistency_warnings.append("Governance status health state mismatch.")

    governance_status_consistent = (
        governance_status_available
        and not missing_governance_status_references
        and not consistency_warnings
    )

    if governance_status_consistent:
        validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "consistent"
    elif consistency_warnings:
        validation_state = "inconsistent"
    elif missing_governance_status_references:
        validation_state = "partial"
    else:
        validation_state = "unknown"

    governance_visible = validation_state in {"consistent", "partial"}
    validation_reference = _validation_reference(
        validation_state=validation_state,
        governance_status_reference=status_reference,
        governance_reference=(
            governance_status.governance_reference
            if governance_status is not None
            else "not available"
        ),
        governance_summary_reference=governance_summary_reference,
        governance_validation_reference=governance_validation_reference,
        capability_validation_reference=capability_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
    )
    summary = _summary_text(
        validation_state=validation_state,
        governance_visible=governance_visible,
        governance_status_consistent=governance_status_consistent,
        validation_reference=validation_reference,
        governance_status_reference=status_reference,
        missing_governance_status_references=missing_governance_status_references,
        consistency_warnings=consistency_warnings,
    )
    return AIResearchContextConsumerGovernanceStatusValidation(
        available=True,
        governance_status_consistent=governance_status_consistent,
        validation_state=validation_state,
        governance_visible=governance_visible,
        validation_reference=validation_reference,
        governance_status_reference=status_reference,
        governance_reference=(
            governance_status.governance_reference
            if governance_status is not None
            else "not available"
        ),
        governance_summary_reference=governance_summary_reference,
        governance_validation_reference=governance_validation_reference,
        capability_validation_reference=capability_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
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
        missing_governance_status_references=missing_governance_status_references,
        consistency_warnings=consistency_warnings,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceStatusValidationContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_status_validation_markdown(
    governance_status_validation: AIResearchContextConsumerGovernanceStatusValidation | None,
) -> str:
    if governance_status_validation is None or not governance_status_validation.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Status Validation",
                "",
                "AI research context consumer governance status validation is unavailable.",
            ]
        )

    rows = [
        ("Validation state", governance_status_validation.validation_state),
        ("Governance visible", "Yes" if governance_status_validation.governance_visible else "No"),
        (
            "Governance status consistent",
            "Yes" if governance_status_validation.governance_status_consistent else "No",
        ),
        ("Validation reference", governance_status_validation.validation_reference),
        ("Governance status reference", governance_status_validation.governance_status_reference),
        ("Governance reference", governance_status_validation.governance_reference),
        (
            "Governance summary reference",
            governance_status_validation.governance_summary_reference,
        ),
        (
            "Governance validation reference",
            governance_status_validation.governance_validation_reference,
        ),
        (
            "Capability validation reference",
            governance_status_validation.capability_validation_reference,
        ),
        ("Readiness reference", governance_status_validation.readiness_reference),
        ("Health reference", governance_status_validation.health_reference),
        ("Version reference", governance_status_validation.version_reference),
        ("Compatibility reference", governance_status_validation.compatibility_reference),
        ("Capability reference", governance_status_validation.capability_reference),
        (
            "Missing governance status references",
            _join_list(governance_status_validation.missing_governance_status_references),
        ),
        (
            "Consistency warnings",
            _join_list(governance_status_validation.consistency_warnings),
        ),
        (
            "Governance status validation contract",
            f"{governance_status_validation.contract_meta.version} / {governance_status_validation.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Status Validation",
        "",
        f"*{governance_status_validation.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _validation_reference(
    *,
    validation_state: str,
    governance_status_reference: str,
    governance_reference: str,
    governance_summary_reference: str,
    governance_validation_reference: str,
    capability_validation_reference: str,
    readiness_reference: str,
    health_reference: str,
) -> str:
    return (
        "AI research context consumer governance status validation: "
        f"state={validation_state}; "
        f"governance_status={governance_status_reference}; "
        f"reference={governance_reference}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_validation={governance_validation_reference}; "
        f"capability_validation={capability_validation_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}"
    )


def _summary_text(
    *,
    validation_state: str,
    governance_visible: bool,
    governance_status_consistent: bool,
    validation_reference: str,
    governance_status_reference: str,
    missing_governance_status_references: list[str],
    consistency_warnings: list[str],
) -> str:
    return (
        "AI research context consumer governance status validation: "
        f"state={validation_state}; "
        f"visible={'yes' if governance_visible else 'no'}; "
        f"consistent={'yes' if governance_status_consistent else 'no'}; "
        f"validation={validation_reference}; "
        f"governance_status={governance_status_reference}; "
        f"missing={_join_list(missing_governance_status_references)}; "
        f"warnings={_join_list(consistency_warnings)}"
    )


def _reference_present(value: str | bool | None) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    return bool(str(value).strip()) and str(value).strip().lower() not in {
        "not available",
        "unavailable",
        "unknown",
    }


def _join_list(values: list[str]) -> str:
    if not values:
        return "none"
    return " | ".join(values)

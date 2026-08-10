from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AI_RESEARCH_CONTEXT_CONSUMER_CAPABILITY_VALIDATION_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_CAPABILITY_VALIDATION_SURFACE = (
    "ai_research_context_consumer_capability_validation"
)


class AIResearchContextConsumerCapabilityValidationContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_CAPABILITY_VALIDATION_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_CAPABILITY_VALIDATION_SURFACE


class AIResearchContextConsumerCapabilityValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    capability_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
    surface_version_reference: str = "not available"
    surface_version_match: bool = False
    approved_surface: tuple[str, ...] = Field(default_factory=tuple)
    capability_supported_surface: tuple[str, ...] = Field(default_factory=tuple)
    compatibility_supported_surface: tuple[str, ...] = Field(default_factory=tuple)
    capability_reference: str = "not available"
    compatibility_reference: str = "not available"
    consumer_surface_declaration: str = "not available"
    capability_reference_present: bool = False
    compatibility_reference_present: bool = False
    consumer_surface_declaration_present: bool = False
    supported_surface_match: bool = False
    compatibility_supported_surface_match: bool = False
    missing_capability_references: list[str] = Field(default_factory=list)
    consistency_warnings: list[str] = Field(default_factory=list)
    summary: str = "AI research context consumer capability validation is unavailable."
    contract_meta: AIResearchContextConsumerCapabilityValidationContractMeta = Field(
        default_factory=AIResearchContextConsumerCapabilityValidationContractMeta
    )


def build_ai_research_context_consumer_capability_validation(
    *,
    surface_version_reference: str,
    approved_surface: tuple[str, ...],
    capability_supported_surface: tuple[str, ...] | None,
    compatibility_supported_surface: tuple[str, ...] | None,
    capability_reference: str | None,
    compatibility_reference: str | None,
    consumer_surface_declaration: str | None,
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_CAPABILITY_VALIDATION_VERSION,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_CAPABILITY_VALIDATION_SURFACE,
) -> AIResearchContextConsumerCapabilityValidation:
    capability_reference_present = _reference_present(capability_reference)
    compatibility_reference_present = _reference_present(compatibility_reference)
    consumer_surface_declaration_present = _reference_present(consumer_surface_declaration)
    version_reference_present = _reference_present(surface_version_reference)
    supported_surface_match = (
        capability_supported_surface is not None
        and tuple(capability_supported_surface) == tuple(approved_surface)
    )
    compatibility_supported_surface_match = (
        compatibility_supported_surface is not None
        and tuple(compatibility_supported_surface) == tuple(approved_surface)
    )

    missing_capability_references = []
    if not version_reference_present:
        missing_capability_references.append("surface_version_reference")
    if not capability_reference_present:
        missing_capability_references.append("capability_reference")
    if not compatibility_reference_present:
        missing_capability_references.append("compatibility_reference")
    if not consumer_surface_declaration_present:
        missing_capability_references.append("consumer_surface_declaration")
    if capability_supported_surface is None:
        missing_capability_references.append("capability_supported_surface")
    if compatibility_supported_surface is None:
        missing_capability_references.append("compatibility_supported_surface")

    consistency_warnings = []
    if version_reference_present and surface_version_reference != version:
        consistency_warnings.append("Surface version reference does not match the capability contract version.")
    if capability_supported_surface is not None and not supported_surface_match:
        consistency_warnings.append("Capability supported surface does not match the approved consumer surface.")
    if compatibility_supported_surface is not None and not compatibility_supported_surface_match:
        consistency_warnings.append("Compatibility supported surface does not match the approved consumer surface.")

    capability_consistent = (
        version_reference_present
        and capability_reference_present
        and compatibility_reference_present
        and consumer_surface_declaration_present
        and supported_surface_match
        and compatibility_supported_surface_match
        and not consistency_warnings
        and not missing_capability_references
    )

    if capability_consistent:
        validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "consistent"
    elif consistency_warnings:
        validation_state = "inconsistent"
    elif missing_capability_references:
        validation_state = "partial"
    else:
        validation_state = "unknown"

    available = bool(
        version_reference_present
        or capability_reference_present
        or compatibility_reference_present
        or consumer_surface_declaration_present
        or capability_supported_surface is not None
        or compatibility_supported_surface is not None
    )
    summary = _summary_text(
        validation_state=validation_state,
        capability_consistent=capability_consistent,
        surface_version_reference=surface_version_reference,
        approved_surface=approved_surface,
        capability_supported_surface=capability_supported_surface,
        compatibility_supported_surface=compatibility_supported_surface,
        missing_capability_references=missing_capability_references,
        consistency_warnings=consistency_warnings,
    )
    return AIResearchContextConsumerCapabilityValidation(
        available=available,
        capability_consistent=capability_consistent,
        validation_state=validation_state,
        surface_version_reference=surface_version_reference,
        surface_version_match=version_reference_present and surface_version_reference == version,
        approved_surface=approved_surface,
        capability_supported_surface=capability_supported_surface or (),
        compatibility_supported_surface=compatibility_supported_surface or (),
        capability_reference=capability_reference or "not available",
        compatibility_reference=compatibility_reference or "not available",
        consumer_surface_declaration=consumer_surface_declaration or "not available",
        capability_reference_present=capability_reference_present,
        compatibility_reference_present=compatibility_reference_present,
        consumer_surface_declaration_present=consumer_surface_declaration_present,
        supported_surface_match=supported_surface_match,
        compatibility_supported_surface_match=compatibility_supported_surface_match,
        missing_capability_references=missing_capability_references,
        consistency_warnings=consistency_warnings,
        summary=summary,
        contract_meta=AIResearchContextConsumerCapabilityValidationContractMeta(surface=surface),
    )


def build_ai_research_context_consumer_capability_validation_markdown(
    capability_validation: AIResearchContextConsumerCapabilityValidation | None,
) -> str:
    if capability_validation is None or not capability_validation.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Capability Validation",
                "",
                "AI research context consumer capability validation is unavailable.",
            ]
        )

    rows = [
        ("Validation state", capability_validation.validation_state),
        ("Capability consistent", "Yes" if capability_validation.capability_consistent else "No"),
        ("Surface version reference", capability_validation.surface_version_reference),
        ("Surface version match", "Yes" if capability_validation.surface_version_match else "No"),
        ("Approved surface", _join_list(capability_validation.approved_surface)),
        (
            "Capability supported surface",
            _join_list(capability_validation.capability_supported_surface),
        ),
        (
            "Compatibility supported surface",
            _join_list(capability_validation.compatibility_supported_surface),
        ),
        ("Capability reference", capability_validation.capability_reference),
        ("Compatibility reference", capability_validation.compatibility_reference),
        (
            "Consumer surface declaration",
            capability_validation.consumer_surface_declaration,
        ),
        (
            "Capability reference present",
            "Yes" if capability_validation.capability_reference_present else "No",
        ),
        (
            "Compatibility reference present",
            "Yes" if capability_validation.compatibility_reference_present else "No",
        ),
        (
            "Consumer surface declaration present",
            "Yes" if capability_validation.consumer_surface_declaration_present else "No",
        ),
        (
            "Supported surface match",
            "Yes" if capability_validation.supported_surface_match else "No",
        ),
        (
            "Compatibility supported surface match",
            "Yes" if capability_validation.compatibility_supported_surface_match else "No",
        ),
        (
            "Missing capability references",
            _join_list(capability_validation.missing_capability_references),
        ),
        ("Consistency warnings", _join_list(capability_validation.consistency_warnings)),
        (
            "Capability validation contract",
            f"{capability_validation.contract_meta.version} / {capability_validation.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Capability Validation",
        "",
        f"*{capability_validation.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _summary_text(
    *,
    validation_state: str,
    capability_consistent: bool,
    surface_version_reference: str,
    approved_surface: tuple[str, ...],
    capability_supported_surface: tuple[str, ...] | None,
    compatibility_supported_surface: tuple[str, ...] | None,
    missing_capability_references: list[str],
    consistency_warnings: list[str],
) -> str:
    return (
        "AI research context consumer capability validation: "
        f"state={validation_state}; "
        f"capability_consistent={'yes' if capability_consistent else 'no'}; "
        f"surface_version_reference={surface_version_reference}; "
        f"approved_surface={_join_list(approved_surface)}; "
        f"capability_supported_surface={_join_list(capability_supported_surface or ())}; "
        f"compatibility_supported_surface={_join_list(compatibility_supported_surface or ())}; "
        f"missing_capability_references={_join_list(tuple(missing_capability_references))}; "
        f"consistency_warnings={_join_list(tuple(consistency_warnings))}"
    )


def _reference_present(value: object | None) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text not in {"not available", "unavailable", "unknown"}


def _join_list(values: tuple[str, ...] | list[str]) -> str:
    if not values:
        return "none"
    return " | ".join(values)

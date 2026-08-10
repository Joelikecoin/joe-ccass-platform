from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_entry_context import (
    AIResearchContextConsumerEntryContext,
    build_ai_research_context_consumer_entry_context,
)
from ccass_core.ai_research_context_consumer_capability_validation import (
    AIResearchContextConsumerCapabilityValidation,
    build_ai_research_context_consumer_capability_validation,
    build_ai_research_context_consumer_capability_validation_markdown,
)
from ccass_core.ai_research_context_delivery import AIResearchContextDelivery
from ccass_core.ai_research_context_historical_delivery import AIResearchContextHistoricalDelivery
from ccass_core.ai_research_context_quality import AIResearchContextQualitySummary

AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_SURFACE = "ai_research_context_consumer_boundary"
AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE = (
    "current_context",
    "historical_context",
    "consumer_context",
    "quality_summary",
)


class AIResearchContextConsumerBoundaryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_SURFACE


class AIResearchContextConsumerBoundaryCompatibilityMetadata(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_SURFACE
    supported_surface: tuple[str, ...] = Field(
        default_factory=lambda: AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE
    )
    evolution_support: str = "additive consumer boundary evolution"
    compatibility_reference: str = (
        "AI research context consumer boundary supports additive consumer evolution."
    )


class AIResearchContextConsumerBoundaryCapabilityMetadata(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_SURFACE
    supported_surface: tuple[str, ...] = Field(
        default_factory=lambda: AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE
    )
    capability_reference: str = (
        "AI research context consumer boundary supports current_context, historical_context, "
        "consumer_context, and quality_summary."
    )
    consumer_surface_declaration: str = (
        "Approved consumer surface exposes current, historical, consumer, and quality views."
    )


class AIResearchContextConsumerBoundary(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    surface_version_reference: str = AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION
    compatibility_metadata: AIResearchContextConsumerBoundaryCompatibilityMetadata = Field(
        default_factory=AIResearchContextConsumerBoundaryCompatibilityMetadata
    )
    capability_metadata: AIResearchContextConsumerBoundaryCapabilityMetadata = Field(
        default_factory=AIResearchContextConsumerBoundaryCapabilityMetadata
    )
    capability_validation: AIResearchContextConsumerCapabilityValidation = Field(
        default_factory=AIResearchContextConsumerCapabilityValidation
    )
    approved_surface: tuple[str, ...] = Field(
        default_factory=lambda: AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE
    )
    current_context: AIResearchContextDelivery | None = None
    historical_context: AIResearchContextHistoricalDelivery | None = None
    consumer_context: AIResearchContextConsumerEntryContext | None = None
    quality_summary: AIResearchContextQualitySummary | None = None
    current_context_visible: bool = False
    historical_context_visible: bool = False
    comparison_visible: bool = False
    timeline_visible: bool = False
    quality_visible: bool = False
    summary_visible: bool = False
    consumer_ready: bool = False
    context_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    current_context_reference: str = "not available"
    historical_context_reference: str = "not available"
    provenance_reference: str = "not available"
    freshness_reference: str = "unavailable"
    warning_summary: str = "0 warning(s)"
    limitation_summary: str = "Consumer boundary is unavailable."
    summary: str = "AI research context consumer boundary is unavailable."
    contract_meta: AIResearchContextConsumerBoundaryContractMeta = Field(
        default_factory=AIResearchContextConsumerBoundaryContractMeta
    )


def build_ai_research_context_consumer_boundary(
    current_context: AIResearchContextDelivery | None,
    historical_context: AIResearchContextHistoricalDelivery | None,
    consumer_context: AIResearchContextConsumerEntryContext | None = None,
    quality_summary: AIResearchContextQualitySummary | None = None,
    *,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_SURFACE,
) -> AIResearchContextConsumerBoundary:
    if consumer_context is None:
        consumer_context = build_ai_research_context_consumer_entry_context(
            current_context,
            historical_context,
        )

    available = any(
        [
            current_context is not None and current_context.available,
            historical_context is not None and historical_context.available,
            consumer_context is not None and consumer_context.available,
        ]
    )
    capability_validation = build_ai_research_context_consumer_capability_validation(
        surface_version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
        approved_surface=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE,
        capability_supported_surface=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE,
        compatibility_supported_surface=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE,
        capability_reference=AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference,
        compatibility_reference=AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference,
        consumer_surface_declaration=AIResearchContextConsumerBoundaryCapabilityMetadata().consumer_surface_declaration,
    )
    if not available:
        return AIResearchContextConsumerBoundary(
            surface_version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
            compatibility_metadata=AIResearchContextConsumerBoundaryCompatibilityMetadata(
                supported_surface=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE
            ),
            capability_metadata=AIResearchContextConsumerBoundaryCapabilityMetadata(
                supported_surface=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE
            ),
            capability_validation=capability_validation,
            approved_surface=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE,
            current_context=current_context,
            historical_context=historical_context,
            consumer_context=consumer_context,
            quality_summary=quality_summary,
            contract_meta=AIResearchContextConsumerBoundaryContractMeta(surface=surface),
        )

    current_context_visible = current_context is not None and current_context.available
    historical_context_visible = historical_context is not None and historical_context.available
    comparison_visible = bool(
        historical_context is not None and historical_context.comparison_visible
    )
    timeline_visible = bool(historical_context is not None and historical_context.timeline_visible)
    quality_visible = bool(quality_summary is not None)
    summary_visible = bool(historical_context is not None and historical_context.summary_visible)
    consumer_ready = bool(quality_summary.consumer_ready if quality_summary is not None else False)
    current_context_reference = (
        current_context.summary if current_context is not None and current_context.available else "not available"
    )
    historical_context_reference = (
        historical_context.summary
        if historical_context is not None and historical_context.available
        else "not available"
    )
    context_state = (
        consumer_context.context_state
        if consumer_context is not None and consumer_context.available
        else _context_state(
            current_context_visible=current_context_visible,
            historical_context_visible=historical_context_visible,
        )
    )
    provenance_reference = (
        current_context.provenance_reference
        if current_context is not None
        else "not available"
    )
    freshness_reference = (
        current_context.freshness_reference if current_context is not None else "unavailable"
    )
    warning_summary = (
        quality_summary.warning_summary
        if quality_summary is not None
        else (current_context.warning_summary if current_context is not None else "0 warning(s)")
    )
    limitation_summary = (
        quality_summary.limitation_summary
        if quality_summary is not None
        else (
            current_context.limitation_summary
            if current_context is not None
            else "Consumer boundary is unavailable."
        )
    )
    summary = _summary_text(
        current_context_visible=current_context_visible,
        historical_context_visible=historical_context_visible,
        comparison_visible=comparison_visible,
        timeline_visible=timeline_visible,
        quality_visible=quality_visible,
        summary_visible=summary_visible,
        consumer_ready=consumer_ready,
        context_state=context_state,
        current_context_reference=current_context_reference,
        historical_context_reference=historical_context_reference,
        provenance_reference=provenance_reference,
        freshness_reference=freshness_reference,
        warning_summary=warning_summary,
        limitation_summary=limitation_summary,
        capability_validation_state=capability_validation.validation_state,
        capability_consistent=capability_validation.capability_consistent,
        capability_missing=len(capability_validation.missing_capability_references),
    )
    return AIResearchContextConsumerBoundary(
        available=True,
        surface_version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
        compatibility_metadata=AIResearchContextConsumerBoundaryCompatibilityMetadata(
            supported_surface=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE
        ),
        capability_metadata=AIResearchContextConsumerBoundaryCapabilityMetadata(
            supported_surface=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE
        ),
        capability_validation=capability_validation,
        approved_surface=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE,
        current_context=current_context,
        historical_context=historical_context,
        consumer_context=consumer_context,
        quality_summary=quality_summary,
        current_context_visible=current_context_visible,
        historical_context_visible=historical_context_visible,
        comparison_visible=comparison_visible,
        timeline_visible=timeline_visible,
        quality_visible=quality_visible,
        summary_visible=summary_visible,
        consumer_ready=consumer_ready,
        context_state=context_state,
        current_context_reference=current_context_reference,
        historical_context_reference=historical_context_reference,
        provenance_reference=provenance_reference,
        freshness_reference=freshness_reference,
        warning_summary=warning_summary,
        limitation_summary=limitation_summary,
        summary=summary,
        contract_meta=AIResearchContextConsumerBoundaryContractMeta(surface=surface),
    )


def build_ai_research_context_consumer_boundary_markdown(
    consumer_boundary: AIResearchContextConsumerBoundary | None,
) -> str:
    if consumer_boundary is None or not consumer_boundary.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Boundary",
                "",
                "AI research context consumer boundary is unavailable.",
            ]
        )

    rows = [
        (
            "Current context visible",
            "Yes" if consumer_boundary.current_context_visible else "No",
        ),
        (
            "Historical context visible",
            "Yes" if consumer_boundary.historical_context_visible else "No",
        ),
        ("Comparison visible", "Yes" if consumer_boundary.comparison_visible else "No"),
        ("Timeline visible", "Yes" if consumer_boundary.timeline_visible else "No"),
        ("Quality visible", "Yes" if consumer_boundary.quality_visible else "No"),
        ("Summary visible", "Yes" if consumer_boundary.summary_visible else "No"),
        ("Surface version reference", consumer_boundary.surface_version_reference),
        (
            "Compatibility reference",
            consumer_boundary.compatibility_metadata.compatibility_reference,
        ),
        (
            "Supported surface",
            _join_list(consumer_boundary.compatibility_metadata.supported_surface),
        ),
        ("Capability validation state", consumer_boundary.capability_validation.validation_state),
        (
            "Capability consistent",
            "Yes" if consumer_boundary.capability_validation.capability_consistent else "No",
        ),
        (
            "Missing capability references",
            _join_list(consumer_boundary.capability_validation.missing_capability_references),
        ),
        (
            "Capability reference",
            consumer_boundary.capability_metadata.capability_reference,
        ),
        (
            "Consumer surface declaration",
            consumer_boundary.capability_metadata.consumer_surface_declaration,
        ),
        ("Approved surface", _join_list(consumer_boundary.approved_surface)),
        ("Consumer ready", "Yes" if consumer_boundary.consumer_ready else "No"),
        ("Context state", consumer_boundary.context_state),
        ("Current context reference", consumer_boundary.current_context_reference),
        ("Historical context reference", consumer_boundary.historical_context_reference),
        ("Provenance reference", consumer_boundary.provenance_reference),
        ("Freshness reference", consumer_boundary.freshness_reference),
        ("Warning summary", consumer_boundary.warning_summary),
        ("Limitation summary", consumer_boundary.limitation_summary),
        (
            "Consumer boundary contract",
            (
                f"{consumer_boundary.contract_meta.version} / "
                f"{consumer_boundary.contract_meta.surface}"
            ),
        ),
    ]
    lines = [
        "### AI Research Context Consumer Boundary",
        "",
        f"*{consumer_boundary.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    if consumer_boundary.consumer_context is not None:
        lines.extend(["", "Consumer entry context summary:"])
        lines.append(f"- {consumer_boundary.consumer_context.summary}")
    if consumer_boundary.quality_summary is not None:
        lines.extend(["", "Quality summary:"])
        lines.extend(
            [
                f"- Overall status: {consumer_boundary.quality_summary.overall_context_status}",
                f"- Availability: {consumer_boundary.quality_summary.availability_summary}",
                f"- Freshness: {consumer_boundary.quality_summary.freshness_summary}",
                f"- Provenance: {consumer_boundary.quality_summary.provenance_summary}",
                f"- Validation: {consumer_boundary.quality_summary.validation_summary}",
                f"- Warning: {consumer_boundary.quality_summary.warning_summary}",
                f"- Limitation: {consumer_boundary.quality_summary.limitation_summary}",
            ]
        )
    if consumer_boundary.capability_validation is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_capability_validation_markdown(
                    consumer_boundary.capability_validation
                ),
            ]
        )
    return "\n".join(lines)


def _context_state(
    *,
    current_context_visible: bool,
    historical_context_visible: bool,
) -> Literal["available", "partial", "unavailable", "unknown"]:
    if current_context_visible and historical_context_visible:
        return "available"
    if current_context_visible or historical_context_visible:
        return "partial"
    return "unavailable"


def _summary_text(
    *,
    current_context_visible: bool,
    historical_context_visible: bool,
    comparison_visible: bool,
    timeline_visible: bool,
    quality_visible: bool,
    summary_visible: bool,
    consumer_ready: bool,
    context_state: Literal["available", "partial", "unavailable", "unknown"],
    current_context_reference: str,
    historical_context_reference: str,
    provenance_reference: str,
    freshness_reference: str,
    warning_summary: str,
    limitation_summary: str,
    capability_validation_state: str,
    capability_consistent: bool,
    capability_missing: int,
) -> str:
    return (
        "AI research context consumer boundary: "
        f"current_context_visible={current_context_visible}; "
        f"historical_context_visible={historical_context_visible}; "
        f"comparison_visible={comparison_visible}; "
        f"timeline_visible={timeline_visible}; "
        f"quality_visible={quality_visible}; "
        f"summary_visible={summary_visible}; "
        f"surface_version_reference={AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION}; "
        f"compatibility_reference={AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference}; "
        f"capability_reference={AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference}; "
        f"capability_validation_state={capability_validation_state}; "
        f"capability_consistent={'yes' if capability_consistent else 'no'}; "
        f"capability_missing={capability_missing}; "
        f"approved_surface={_join_list(AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_APPROVED_SURFACE)}; "
        f"consumer_ready={'ready' if consumer_ready else 'not ready'}; "
        f"context_state={context_state}; "
        f"current_context={current_context_reference}; "
        f"historical_context={historical_context_reference}; "
        f"provenance={provenance_reference}; "
        f"freshness={freshness_reference}; "
        f"warnings={warning_summary}; "
        f"limitations={limitation_summary}"
    )


def _join_list(values: tuple[str, ...] | list[str]) -> str:
    if not values:
        return "none"
    return " | ".join(values)

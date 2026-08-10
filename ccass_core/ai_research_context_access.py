from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_assembly import (
    AIResearchContextAssembly,
    AIResearchContextAssemblyContractMeta,
)
from ccass_core.ai_research_context_audit import (
    AIResearchContextAuditTrail,
    build_ai_research_context_audit_trail,
)
from ccass_core.ai_research_context_consumer import (
    AIResearchContextConsumerView,
    build_ai_research_context_consumer_view,
)
from ccass_core.ai_research_context_quality import AIResearchContextQualitySummary
from ccass_core.ai_research_context_validation import AIResearchContextValidationResult

AI_RESEARCH_CONTEXT_ACCESS_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_ACCESS_SURFACE = "ai_research_context_access"


class AIResearchContextAccessContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_ACCESS_VERSION
    surface: str = AI_RESEARCH_CONTEXT_ACCESS_SURFACE


class AIResearchContextAccess(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    assembly: AIResearchContextAssembly | None = None
    consumer_view: AIResearchContextConsumerView | None = None
    validation: AIResearchContextValidationResult | None = None
    quality_summary: AIResearchContextQualitySummary | None = None
    validation_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    quality_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    consumer_ready: bool = False
    context_available: bool = False
    availability_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    freshness_state: Literal[
        "fresh",
        "cached",
        "stale",
        "partial",
        "unavailable",
        "unknown",
    ] = "unknown"
    audit_trail: AIResearchContextAuditTrail | None = None
    provenance_reference: str = "not available"
    freshness_reference: str = "unavailable"
    warning_summary: str = "0 warning(s)"
    limitation_summary: str = "Consumer access is unavailable."
    usage_steps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str = "AI research context consumer access is unavailable."
    contract_meta: AIResearchContextAccessContractMeta = Field(
        default_factory=AIResearchContextAccessContractMeta
    )


def build_ai_research_context_access(
    assembly: AIResearchContextAssembly | None,
) -> AIResearchContextAccess:
    if assembly is None:
        return AIResearchContextAccess(
            availability_state="unavailable",
            freshness_state="unavailable",
            audit_trail=build_ai_research_context_audit_trail(
                available=False,
                snapshot_id=None,
                previous_snapshot_id=None,
                context_version_reference="not available",
                creation_reference="not available",
                linked_audit_reference="not available",
                provenance_reference="not available",
                governance_reference="unavailable",
                validation_reference="unavailable",
                quality_summary_reference="unavailable",
                warnings_reference="0 warning(s)",
            ),
        )

    consumer_view = build_ai_research_context_consumer_view(assembly)
    validation = consumer_view.validation
    quality_summary = consumer_view.quality_summary
    validation_status = validation.status if validation is not None else "unknown"
    quality_status = (
        quality_summary.overall_context_status if quality_summary is not None else "unknown"
    )
    consumer_ready = bool(
        (validation.consumer_ready if validation is not None else False)
        and (quality_summary.consumer_ready if quality_summary is not None else False)
    )
    availability_state = consumer_view.availability_state
    freshness_state = consumer_view.freshness_state
    snapshot_id, previous_snapshot_id, context_version_reference = _snapshot_identity_reference(
        assembly
    )
    audit_trail = build_ai_research_context_audit_trail(
        available=True,
        snapshot_id=snapshot_id,
        previous_snapshot_id=previous_snapshot_id,
        context_version_reference=context_version_reference,
        creation_reference=(
            f"{assembly.contract_meta.version} / {assembly.contract_meta.surface} -> "
            f"{AI_RESEARCH_CONTEXT_ACCESS_VERSION} / {AI_RESEARCH_CONTEXT_ACCESS_SURFACE}"
        ),
        linked_audit_reference=context_version_reference,
        provenance_reference=consumer_view.provenance_reference,
        governance_reference=assembly.summary,
        validation_reference=validation.summary if validation is not None else "unavailable",
        quality_summary_reference=(
            quality_summary.summary if quality_summary is not None else "unavailable"
        ),
        warnings_reference=consumer_view.warning_summary,
        warnings=consumer_view.warnings,
    )
    summary = _summary_text(
        validation_status=validation_status,
        quality_status=quality_status,
        context_available=consumer_view.context_available,
        availability_state=availability_state,
        freshness_state=freshness_state,
        provenance_reference=consumer_view.provenance_reference,
        freshness_reference=consumer_view.freshness_reference,
        warning_summary=consumer_view.warning_summary,
        limitation_summary=consumer_view.limitation_summary,
        consumer_ready=consumer_ready,
    )
    return AIResearchContextAccess(
        available=True,
        assembly=assembly,
        consumer_view=consumer_view,
        validation=validation,
        quality_summary=quality_summary,
        validation_status=validation_status,
        quality_status=quality_status,
        consumer_ready=consumer_ready,
        context_available=consumer_view.context_available,
        availability_state=availability_state,
        freshness_state=freshness_state,
        audit_trail=audit_trail,
        provenance_reference=consumer_view.provenance_reference,
        freshness_reference=consumer_view.freshness_reference,
        warning_summary=consumer_view.warning_summary,
        limitation_summary=consumer_view.limitation_summary,
        usage_steps=list(consumer_view.usage_steps),
        warnings=list(consumer_view.warnings),
        summary=summary,
        contract_meta=AIResearchContextAccessContractMeta(surface=AI_RESEARCH_CONTEXT_ACCESS_SURFACE),
    )


def _snapshot_identity_reference(
    assembly: AIResearchContextAssembly,
) -> tuple[int | None, int | None, str]:
    read_model = (
        assembly.ai_read_model_consumer_view.read_model
        if assembly.ai_read_model_consumer_view is not None
        else None
    )
    if read_model is None:
        return None, None, "not available"
    history = read_model.history
    snapshot_id = history.snapshot_id
    previous_snapshot_id = (
        history.previous_snapshot.snapshot_id if history.previous_snapshot is not None else None
    )
    context_version_reference = (
        f"{read_model.contract_meta.version} / {read_model.contract_meta.surface}"
    )
    return snapshot_id, previous_snapshot_id, context_version_reference


def _summary_text(
    *,
    validation_status: str,
    quality_status: str,
    context_available: bool,
    availability_state: str,
    freshness_state: str,
    provenance_reference: str,
    freshness_reference: str,
    warning_summary: str,
    limitation_summary: str,
    consumer_ready: bool,
) -> str:
    context_state = "available" if context_available else "unavailable"
    ready_state = "ready" if consumer_ready else "not ready"
    return (
        "AI research context access: "
        f"context={context_state}; "
        f"validation={validation_status}; "
        f"quality={quality_status}; "
        f"availability={availability_state}; "
        f"freshness_state={freshness_state}; "
        f"consumer_ready={ready_state}; "
        f"provenance={provenance_reference}; "
        f"freshness_reference={freshness_reference}; "
        f"warnings={warning_summary}; "
        f"limitations={limitation_summary}"
    )

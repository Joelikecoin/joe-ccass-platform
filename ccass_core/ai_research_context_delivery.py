from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_read_model import AIReadModelIdentity
from ccass_core.ai_research_context_access import (
    AIResearchContextAccess,
    AIResearchContextAccessContractMeta,
    build_ai_research_context_access,
)
from ccass_core.ai_research_context_assembly import (
    AIResearchContextAssembly,
    AIResearchContextAssemblyContractMeta,
)
from ccass_core.ai_research_context_consumer import (
    AIResearchContextConsumerView,
    build_ai_research_context_usage_markdown,
)
from ccass_core.ai_research_context_quality import AIResearchContextQualitySummary
from ccass_core.ai_research_context_validation import AIResearchContextValidationResult

AI_RESEARCH_CONTEXT_DELIVERY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_DELIVERY_SURFACE = "ai_research_context_delivery"


class AIResearchContextDeliveryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_DELIVERY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_DELIVERY_SURFACE


class AIResearchContextDeliveryConsumerMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    identity: AIReadModelIdentity | None = None
    assembly_contract_meta: AIResearchContextAssemblyContractMeta | None = None
    access_contract_meta: AIResearchContextAccessContractMeta | None = None
    assembly_reference: str = "not available"
    access_reference: str = "not available"


class AIResearchContextDelivery(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    assembly: AIResearchContextAssembly | None = None
    access: AIResearchContextAccess | None = None
    consumer_view: AIResearchContextConsumerView | None = None
    validation: AIResearchContextValidationResult | None = None
    quality_summary: AIResearchContextQualitySummary | None = None
    consumer_metadata: AIResearchContextDeliveryConsumerMetadata | None = None
    governance_visible: bool = False
    quality_visible: bool = False
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
    provenance_reference: str = "not available"
    freshness_reference: str = "unavailable"
    warning_summary: str = "0 warning(s)"
    limitation_summary: str = "Delivery is unavailable."
    usage_steps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str = "AI research context delivery is unavailable."
    contract_meta: AIResearchContextDeliveryContractMeta = Field(
        default_factory=AIResearchContextDeliveryContractMeta
    )


def build_ai_research_context_delivery(
    assembly: AIResearchContextAssembly | None,
) -> AIResearchContextDelivery:
    access = build_ai_research_context_access(assembly)
    if not access.available:
        return AIResearchContextDelivery(
            access=access,
            availability_state=access.availability_state,
            freshness_state=access.freshness_state,
            contract_meta=AIResearchContextDeliveryContractMeta(
                surface=AI_RESEARCH_CONTEXT_DELIVERY_SURFACE
            ),
            summary=_summary_text(
                context_available=False,
                availability_state=access.availability_state,
                freshness_state=access.freshness_state,
                governance_visible=False,
                quality_visible=False,
                consumer_ready=False,
                provenance_reference=access.provenance_reference,
                freshness_reference=access.freshness_reference,
                warning_summary=access.warning_summary,
                limitation_summary=access.limitation_summary,
            ),
        )

    consumer_metadata = _consumer_metadata(access)
    governance_visible = bool(access.validation is not None and access.consumer_view is not None)
    quality_visible = access.quality_summary is not None
    summary = _summary_text(
        context_available=access.context_available,
        availability_state=access.availability_state,
        freshness_state=access.freshness_state,
        governance_visible=governance_visible,
        quality_visible=quality_visible,
        consumer_ready=access.consumer_ready,
        provenance_reference=access.provenance_reference,
        freshness_reference=access.freshness_reference,
        warning_summary=access.warning_summary,
        limitation_summary=access.limitation_summary,
    )
    return AIResearchContextDelivery(
        available=True,
        assembly=access.assembly,
        access=access,
        consumer_view=access.consumer_view,
        validation=access.validation,
        quality_summary=access.quality_summary,
        consumer_metadata=consumer_metadata,
        governance_visible=governance_visible,
        quality_visible=quality_visible,
        consumer_ready=access.consumer_ready,
        context_available=access.context_available,
        availability_state=access.availability_state,
        freshness_state=access.freshness_state,
        provenance_reference=access.provenance_reference,
        freshness_reference=access.freshness_reference,
        warning_summary=access.warning_summary,
        limitation_summary=access.limitation_summary,
        usage_steps=list(access.usage_steps),
        warnings=list(access.warnings),
        summary=summary,
        contract_meta=AIResearchContextDeliveryContractMeta(
            surface=AI_RESEARCH_CONTEXT_DELIVERY_SURFACE
        ),
    )


def build_ai_research_context_delivery_markdown(
    delivery: AIResearchContextDelivery | None,
) -> str:
    if delivery is None or not delivery.available:
        return "\n".join(
            [
                "### AI Research Context Delivery",
                "",
                "AI research context delivery is unavailable.",
            ]
        )

    access = delivery.access
    consumer_metadata = delivery.consumer_metadata
    rows = [
        ("Context availability", "available" if delivery.context_available else "unavailable"),
        ("Availability state", delivery.availability_state),
        ("Freshness state", delivery.freshness_state),
        ("Governance visibility", "visible" if delivery.governance_visible else "hidden"),
        ("Quality visibility", "visible" if delivery.quality_visible else "hidden"),
        ("Consumer ready", "Yes" if delivery.consumer_ready else "No"),
        ("Provenance reference", delivery.provenance_reference),
        ("Freshness reference", delivery.freshness_reference),
        ("Warning summary", delivery.warning_summary),
        ("Limitation summary", delivery.limitation_summary),
        (
            "Assembly contract",
            (
                f"{consumer_metadata.assembly_contract_meta.version} / "
                f"{consumer_metadata.assembly_contract_meta.surface}"
                if consumer_metadata is not None and consumer_metadata.assembly_contract_meta is not None
                else "not available"
            ),
        ),
        (
            "Access contract",
            (
                f"{consumer_metadata.access_contract_meta.version} / "
                f"{consumer_metadata.access_contract_meta.surface}"
                if consumer_metadata is not None and consumer_metadata.access_contract_meta is not None
                else "not available"
            ),
        ),
        (
            "Delivery contract",
            f"{delivery.contract_meta.version} / {delivery.contract_meta.surface}",
        ),
    ]
    if consumer_metadata is not None and consumer_metadata.identity is not None:
        rows.insert(0, ("Stock code", consumer_metadata.identity.stock_code))
        rows.insert(1, ("Market", consumer_metadata.identity.market))
        rows.insert(2, ("Company name", consumer_metadata.identity.company_name))
    lines = [
        "### AI Research Context Delivery",
        "",
        f"*{delivery.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    if delivery.usage_steps:
        lines.extend(["", "Delivery steps:"])
        lines.extend(f"- {step}" for step in delivery.usage_steps)
    if access is not None and access.validation is not None:
        lines.extend(["", "Validation warnings:"])
        if access.validation.warnings:
            lines.extend(f"- {warning}" for warning in access.validation.warnings)
        else:
            lines.append("- none")
    if delivery.quality_summary is not None:
        lines.extend(["", "Quality summary:"])
        lines.extend(
            f"- {label}: {value}"
            for label, value in [
                ("Overall status", delivery.quality_summary.overall_context_status),
                ("Availability", delivery.quality_summary.availability_summary),
                ("Freshness", delivery.quality_summary.freshness_summary),
                ("Provenance", delivery.quality_summary.provenance_summary),
                ("Validation", delivery.quality_summary.validation_summary),
                ("Warning", delivery.quality_summary.warning_summary),
                ("Limitation", delivery.quality_summary.limitation_summary),
            ]
        )
    if delivery.warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {warning}" for warning in delivery.warnings)
    return "\n".join(lines)


def _consumer_metadata(
    access: AIResearchContextAccess,
) -> AIResearchContextDeliveryConsumerMetadata:
    assembly = access.assembly
    return AIResearchContextDeliveryConsumerMetadata(
        identity=assembly.identity if assembly is not None else None,
        assembly_contract_meta=assembly.contract_meta if assembly is not None else None,
        access_contract_meta=access.contract_meta,
        assembly_reference=(
            f"{assembly.contract_meta.version} / {assembly.contract_meta.surface}"
            if assembly is not None
            else "not available"
        ),
        access_reference=f"{access.contract_meta.version} / {access.contract_meta.surface}",
    )


def _summary_text(
    *,
    context_available: bool,
    availability_state: str,
    freshness_state: str,
    governance_visible: bool,
    quality_visible: bool,
    consumer_ready: bool,
    provenance_reference: str,
    freshness_reference: str,
    warning_summary: str,
    limitation_summary: str,
) -> str:
    context_state = "available" if context_available else "unavailable"
    governance_state = "visible" if governance_visible else "hidden"
    quality_state = "visible" if quality_visible else "hidden"
    ready_state = "ready" if consumer_ready else "not ready"
    return (
        "AI research context delivery: "
        f"context={context_state}; "
        f"availability={availability_state}; "
        f"freshness_state={freshness_state}; "
        f"governance={governance_state}; "
        f"quality={quality_state}; "
        f"consumer_ready={ready_state}; "
        f"provenance={provenance_reference}; "
        f"freshness_reference={freshness_reference}; "
        f"warnings={warning_summary}; "
        f"limitations={limitation_summary}"
    )

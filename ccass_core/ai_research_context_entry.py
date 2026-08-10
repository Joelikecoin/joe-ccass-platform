from __future__ import annotations

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
from ccass_core.ai_research_context_consumer import AIResearchContextConsumerView
from ccass_core.ai_research_context_delivery import (
    AIResearchContextDelivery,
    AIResearchContextDeliveryContractMeta,
    build_ai_research_context_delivery,
    build_ai_research_context_delivery_markdown,
)
from ccass_core.ai_research_context_quality import AIResearchContextQualitySummary
from ccass_core.ai_research_context_validation import AIResearchContextValidationResult

AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_SURFACE = "ai_research_context_consumer_entry"


class AIResearchContextConsumerEntryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_SURFACE


class AIResearchContextConsumerEntryMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    identity: AIReadModelIdentity | None = None
    assembly_contract_meta: AIResearchContextAssemblyContractMeta | None = None
    access_contract_meta: AIResearchContextAccessContractMeta | None = None
    delivery_contract_meta: AIResearchContextDeliveryContractMeta | None = None
    assembly_reference: str = "not available"
    access_reference: str = "not available"
    delivery_reference: str = "not available"


class AIResearchContextConsumerEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    assembly: AIResearchContextAssembly | None = None
    access: AIResearchContextAccess | None = None
    delivery: AIResearchContextDelivery | None = None
    consumer_view: AIResearchContextConsumerView | None = None
    validation: AIResearchContextValidationResult | None = None
    quality_summary: AIResearchContextQualitySummary | None = None
    consumer_metadata: AIResearchContextConsumerEntryMetadata | None = None
    delivery_markdown: str = "AI research context delivery is unavailable."
    governance_visible: bool = False
    quality_visible: bool = False
    consumer_ready: bool = False
    context_available: bool = False
    provenance_reference: str = "not available"
    freshness_reference: str = "unavailable"
    warning_summary: str = "0 warning(s)"
    limitation_summary: str = "Consumer entry is unavailable."
    usage_steps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str = "AI research context consumer entry is unavailable."
    contract_meta: AIResearchContextConsumerEntryContractMeta = Field(
        default_factory=AIResearchContextConsumerEntryContractMeta
    )


def build_ai_research_context_consumer_entry(
    assembly: AIResearchContextAssembly | None,
) -> AIResearchContextConsumerEntry:
    access = build_ai_research_context_access(assembly)
    delivery = build_ai_research_context_delivery(assembly)
    if not delivery.available:
        return AIResearchContextConsumerEntry(
            access=access,
            delivery=delivery,
            delivery_markdown=build_ai_research_context_delivery_markdown(delivery),
            contract_meta=AIResearchContextConsumerEntryContractMeta(
                surface=AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_SURFACE
            ),
            summary=_summary_text(
                context_available=False,
                governance_visible=False,
                quality_visible=False,
                consumer_ready=False,
                provenance_reference=access.provenance_reference,
                freshness_reference=access.freshness_reference,
                warning_summary=access.warning_summary,
                limitation_summary=access.limitation_summary,
            ),
        )

    consumer_metadata = _consumer_metadata(delivery)
    summary = _summary_text(
        context_available=delivery.context_available,
        governance_visible=delivery.governance_visible,
        quality_visible=delivery.quality_visible,
        consumer_ready=delivery.consumer_ready,
        provenance_reference=delivery.provenance_reference,
        freshness_reference=delivery.freshness_reference,
        warning_summary=delivery.warning_summary,
        limitation_summary=delivery.limitation_summary,
    )
    return AIResearchContextConsumerEntry(
        available=True,
        assembly=delivery.assembly,
        access=access,
        delivery=delivery,
        consumer_view=delivery.consumer_view,
        validation=delivery.validation,
        quality_summary=delivery.quality_summary,
        consumer_metadata=consumer_metadata,
        delivery_markdown=build_ai_research_context_delivery_markdown(delivery),
        governance_visible=delivery.governance_visible,
        quality_visible=delivery.quality_visible,
        consumer_ready=delivery.consumer_ready,
        context_available=delivery.context_available,
        provenance_reference=delivery.provenance_reference,
        freshness_reference=delivery.freshness_reference,
        warning_summary=delivery.warning_summary,
        limitation_summary=delivery.limitation_summary,
        usage_steps=list(delivery.usage_steps),
        warnings=list(delivery.warnings),
        summary=summary,
        contract_meta=AIResearchContextConsumerEntryContractMeta(
            surface=AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_SURFACE
        ),
    )


def build_ai_research_context_consumer_entry_markdown(
    entry: AIResearchContextConsumerEntry | None,
) -> str:
    if entry is None or not entry.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Entry",
                "",
                "AI research context consumer entry is unavailable.",
            ]
        )

    consumer_metadata = entry.consumer_metadata
    rows = [
        ("Context availability", "available" if entry.context_available else "unavailable"),
        ("Governance visibility", "visible" if entry.governance_visible else "hidden"),
        ("Quality visibility", "visible" if entry.quality_visible else "hidden"),
        ("Consumer ready", "Yes" if entry.consumer_ready else "No"),
        ("Provenance reference", entry.provenance_reference),
        ("Freshness reference", entry.freshness_reference),
        ("Warning summary", entry.warning_summary),
        ("Limitation summary", entry.limitation_summary),
        ("Delivery markdown", "available"),
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
            (
                f"{consumer_metadata.delivery_contract_meta.version} / "
                f"{consumer_metadata.delivery_contract_meta.surface}"
                if consumer_metadata is not None and consumer_metadata.delivery_contract_meta is not None
                else "not available"
            ),
        ),
        (
            "Consumer entry contract",
            f"{entry.contract_meta.version} / {entry.contract_meta.surface}",
        ),
    ]
    if consumer_metadata is not None and consumer_metadata.identity is not None:
        rows.insert(0, ("Stock code", consumer_metadata.identity.stock_code))
        rows.insert(1, ("Market", consumer_metadata.identity.market))
        rows.insert(2, ("Company name", consumer_metadata.identity.company_name))

    lines = [
        "### AI Research Context Consumer Entry",
        "",
        f"*{entry.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    if entry.usage_steps:
        lines.extend(["", "Usage steps:"])
        lines.extend(f"- {step}" for step in entry.usage_steps)
    if entry.validation is not None:
        lines.extend(["", "Validation warnings:"])
        if entry.validation.warnings:
            lines.extend(f"- {warning}" for warning in entry.validation.warnings)
        else:
            lines.append("- none")
    if entry.quality_summary is not None:
        lines.extend(["", "Quality summary:"])
        lines.extend(
            f"- {label}: {value}"
            for label, value in [
                ("Overall status", entry.quality_summary.overall_context_status),
                ("Availability", entry.quality_summary.availability_summary),
                ("Freshness", entry.quality_summary.freshness_summary),
                ("Provenance", entry.quality_summary.provenance_summary),
                ("Validation", entry.quality_summary.validation_summary),
                ("Warning", entry.quality_summary.warning_summary),
                ("Limitation", entry.quality_summary.limitation_summary),
            ]
        )
    if entry.warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {warning}" for warning in entry.warnings)
    lines.extend(["", "Delivery output:"])
    lines.append(entry.delivery_markdown)
    return "\n".join(lines)


def _consumer_metadata(
    delivery: AIResearchContextDelivery,
) -> AIResearchContextConsumerEntryMetadata:
    access = delivery.access
    assembly = delivery.assembly
    return AIResearchContextConsumerEntryMetadata(
        identity=delivery.consumer_metadata.identity if delivery.consumer_metadata is not None else None,
        assembly_contract_meta=(
            delivery.consumer_metadata.assembly_contract_meta
            if delivery.consumer_metadata is not None
            else None
        ),
        access_contract_meta=(
            delivery.consumer_metadata.access_contract_meta
            if delivery.consumer_metadata is not None
            else None
        ),
        delivery_contract_meta=delivery.contract_meta,
        assembly_reference=(
            f"{assembly.contract_meta.version} / {assembly.contract_meta.surface}"
            if assembly is not None
            else "not available"
        ),
        access_reference=(
            f"{access.contract_meta.version} / {access.contract_meta.surface}"
            if access is not None
            else "not available"
        ),
        delivery_reference=f"{delivery.contract_meta.version} / {delivery.contract_meta.surface}",
    )


def _summary_text(
    *,
    context_available: bool,
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
        "AI research context consumer entry: "
        f"context={context_state}; "
        f"governance={governance_state}; "
        f"quality={quality_state}; "
        f"consumer_ready={ready_state}; "
        f"provenance={provenance_reference}; "
        f"freshness={freshness_reference}; "
        f"warnings={warning_summary}; "
        f"limitations={limitation_summary}"
    )

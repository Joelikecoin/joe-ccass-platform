from __future__ import annotations

from types import SimpleNamespace
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_read_model import AIReadModelIdentity, AIReadModelSnapshotReference
from ccass_core.ai_research_context_access import (
    AIResearchContextAccess,
    AIResearchContextAccessContractMeta,
    build_ai_research_context_access,
)
from ccass_core.ai_research_context_assembly import (
    AIResearchContextAssembly,
    AIResearchContextAssemblyContractMeta,
)
from ccass_core.ai_research_context_comparison import (
    AIResearchContextComparison,
    build_ai_research_context_comparison,
    build_ai_research_context_comparison_markdown,
)
from ccass_core.ai_research_context_change_summary import (
    AIResearchContextChangeSummary,
    build_ai_research_context_change_summary,
    build_ai_research_context_change_summary_markdown,
)
from ccass_core.ai_research_context_timeline import (
    AIResearchContextTimeline,
    build_ai_research_context_timeline,
    build_ai_research_context_timeline_markdown,
)
from ccass_core.ai_research_context_timeline_summary import (
    AIResearchContextTimelineSummary,
    build_ai_research_context_timeline_summary,
    build_ai_research_context_timeline_summary_markdown,
)
from ccass_core.ai_research_context_historical_query import (
    AIResearchContextHistoricalQuery,
    build_ai_research_context_historical_query,
    build_ai_research_context_historical_query_markdown,
)
from ccass_core.ai_research_context_historical_comparison_query import (
    AIResearchContextHistoricalComparisonQuery,
    build_ai_research_context_historical_comparison_query,
    build_ai_research_context_historical_comparison_query_markdown,
)
from ccass_core.ai_research_context_historical_summary import (
    AIResearchContextHistoricalSummary,
    build_ai_research_context_historical_summary,
    build_ai_research_context_historical_summary_markdown,
)
from ccass_core.ai_research_context_historical_delivery import (
    AIResearchContextHistoricalDelivery,
    build_ai_research_context_historical_delivery,
    build_ai_research_context_historical_delivery_markdown,
)
from ccass_core.ai_research_context_consumer_entry_context import (
    AIResearchContextConsumerEntryContext,
    build_ai_research_context_consumer_entry_context,
    build_ai_research_context_consumer_entry_context_markdown,
)
from ccass_core.ai_research_context_consumer_boundary import (
    AIResearchContextConsumerBoundary,
    build_ai_research_context_consumer_boundary,
    build_ai_research_context_consumer_boundary_markdown,
)
from ccass_core.ai_research_context_consumer_capability_validation import (
    AIResearchContextConsumerCapabilityValidation,
    build_ai_research_context_consumer_capability_validation_markdown,
)
from ccass_core.ai_research_context_consumer_health import (
    AIResearchContextConsumerHealthIndicator,
    build_ai_research_context_consumer_health_indicator_markdown,
)
from ccass_core.ai_research_context_consumer_governance_summary import (
    AIResearchContextConsumerGovernanceSummary,
    build_ai_research_context_consumer_governance_summary_markdown,
)
from ccass_core.ai_research_context_consumer_governance_status import (
    AIResearchContextConsumerGovernanceStatus,
    build_ai_research_context_consumer_governance_status_markdown,
)
from ccass_core.ai_research_context_consumer_governance_validation import (
    AIResearchContextConsumerGovernanceValidation,
    build_ai_research_context_consumer_governance_validation_markdown,
)
from ccass_core.ai_research_context_consumer_readiness import (
    AIResearchContextConsumerReadinessStatus,
    build_ai_research_context_consumer_readiness_status_markdown,
)
from ccass_core.ai_research_context_audit import (
    AIResearchContextAuditTrail,
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
    audit_trail: AIResearchContextAuditTrail | None = None
    comparison: AIResearchContextComparison | None = None
    change_summary: AIResearchContextChangeSummary | None = None
    timeline: AIResearchContextTimeline | None = None
    timeline_summary: AIResearchContextTimelineSummary | None = None
    historical_query: AIResearchContextHistoricalQuery | None = None
    historical_comparison_query: AIResearchContextHistoricalComparisonQuery | None = None
    historical_summary: AIResearchContextHistoricalSummary | None = None
    historical_delivery: AIResearchContextHistoricalDelivery | None = None
    consumer_context: AIResearchContextConsumerEntryContext | None = None
    consumer_boundary: AIResearchContextConsumerBoundary | None = None
    consumer_boundary_capability_validation: AIResearchContextConsumerCapabilityValidation | None = None
    consumer_boundary_readiness_status: AIResearchContextConsumerReadinessStatus | None = None
    consumer_boundary_health_indicator: AIResearchContextConsumerHealthIndicator | None = None
    consumer_boundary_governance_summary: AIResearchContextConsumerGovernanceSummary | None = None
    consumer_boundary_governance_status: AIResearchContextConsumerGovernanceStatus | None = None
    consumer_boundary_governance_validation: AIResearchContextConsumerGovernanceValidation | None = None
    consumer_boundary_version_reference: str = "not available"
    consumer_boundary_compatibility_reference: str = "not available"
    consumer_boundary_capability_reference: str = "not available"
    consumer_boundary_readiness_reference: str = "not available"
    consumer_boundary_health_reference: str = "not available"
    consumer_boundary_governance_reference: str = "not available"
    consumer_boundary_governance_status_reference: str = "not available"
    consumer_boundary_governance_validation_reference: str = "not available"
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
    comparison = _comparison(delivery)
    change_summary = _change_summary(comparison, delivery)
    timeline = _timeline(delivery, comparison, change_summary)
    timeline_summary = build_ai_research_context_timeline_summary(timeline)
    historical_query = build_ai_research_context_historical_query(timeline)
    historical_comparison_query = build_ai_research_context_historical_comparison_query(
        comparison,
        change_summary,
        timeline,
    )
    historical_summary = build_ai_research_context_historical_summary(
        historical_query,
        historical_comparison_query,
        timeline_summary,
        change_summary,
    )
    historical_delivery = build_ai_research_context_historical_delivery(
        historical_summary,
        historical_query,
        historical_comparison_query,
        timeline,
        timeline_summary,
    )
    consumer_context = build_ai_research_context_consumer_entry_context(
        delivery,
        historical_delivery,
    )
    consumer_boundary = build_ai_research_context_consumer_boundary(
        delivery,
        historical_delivery,
        consumer_context,
        delivery.quality_summary if delivery is not None else None,
    )
    if not delivery.available:
        return AIResearchContextConsumerEntry(
            access=access,
            delivery=delivery,
            availability_state=access.availability_state,
            freshness_state=access.freshness_state,
            audit_trail=delivery.audit_trail,
            comparison=comparison,
            change_summary=change_summary,
            timeline=timeline,
            timeline_summary=timeline_summary,
            historical_query=historical_query,
            historical_comparison_query=historical_comparison_query,
            historical_summary=historical_summary,
            historical_delivery=historical_delivery,
            consumer_context=consumer_context,
            consumer_boundary=consumer_boundary,
            consumer_boundary_capability_validation=consumer_boundary.capability_validation
            if consumer_boundary is not None
            else None,
            consumer_boundary_readiness_status=consumer_boundary.readiness_status
            if consumer_boundary is not None
            else None,
            consumer_boundary_health_indicator=consumer_boundary.health_indicator
            if consumer_boundary is not None
            else None,
            consumer_boundary_governance_summary=consumer_boundary.governance_summary
            if consumer_boundary is not None
            else None,
            consumer_boundary_governance_status=consumer_boundary.governance_status
            if consumer_boundary is not None
            else None,
            consumer_boundary_governance_validation=consumer_boundary.governance_validation
            if consumer_boundary is not None
            else None,
            consumer_boundary_version_reference=(
                consumer_boundary.surface_version_reference
                if consumer_boundary is not None
                else "not available"
            ),
            consumer_boundary_compatibility_reference=(
                consumer_boundary.compatibility_metadata.compatibility_reference
                if consumer_boundary is not None
                else "not available"
            ),
            consumer_boundary_capability_reference=(
                consumer_boundary.capability_metadata.capability_reference
                if consumer_boundary is not None
                else "not available"
            ),
            consumer_boundary_readiness_reference=(
                consumer_boundary.readiness_status.readiness_reference
                if consumer_boundary is not None
                else "not available"
            ),
            consumer_boundary_health_reference=(
                consumer_boundary.health_indicator.health_reference
                if consumer_boundary is not None
                else "not available"
            ),
            consumer_boundary_governance_reference=(
                consumer_boundary.governance_summary.governance_reference
                if consumer_boundary is not None
                else "not available"
            ),
            consumer_boundary_governance_status_reference=(
                consumer_boundary.governance_status.governance_reference
                if consumer_boundary is not None
                else "not available"
            ),
            consumer_boundary_governance_validation_reference=(
                consumer_boundary.governance_validation.validation_reference
                if consumer_boundary is not None
                else "not available"
            ),
            delivery_markdown=build_ai_research_context_delivery_markdown(delivery),
            contract_meta=AIResearchContextConsumerEntryContractMeta(
                surface=AI_RESEARCH_CONTEXT_CONSUMER_ENTRY_SURFACE
            ),
            summary=consumer_boundary.summary,
        )

    consumer_metadata = _consumer_metadata(delivery)
    return AIResearchContextConsumerEntry(
        available=True,
        assembly=delivery.assembly,
        access=access,
        delivery=delivery,
        consumer_view=delivery.consumer_view,
        validation=delivery.validation,
        quality_summary=delivery.quality_summary,
        consumer_metadata=consumer_metadata,
        audit_trail=delivery.audit_trail,
        comparison=comparison,
        change_summary=change_summary,
        timeline=timeline,
        timeline_summary=timeline_summary,
        historical_query=historical_query,
        historical_comparison_query=historical_comparison_query,
        historical_summary=historical_summary,
        historical_delivery=historical_delivery,
        consumer_context=consumer_context,
        consumer_boundary=consumer_boundary,
        consumer_boundary_capability_validation=consumer_boundary.capability_validation
        if consumer_boundary is not None
        else None,
        consumer_boundary_readiness_status=consumer_boundary.readiness_status
        if consumer_boundary is not None
        else None,
        consumer_boundary_health_indicator=consumer_boundary.health_indicator
        if consumer_boundary is not None
        else None,
        consumer_boundary_governance_summary=consumer_boundary.governance_summary
        if consumer_boundary is not None
        else None,
        consumer_boundary_governance_status=consumer_boundary.governance_status
        if consumer_boundary is not None
        else None,
        consumer_boundary_governance_validation=consumer_boundary.governance_validation
        if consumer_boundary is not None
        else None,
        consumer_boundary_version_reference=(
            consumer_boundary.surface_version_reference
            if consumer_boundary is not None
            else "not available"
        ),
        consumer_boundary_compatibility_reference=(
            consumer_boundary.compatibility_metadata.compatibility_reference
            if consumer_boundary is not None
            else "not available"
        ),
        consumer_boundary_capability_reference=(
            consumer_boundary.capability_metadata.capability_reference
            if consumer_boundary is not None
            else "not available"
        ),
        consumer_boundary_readiness_reference=(
            consumer_boundary.readiness_status.readiness_reference
            if consumer_boundary is not None
            else "not available"
        ),
        consumer_boundary_health_reference=(
            consumer_boundary.health_indicator.health_reference
            if consumer_boundary is not None
            else "not available"
        ),
        consumer_boundary_governance_reference=(
            consumer_boundary.governance_summary.governance_reference
            if consumer_boundary is not None
            else "not available"
        ),
        consumer_boundary_governance_status_reference=(
            consumer_boundary.governance_status.governance_reference
            if consumer_boundary is not None
            else "not available"
        ),
        consumer_boundary_governance_validation_reference=(
            consumer_boundary.governance_validation.validation_reference
            if consumer_boundary is not None
            else "not available"
        ),
        delivery_markdown=build_ai_research_context_delivery_markdown(delivery),
        governance_visible=delivery.governance_visible,
        quality_visible=delivery.quality_visible,
        consumer_ready=delivery.consumer_ready,
        context_available=delivery.context_available,
        availability_state=delivery.availability_state,
        freshness_state=delivery.freshness_state,
        provenance_reference=delivery.provenance_reference,
        freshness_reference=delivery.freshness_reference,
        warning_summary=delivery.warning_summary,
        limitation_summary=delivery.limitation_summary,
        usage_steps=list(delivery.usage_steps),
        warnings=list(delivery.warnings),
        summary=consumer_boundary.summary,
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
        ("Availability state", entry.availability_state),
        ("Freshness state", entry.freshness_state),
        (
            "Consumer boundary state",
            entry.consumer_boundary.context_state if entry.consumer_boundary is not None else "unavailable",
        ),
        (
            "Consumer boundary capability validation",
            (
                entry.consumer_boundary_capability_validation.summary
                if entry.consumer_boundary_capability_validation is not None
                else "not available"
            ),
        ),
        (
            "Consumer boundary readiness status",
            (
                entry.consumer_boundary_readiness_status.readiness_status
                if entry.consumer_boundary_readiness_status is not None
                else "not available"
            ),
        ),
        ("Consumer boundary readiness reference", entry.consumer_boundary_readiness_reference),
        (
            "Consumer boundary health status",
            (
                entry.consumer_boundary_health_indicator.health_status
                if entry.consumer_boundary_health_indicator is not None
                else "not available"
            ),
        ),
        (
            "Consumer boundary health reference",
            entry.consumer_boundary_health_reference,
        ),
        (
            "Consumer boundary governance status",
            (
                entry.consumer_boundary_governance_status.governance_status
                if entry.consumer_boundary_governance_status is not None
                else "not available"
            ),
        ),
        (
            "Consumer boundary governance status reference",
            entry.consumer_boundary_governance_status_reference,
        ),
        (
            "Consumer boundary governance reference",
            entry.consumer_boundary_governance_reference,
        ),
        (
            "Consumer boundary governance validation state",
            (
                entry.consumer_boundary_governance_validation.validation_state
                if entry.consumer_boundary_governance_validation is not None
                else "not available"
            ),
        ),
        (
            "Consumer boundary governance validation reference",
            entry.consumer_boundary_governance_validation_reference,
        ),
        ("Consumer boundary version reference", entry.consumer_boundary_version_reference),
        (
            "Consumer boundary compatibility reference",
            entry.consumer_boundary_compatibility_reference,
        ),
        (
            "Consumer boundary capability reference",
            entry.consumer_boundary_capability_reference,
        ),
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
    if entry.consumer_boundary is not None:
        lines.extend(["", build_ai_research_context_consumer_boundary_markdown(entry.consumer_boundary)])
    if entry.consumer_boundary_capability_validation is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_capability_validation_markdown(
                    entry.consumer_boundary_capability_validation
                ),
            ]
        )
    if entry.consumer_boundary_readiness_status is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_readiness_status_markdown(
                    entry.consumer_boundary_readiness_status
                ),
            ]
        )
    if entry.consumer_boundary_health_indicator is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_health_indicator_markdown(
                    entry.consumer_boundary_health_indicator
                ),
            ]
        )
    if entry.consumer_boundary_governance_summary is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_summary_markdown(
                    entry.consumer_boundary_governance_summary
                ),
            ]
        )
    if entry.consumer_boundary_governance_status is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_status_markdown(
                    entry.consumer_boundary_governance_status
                ),
            ]
        )
    if entry.consumer_boundary_governance_validation is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_validation_markdown(
                    entry.consumer_boundary_governance_validation
                ),
            ]
        )
    if entry.validation is not None:
        lines.extend(["", "Validation warnings:"])
        if entry.validation.warnings:
            lines.extend(f"- {warning}" for warning in entry.validation.warnings)
        else:
            lines.append("- none")
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
    availability_state: str,
    freshness_state: str,
    comparison_state: str,
    change_summary_state: str,
    timeline_state: str,
    timeline_summary_state: str,
    historical_query_state: str,
    historical_comparison_query_state: str,
    historical_summary_state: str,
    historical_delivery_state: str,
    consumer_context_state: str,
    governance_visible: bool,
    quality_visible: bool,
    consumer_ready: bool,
    health_status: str,
    health_visible: bool,
    provenance_reference: str,
    freshness_reference: str,
    warning_summary: str,
    limitation_summary: str,
    governance_validation_state: str,
    governance_validation_visible: bool,
    governance_status_value: str,
    governance_status_visible: bool,
) -> str:
    context_state = "available" if context_available else "unavailable"
    governance_state = "visible" if governance_visible else "hidden"
    quality_state = "visible" if quality_visible else "hidden"
    ready_state = "ready" if consumer_ready else "not ready"
    return (
        "AI research context consumer entry: "
        f"context={context_state}; "
        f"availability={availability_state}; "
        f"freshness_state={freshness_state}; "
        f"comparison={comparison_state}; "
        f"change_summary={change_summary_state}; "
        f"timeline={timeline_state}; "
        f"timeline_summary={timeline_summary_state}; "
        f"historical_query={historical_query_state}; "
        f"historical_comparison_query={historical_comparison_query_state}; "
        f"historical_summary={historical_summary_state}; "
        f"historical_delivery={historical_delivery_state}; "
        f"consumer_context={consumer_context_state}; "
        f"governance={governance_state}; "
        f"quality={quality_state}; "
        f"consumer_ready={ready_state}; "
        f"health_status={health_status}; "
        f"health_visible={'yes' if health_visible else 'no'}; "
        f"provenance={provenance_reference}; "
        f"freshness_reference={freshness_reference}; "
        f"governance_validation_state={governance_validation_state}; "
        f"governance_validation_visible={'yes' if governance_validation_visible else 'no'}; "
        f"governance_status_value={governance_status_value}; "
        f"governance_status_visible={'yes' if governance_status_visible else 'no'}; "
        f"warnings={warning_summary}; "
        f"limitations={limitation_summary}"
    )


def _comparison(delivery: AIResearchContextDelivery | None) -> AIResearchContextComparison | None:
    if delivery is None or not delivery.available or delivery.assembly is None:
        return build_ai_research_context_comparison(
            current_snapshot_reference=None,
            previous_snapshot_reference=None,
            comparison_metadata=None,
            audit_trail_reference="not available",
            provenance_reference="not available",
            governance_reference="unavailable",
            quality_summary_reference="unavailable",
            warning_summary="0 warning(s)",
        )

    read_model = (
        delivery.assembly.ai_read_model_consumer_view.read_model
        if delivery.assembly.ai_read_model_consumer_view is not None
        else None
    )
    history = read_model.history if read_model is not None else None
    current_snapshot_reference = (
        _current_snapshot_reference(read_model) if read_model is not None else None
    )
    previous_snapshot_reference = history.previous_snapshot if history is not None else None
    comparison_metadata = history.comparison_context if history is not None else None
    audit_trail_reference = (
        delivery.audit_trail.creation_reference if delivery.audit_trail is not None else "not available"
    )
    governance_reference = (
        delivery.consumer_view.governance_summary
        if delivery.consumer_view is not None
        else delivery.limitation_summary
    )
    quality_summary_reference = (
        delivery.quality_summary.summary if delivery.quality_summary is not None else "unavailable"
    )
    return build_ai_research_context_comparison(
        current_snapshot_reference=current_snapshot_reference,
        previous_snapshot_reference=previous_snapshot_reference,
        comparison_metadata=comparison_metadata,
        audit_trail_reference=audit_trail_reference,
        provenance_reference=delivery.provenance_reference,
        governance_reference=governance_reference,
        quality_summary_reference=quality_summary_reference,
        warning_summary=delivery.warning_summary,
    )


def _change_summary(
    comparison: AIResearchContextComparison | None,
    delivery: AIResearchContextDelivery | None,
) -> AIResearchContextChangeSummary | None:
    if delivery is None or not delivery.available:
        return build_ai_research_context_change_summary(
            comparison,
            audit_trail_reference="not available",
            provenance_reference="not available",
            governance_reference="unavailable",
            quality_summary_reference="unavailable",
            warning_summary="0 warning(s)",
        )

    audit_trail_reference = (
        delivery.audit_trail.creation_reference if delivery.audit_trail is not None else "not available"
    )
    governance_reference = (
        delivery.consumer_view.governance_summary
        if delivery.consumer_view is not None
        else delivery.limitation_summary
    )
    quality_summary_reference = (
        delivery.quality_summary.summary if delivery.quality_summary is not None else "unavailable"
    )
    return build_ai_research_context_change_summary(
        comparison,
        audit_trail_reference=audit_trail_reference,
        provenance_reference=delivery.provenance_reference,
        governance_reference=governance_reference,
        quality_summary_reference=quality_summary_reference,
        warning_summary=delivery.warning_summary,
    )


def _timeline(
    delivery: AIResearchContextDelivery | None,
    comparison: AIResearchContextComparison | None,
    change_summary: AIResearchContextChangeSummary | None,
):
    timeline_source = SimpleNamespace(
        available=bool(delivery is not None and delivery.available),
        delivery=delivery,
        comparison=comparison,
        change_summary=change_summary,
        audit_trail=delivery.audit_trail if delivery is not None else None,
        provenance_reference=delivery.provenance_reference if delivery is not None else "not available",
        warning_summary=delivery.warning_summary if delivery is not None else "0 warning(s)",
        consumer_view=delivery.consumer_view if delivery is not None else None,
        quality_summary=delivery.quality_summary if delivery is not None else None,
        limitation_summary=delivery.limitation_summary if delivery is not None else "Consumer entry is unavailable.",
    )
    return build_ai_research_context_timeline(timeline_source)


def _current_snapshot_reference(
    read_model,
) -> AIReadModelSnapshotReference | None:
    if read_model is None:
        return None
    return AIReadModelSnapshotReference(
        snapshot_id=read_model.history.snapshot_id,
        snapshot_date=read_model.timing.data_as_of,
        data_as_of=read_model.timing.data_as_of,
        fetched_at=read_model.timing.fetched_at,
        source=read_model.provenance.source,
    )

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
from ccass_core.ai_research_context_consumer_readiness import (
    AIResearchContextConsumerReadinessStatus,
    build_ai_research_context_consumer_readiness_status,
    build_ai_research_context_consumer_readiness_status_markdown,
)
from ccass_core.ai_research_context_consumer_health import (
    AIResearchContextConsumerHealthIndicator,
    build_ai_research_context_consumer_health_indicator,
    build_ai_research_context_consumer_health_indicator_markdown,
)
from ccass_core.ai_research_context_consumer_governance_summary import (
    AIResearchContextConsumerGovernanceSummary,
    build_ai_research_context_consumer_governance_summary,
    build_ai_research_context_consumer_governance_summary_markdown,
)
from ccass_core.ai_research_context_consumer_governance_validation import (
    AIResearchContextConsumerGovernanceValidation,
    build_ai_research_context_consumer_governance_validation,
    build_ai_research_context_consumer_governance_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_status_validation import (
    AIResearchContextConsumerGovernanceStatusValidation,
    build_ai_research_context_consumer_governance_status_validation,
    build_ai_research_context_consumer_governance_status_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_snapshot_validation import (
    AIResearchContextConsumerGovernanceSnapshotValidation,
    build_ai_research_context_consumer_governance_snapshot_validation,
    build_ai_research_context_consumer_governance_snapshot_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline import (
    AIResearchContextConsumerGovernanceTimeline,
    build_ai_research_context_consumer_governance_timeline,
    build_ai_research_context_consumer_governance_timeline_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_validation import (
    AIResearchContextConsumerGovernanceTimelineValidation,
    build_ai_research_context_consumer_governance_timeline_validation,
    build_ai_research_context_consumer_governance_timeline_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_summary import (
    AIResearchContextConsumerGovernanceTimelineSummary,
    build_ai_research_context_consumer_governance_timeline_summary,
    build_ai_research_context_consumer_governance_timeline_summary_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot import (
    AIResearchContextConsumerGovernanceTimelineSnapshot,
    build_ai_research_context_consumer_governance_timeline_snapshot,
    build_ai_research_context_consumer_governance_timeline_snapshot_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotValidation,
    build_ai_research_context_consumer_governance_timeline_snapshot_validation,
    build_ai_research_context_consumer_governance_timeline_snapshot_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary import (
    AIResearchContextConsumerGovernanceTimelineSnapshotSummary,
    build_ai_research_context_consumer_governance_timeline_snapshot_summary,
    build_ai_research_context_consumer_governance_timeline_snapshot_summary_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation,
    build_ai_research_context_consumer_governance_timeline_snapshot_summary_validation,
    build_ai_research_context_consumer_governance_timeline_snapshot_summary_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation,
    build_ai_research_context_consumer_governance_timeline_snapshot_delivery_validation,
    build_ai_research_context_consumer_governance_timeline_snapshot_delivery_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_summary import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary,
    build_ai_research_context_consumer_governance_timeline_snapshot_delivery_summary,
    build_ai_research_context_consumer_governance_timeline_snapshot_delivery_summary_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_summary_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryValidation,
    build_ai_research_context_consumer_governance_timeline_snapshot_delivery_summary_validation,
    build_ai_research_context_consumer_governance_timeline_snapshot_delivery_summary_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_status import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus,
    build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status,
    build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDelivery,
    build_ai_research_context_consumer_governance_timeline_snapshot_delivery,
    build_ai_research_context_consumer_governance_timeline_snapshot_delivery_markdown,
)
from ccass_core.ai_research_context_consumer_governance_status import (
    AIResearchContextConsumerGovernanceStatus,
    build_ai_research_context_consumer_governance_status,
    build_ai_research_context_consumer_governance_status_markdown,
)
from ccass_core.ai_research_context_consumer_governance_snapshot import (
    AIResearchContextConsumerGovernanceSnapshot,
    build_ai_research_context_consumer_governance_snapshot,
    build_ai_research_context_consumer_governance_snapshot_markdown,
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
    readiness_status: AIResearchContextConsumerReadinessStatus = Field(
        default_factory=AIResearchContextConsumerReadinessStatus
    )
    health_indicator: AIResearchContextConsumerHealthIndicator = Field(
        default_factory=AIResearchContextConsumerHealthIndicator
    )
    governance_summary: AIResearchContextConsumerGovernanceSummary = Field(
        default_factory=AIResearchContextConsumerGovernanceSummary
    )
    governance_validation: AIResearchContextConsumerGovernanceValidation = Field(
        default_factory=AIResearchContextConsumerGovernanceValidation
    )
    governance_status_validation: AIResearchContextConsumerGovernanceStatusValidation = Field(
        default_factory=AIResearchContextConsumerGovernanceStatusValidation
    )
    governance_snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation = Field(
        default_factory=AIResearchContextConsumerGovernanceSnapshotValidation
    )
    governance_timeline: AIResearchContextConsumerGovernanceTimeline = Field(
        default_factory=AIResearchContextConsumerGovernanceTimeline
    )
    governance_timeline_validation: AIResearchContextConsumerGovernanceTimelineValidation = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineValidation
    )
    governance_timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSummary
    )
    governance_timeline_snapshot: AIResearchContextConsumerGovernanceTimelineSnapshot = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshot
    )
    governance_timeline_snapshot_validation: AIResearchContextConsumerGovernanceTimelineSnapshotValidation = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotValidation
    )
    governance_timeline_snapshot_summary: AIResearchContextConsumerGovernanceTimelineSnapshotSummary = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotSummary
    )
    governance_timeline_snapshot_summary_validation: AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation
    )
    governance_timeline_snapshot_delivery_validation: AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation
    )
    governance_timeline_snapshot_delivery_summary: AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary
    )
    governance_timeline_snapshot_delivery_summary_validation: AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryValidation = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryValidation
    )
    governance_timeline_snapshot_delivery_status: AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus
    )
    governance_timeline_snapshot_delivery: AIResearchContextConsumerGovernanceTimelineSnapshotDelivery = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDelivery
    )
    governance_status: AIResearchContextConsumerGovernanceStatus = Field(
        default_factory=AIResearchContextConsumerGovernanceStatus
    )
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot = Field(
        default_factory=AIResearchContextConsumerGovernanceSnapshot
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
    readiness_status = build_ai_research_context_consumer_readiness_status(
        available=available,
        consumer_ready=bool(quality_summary.consumer_ready if quality_summary is not None else False),
        capability_validation=capability_validation,
        capability_reference=AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference,
        compatibility_reference=AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference,
        consumer_surface_declaration=AIResearchContextConsumerBoundaryCapabilityMetadata().consumer_surface_declaration,
        surface_version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
    )
    health_indicator = build_ai_research_context_consumer_health_indicator(
        available=available,
        consumer_ready=bool(quality_summary.consumer_ready if quality_summary is not None else False),
        capability_validation=capability_validation,
        readiness_status=readiness_status,
    )
    governance_summary = build_ai_research_context_consumer_governance_summary(
        available=available,
        version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
        compatibility_reference=AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference,
        capability_reference=AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference,
        capability_validation=capability_validation,
        readiness_status=readiness_status,
        health_indicator=health_indicator,
    )
    governance_validation = build_ai_research_context_consumer_governance_validation(
        available=available,
        governance_summary=governance_summary,
        version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
        compatibility_reference=AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference,
        capability_reference=AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference,
        capability_validation=capability_validation,
        readiness_status=readiness_status,
        health_indicator=health_indicator,
    )
    governance_status = build_ai_research_context_consumer_governance_status(
        available=available,
        version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
        compatibility_reference=AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference,
        capability_reference=AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference,
        capability_validation=capability_validation,
        governance_summary=governance_summary,
        governance_validation=governance_validation,
        readiness_status=readiness_status,
        health_indicator=health_indicator,
    )
    governance_status_validation = build_ai_research_context_consumer_governance_status_validation(
        available=available,
        governance_status=governance_status,
        governance_summary=governance_summary,
        governance_validation=governance_validation,
        version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
        compatibility_reference=AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference,
        capability_reference=AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference,
        capability_validation=capability_validation,
        readiness_status=readiness_status,
        health_indicator=health_indicator,
    )
    governance_snapshot = build_ai_research_context_consumer_governance_snapshot(
        available=available,
        version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
        compatibility_reference=AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference,
        capability_reference=AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference,
        governance_summary=governance_summary,
        governance_status=governance_status,
        governance_status_validation=governance_status_validation,
        readiness_status=readiness_status,
        health_indicator=health_indicator,
    )
    governance_snapshot_validation = build_ai_research_context_consumer_governance_snapshot_validation(
        available=available,
        governance_snapshot=governance_snapshot,
        governance_summary=governance_summary,
        governance_status=governance_status,
        governance_status_validation=governance_status_validation,
        version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
        compatibility_reference=AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference,
        capability_reference=AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference,
        readiness_status=readiness_status,
        health_indicator=health_indicator,
    )
    governance_timeline = build_ai_research_context_consumer_governance_timeline(
        available=available,
        governance_summary=governance_summary,
        governance_status=governance_status,
        governance_status_validation=governance_status_validation,
        governance_snapshot=governance_snapshot,
        governance_snapshot_validation=governance_snapshot_validation,
        version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
        compatibility_reference=AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference,
        capability_reference=AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference,
        readiness_status=readiness_status,
        health_indicator=health_indicator,
    )
    governance_timeline_validation = build_ai_research_context_consumer_governance_timeline_validation(
        available=available,
        governance_timeline=governance_timeline,
        governance_summary=governance_summary,
        governance_status=governance_status,
        governance_status_validation=governance_status_validation,
        governance_snapshot=governance_snapshot,
        governance_snapshot_validation=governance_snapshot_validation,
        version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
        compatibility_reference=AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference,
        capability_reference=AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference,
        readiness_status=readiness_status,
        health_indicator=health_indicator,
    )
    governance_timeline_summary = build_ai_research_context_consumer_governance_timeline_summary(
        available=available,
        governance_timeline=governance_timeline,
        governance_timeline_validation=governance_timeline_validation,
        governance_snapshot=governance_snapshot,
        governance_status=governance_status,
    )
    governance_timeline_snapshot = build_ai_research_context_consumer_governance_timeline_snapshot(
        available=available,
        governance_timeline=governance_timeline,
        governance_timeline_validation=governance_timeline_validation,
        governance_timeline_summary=governance_timeline_summary,
        governance_snapshot=governance_snapshot,
        governance_snapshot_validation=governance_snapshot_validation,
    )
    governance_timeline_snapshot_validation = (
        build_ai_research_context_consumer_governance_timeline_snapshot_validation(
            available=available,
            governance_timeline_snapshot=governance_timeline_snapshot,
            governance_timeline=governance_timeline,
            governance_timeline_validation=governance_timeline_validation,
            governance_timeline_summary=governance_timeline_summary,
            governance_snapshot=governance_snapshot,
            governance_snapshot_validation=governance_snapshot_validation,
            version_reference=AI_RESEARCH_CONTEXT_CONSUMER_BOUNDARY_VERSION,
            compatibility_reference=AIResearchContextConsumerBoundaryCompatibilityMetadata().compatibility_reference,
            capability_reference=AIResearchContextConsumerBoundaryCapabilityMetadata().capability_reference,
            readiness_status=readiness_status,
            health_indicator=health_indicator,
        )
    )
    governance_timeline_snapshot_summary = (
        build_ai_research_context_consumer_governance_timeline_snapshot_summary(
            available=available,
            governance_timeline_snapshot=governance_timeline_snapshot,
            governance_timeline_snapshot_validation=governance_timeline_snapshot_validation,
            governance_timeline_summary=governance_timeline_summary,
            governance_snapshot=governance_snapshot,
            governance_snapshot_validation=governance_snapshot_validation,
        )
    )
    governance_timeline_snapshot_summary_validation = (
        build_ai_research_context_consumer_governance_timeline_snapshot_summary_validation(
            available=available,
            governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
            governance_timeline_snapshot=governance_timeline_snapshot,
            governance_timeline_snapshot_validation=governance_timeline_snapshot_validation,
            governance_timeline_summary=governance_timeline_summary,
            governance_snapshot=governance_snapshot,
            governance_snapshot_validation=governance_snapshot_validation,
        )
    )
    governance_timeline_snapshot_delivery = (
        build_ai_research_context_consumer_governance_timeline_snapshot_delivery(
            available=available,
            governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
            governance_timeline_snapshot_summary_validation=governance_timeline_snapshot_summary_validation,
        )
    )
    governance_timeline_snapshot_delivery_validation = (
        build_ai_research_context_consumer_governance_timeline_snapshot_delivery_validation(
            available=available,
            governance_timeline_snapshot_delivery=governance_timeline_snapshot_delivery,
            governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
            governance_timeline_snapshot_summary_validation=governance_timeline_snapshot_summary_validation,
            governance_timeline_snapshot_validation=governance_timeline_snapshot_validation,
        )
    )
    governance_timeline_snapshot_delivery_summary = (
        build_ai_research_context_consumer_governance_timeline_snapshot_delivery_summary(
            available=available,
            governance_timeline_snapshot_delivery=governance_timeline_snapshot_delivery,
            governance_timeline_snapshot_delivery_validation=governance_timeline_snapshot_delivery_validation,
            governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
            governance_timeline_snapshot_summary_validation=governance_timeline_snapshot_summary_validation,
        )
    )
    governance_timeline_snapshot_delivery_summary_validation = (
        build_ai_research_context_consumer_governance_timeline_snapshot_delivery_summary_validation(
            available=available,
            governance_timeline_snapshot_delivery_summary=governance_timeline_snapshot_delivery_summary,
            governance_timeline_snapshot_delivery=governance_timeline_snapshot_delivery,
            governance_timeline_snapshot_delivery_validation=governance_timeline_snapshot_delivery_validation,
            governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
            governance_timeline_snapshot_summary_validation=governance_timeline_snapshot_summary_validation,
        )
    )
    governance_timeline_snapshot_delivery_status = (
        build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status(
            available=available,
            governance_timeline_snapshot_delivery_summary_validation=governance_timeline_snapshot_delivery_summary_validation,
            governance_timeline_snapshot_delivery_summary=governance_timeline_snapshot_delivery_summary,
            governance_timeline_snapshot_delivery=governance_timeline_snapshot_delivery,
            governance_timeline_snapshot_delivery_validation=governance_timeline_snapshot_delivery_validation,
            governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
            governance_timeline_snapshot_summary_validation=governance_timeline_snapshot_summary_validation,
        )
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
            readiness_status=readiness_status,
            health_indicator=health_indicator,
            governance_summary=governance_summary,
            governance_validation=governance_validation,
            governance_status_validation=governance_status_validation,
            governance_snapshot_validation=governance_snapshot_validation,
            governance_timeline=governance_timeline,
            governance_timeline_validation=governance_timeline_validation,
            governance_timeline_summary=governance_timeline_summary,
            governance_timeline_snapshot=governance_timeline_snapshot,
            governance_timeline_snapshot_validation=governance_timeline_snapshot_validation,
            governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
            governance_timeline_snapshot_summary_validation=governance_timeline_snapshot_summary_validation,
            governance_timeline_snapshot_delivery=governance_timeline_snapshot_delivery,
            governance_timeline_snapshot_delivery_validation=governance_timeline_snapshot_delivery_validation,
            governance_timeline_snapshot_delivery_summary=governance_timeline_snapshot_delivery_summary,
            governance_timeline_snapshot_delivery_summary_validation=governance_timeline_snapshot_delivery_summary_validation,
            governance_timeline_snapshot_delivery_status=governance_timeline_snapshot_delivery_status,
            governance_status=governance_status,
            governance_snapshot=governance_snapshot,
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
        readiness_status=readiness_status.readiness_status,
        readiness_visible=readiness_status.readiness_visible,
        health_status=health_indicator.health_status,
        health_visible=health_indicator.health_visible,
        governance_status=governance_summary.governance_status,
        governance_visible=governance_summary.governance_visible,
        governance_validation_state=governance_validation.validation_state,
        governance_validation_visible=governance_validation.governance_visible,
        governance_status_validation_state=governance_status_validation.validation_state,
        governance_status_validation_visible=governance_status_validation.governance_visible,
        governance_snapshot_validation_state=governance_snapshot_validation.validation_state,
        governance_snapshot_validation_visible=governance_snapshot_validation.governance_snapshot_visible,
        governance_timeline_validation_state=governance_timeline_validation.validation_state,
        governance_timeline_validation_visible=governance_timeline_validation.governance_timeline_visible,
        governance_timeline_summary_state=governance_timeline_summary.governance_timeline_summary_state,
        governance_timeline_summary_visible=governance_timeline_summary.governance_timeline_summary_visible,
        governance_timeline_snapshot_state=governance_timeline_snapshot.governance_timeline_snapshot_state,
        governance_timeline_snapshot_visible=governance_timeline_snapshot.governance_timeline_snapshot_visible,
        governance_timeline_snapshot_validation_state=governance_timeline_snapshot_validation.validation_state,
        governance_timeline_snapshot_validation_visible=governance_timeline_snapshot_validation.governance_timeline_snapshot_visible,
        governance_timeline_snapshot_summary_state=governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_state,
        governance_timeline_snapshot_summary_visible=governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_visible,
        governance_timeline_snapshot_summary_validation_state=governance_timeline_snapshot_summary_validation.validation_state,
        governance_timeline_snapshot_summary_validation_visible=governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_summary_visible,
        governance_timeline_snapshot_delivery_state=governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_state,
        governance_timeline_snapshot_delivery_visible=governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_visible,
        governance_timeline_snapshot_delivery_validation_state=governance_timeline_snapshot_delivery_validation.validation_state,
        governance_timeline_snapshot_delivery_validation_visible=governance_timeline_snapshot_delivery_validation.governance_timeline_snapshot_delivery_visible,
        governance_timeline_snapshot_delivery_summary_state=governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_summary_state,
        governance_timeline_snapshot_delivery_summary_visible=governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_summary_visible,
        governance_timeline_snapshot_delivery_summary_validation_state=governance_timeline_snapshot_delivery_summary_validation.validation_state,
        governance_timeline_snapshot_delivery_summary_validation_visible=governance_timeline_snapshot_delivery_summary_validation.governance_timeline_snapshot_delivery_summary_visible,
        governance_timeline_snapshot_delivery_status_state=governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_state,
        governance_timeline_snapshot_delivery_status_visible=governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_visible,
        governance_timeline_state=governance_timeline.governance_timeline_state,
        governance_timeline_visible=governance_timeline.governance_timeline_visible,
        governance_status_value=governance_status.governance_status,
        governance_status_visible=governance_status.governance_visible,
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
        readiness_status=readiness_status,
        health_indicator=health_indicator,
        governance_summary=governance_summary,
        governance_validation=governance_validation,
        governance_status_validation=governance_status_validation,
        governance_snapshot_validation=governance_snapshot_validation,
        governance_timeline=governance_timeline,
        governance_timeline_validation=governance_timeline_validation,
        governance_timeline_summary=governance_timeline_summary,
        governance_timeline_snapshot=governance_timeline_snapshot,
        governance_timeline_snapshot_validation=governance_timeline_snapshot_validation,
        governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
        governance_timeline_snapshot_summary_validation=governance_timeline_snapshot_summary_validation,
        governance_timeline_snapshot_delivery=governance_timeline_snapshot_delivery,
        governance_timeline_snapshot_delivery_validation=governance_timeline_snapshot_delivery_validation,
        governance_timeline_snapshot_delivery_summary=governance_timeline_snapshot_delivery_summary,
        governance_timeline_snapshot_delivery_summary_validation=governance_timeline_snapshot_delivery_summary_validation,
        governance_timeline_snapshot_delivery_status=governance_timeline_snapshot_delivery_status,
        governance_status=governance_status,
        governance_snapshot=governance_snapshot,
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
        ("Readiness status", consumer_boundary.readiness_status.readiness_status),
        (
            "Readiness visible",
            "Yes" if consumer_boundary.readiness_status.readiness_visible else "No",
        ),
        (
            "Availability indication",
            consumer_boundary.readiness_status.availability_indication,
        ),
        ("Readiness reference", consumer_boundary.readiness_status.readiness_reference),
        ("Health status", consumer_boundary.health_indicator.health_status),
        (
            "Health visible",
            "Yes" if consumer_boundary.health_indicator.health_visible else "No",
        ),
        (
            "Health indication",
            consumer_boundary.health_indicator.availability_indication,
        ),
        ("Health reference", consumer_boundary.health_indicator.health_reference),
        ("Governance status", consumer_boundary.governance_summary.governance_status),
        (
            "Governance visible",
            "Yes" if consumer_boundary.governance_summary.governance_visible else "No",
        ),
        (
            "Governance indication",
            consumer_boundary.governance_summary.availability_indication,
        ),
        ("Governance reference", consumer_boundary.governance_summary.governance_reference),
        ("Governance validation state", consumer_boundary.governance_validation.validation_state),
        (
            "Governance validation visible",
            "Yes" if consumer_boundary.governance_validation.governance_visible else "No",
        ),
        (
            "Governance validation reference",
            consumer_boundary.governance_validation.validation_reference,
        ),
        (
            "Governance status validation state",
            consumer_boundary.governance_status_validation.validation_state,
        ),
        (
            "Governance status validation visible",
            "Yes" if consumer_boundary.governance_status_validation.governance_visible else "No",
        ),
        (
            "Governance status validation reference",
            consumer_boundary.governance_status_validation.validation_reference,
        ),
        (
            "Governance snapshot validation state",
            consumer_boundary.governance_snapshot_validation.validation_state,
        ),
        (
            "Governance snapshot validation visible",
            "Yes" if consumer_boundary.governance_snapshot_validation.governance_snapshot_visible else "No",
        ),
        (
            "Governance snapshot validation reference",
            consumer_boundary.governance_snapshot_validation.validation_reference,
        ),
        (
            "Governance timeline validation state",
            consumer_boundary.governance_timeline_validation.validation_state,
        ),
        (
            "Governance timeline validation visible",
            "Yes" if consumer_boundary.governance_timeline_validation.governance_timeline_visible else "No",
        ),
        (
            "Governance timeline validation reference",
            consumer_boundary.governance_timeline_validation.validation_reference,
        ),
        (
            "Governance timeline summary state",
            consumer_boundary.governance_timeline_summary.governance_timeline_summary_state,
        ),
        (
            "Governance timeline summary visible",
            "Yes" if consumer_boundary.governance_timeline_summary.governance_timeline_summary_visible else "No",
        ),
        (
            "Governance timeline summary reference",
            consumer_boundary.governance_timeline_summary.governance_timeline_summary_reference,
        ),
        (
            "Governance timeline snapshot state",
            consumer_boundary.governance_timeline_snapshot.governance_timeline_snapshot_state,
        ),
        (
            "Governance timeline snapshot visible",
            "Yes" if consumer_boundary.governance_timeline_snapshot.governance_timeline_snapshot_visible else "No",
        ),
        (
            "Governance timeline snapshot reference",
            consumer_boundary.governance_timeline_snapshot.governance_timeline_snapshot_reference,
        ),
        (
            "Governance timeline snapshot validation state",
            consumer_boundary.governance_timeline_snapshot_validation.validation_state,
        ),
        (
            "Governance timeline snapshot validation visible",
            "Yes"
            if consumer_boundary.governance_timeline_snapshot_validation.governance_timeline_snapshot_visible
            else "No",
        ),
        (
            "Governance timeline snapshot validation reference",
            consumer_boundary.governance_timeline_snapshot_validation.validation_reference,
        ),
        (
            "Governance timeline state",
            consumer_boundary.governance_timeline.governance_timeline_state,
        ),
        (
            "Governance timeline visible",
            "Yes" if consumer_boundary.governance_timeline.governance_timeline_visible else "No",
        ),
        (
            "Governance timeline reference",
            consumer_boundary.governance_timeline.governance_timeline_reference,
        ),
        ("Governance snapshot state", consumer_boundary.governance_snapshot.governance_snapshot_state),
        (
            "Governance snapshot visible",
            "Yes" if consumer_boundary.governance_snapshot.governance_snapshot_visible else "No",
        ),
        (
            "Governance snapshot reference",
            consumer_boundary.governance_snapshot.governance_snapshot_reference,
        ),
        (
            "Governance continuity reference",
            consumer_boundary.governance_snapshot.governance_continuity_reference,
        ),
        ("Governance status", consumer_boundary.governance_status.governance_status),
        (
            "Governance status visible",
            "Yes" if consumer_boundary.governance_status.governance_visible else "No",
        ),
        (
            "Governance status reference",
            consumer_boundary.governance_status.governance_reference,
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
    if consumer_boundary.readiness_status is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_readiness_status_markdown(
                    consumer_boundary.readiness_status
                ),
            ]
        )
    if consumer_boundary.health_indicator is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_health_indicator_markdown(
                    consumer_boundary.health_indicator
                ),
            ]
        )
    if consumer_boundary.governance_summary is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_summary_markdown(
                    consumer_boundary.governance_summary
                ),
            ]
        )
    if consumer_boundary.governance_validation is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_validation_markdown(
                    consumer_boundary.governance_validation
                ),
            ]
        )
    if consumer_boundary.governance_status_validation is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_status_validation_markdown(
                    consumer_boundary.governance_status_validation
                ),
            ]
        )
    if consumer_boundary.governance_snapshot_validation is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_snapshot_validation_markdown(
                    consumer_boundary.governance_snapshot_validation
                ),
            ]
        )
    if consumer_boundary.governance_timeline_validation is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_validation_markdown(
                    consumer_boundary.governance_timeline_validation
                ),
            ]
        )
    if consumer_boundary.governance_timeline_summary is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_summary_markdown(
                    consumer_boundary.governance_timeline_summary
                ),
            ]
        )
    if consumer_boundary.governance_timeline_snapshot is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_snapshot_markdown(
                    consumer_boundary.governance_timeline_snapshot
                ),
            ]
        )
    if consumer_boundary.governance_timeline_snapshot_validation is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_snapshot_validation_markdown(
                    consumer_boundary.governance_timeline_snapshot_validation
                ),
            ]
        )
    if consumer_boundary.governance_timeline_snapshot_summary is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_snapshot_summary_markdown(
                    consumer_boundary.governance_timeline_snapshot_summary
                ),
            ]
        )
    if consumer_boundary.governance_timeline_snapshot_summary_validation is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_snapshot_summary_validation_markdown(
                    consumer_boundary.governance_timeline_snapshot_summary_validation
                ),
            ]
        )
    if consumer_boundary.governance_timeline_snapshot_delivery is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_snapshot_delivery_markdown(
                    consumer_boundary.governance_timeline_snapshot_delivery
                ),
            ]
        )
    if consumer_boundary.governance_timeline_snapshot_delivery_validation is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_snapshot_delivery_validation_markdown(
                    consumer_boundary.governance_timeline_snapshot_delivery_validation
                ),
            ]
        )
    if consumer_boundary.governance_timeline_snapshot_delivery_summary is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_snapshot_delivery_summary_markdown(
                    consumer_boundary.governance_timeline_snapshot_delivery_summary
                ),
            ]
        )
    if consumer_boundary.governance_timeline_snapshot_delivery_summary_validation is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_snapshot_delivery_summary_validation_markdown(
                    consumer_boundary.governance_timeline_snapshot_delivery_summary_validation
                ),
            ]
        )
    if consumer_boundary.governance_timeline_snapshot_delivery_status is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status_markdown(
                    consumer_boundary.governance_timeline_snapshot_delivery_status
                ),
            ]
        )
    if consumer_boundary.governance_timeline is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_timeline_markdown(
                    consumer_boundary.governance_timeline
                ),
            ]
        )
    if consumer_boundary.governance_status is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_status_markdown(
                    consumer_boundary.governance_status
                ),
            ]
        )
    if consumer_boundary.governance_snapshot is not None:
        lines.extend(
            [
                "",
                build_ai_research_context_consumer_governance_snapshot_markdown(
                    consumer_boundary.governance_snapshot
                ),
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
    readiness_status: str,
    readiness_visible: bool,
    health_status: str,
    health_visible: bool,
    governance_status: str,
    governance_visible: bool,
    governance_validation_state: str,
    governance_validation_visible: bool,
    governance_status_validation_state: str,
    governance_status_validation_visible: bool,
    governance_snapshot_validation_state: str,
    governance_snapshot_validation_visible: bool,
    governance_timeline_validation_state: str,
    governance_timeline_validation_visible: bool,
    governance_timeline_summary_state: str,
    governance_timeline_summary_visible: bool,
    governance_timeline_snapshot_state: str,
    governance_timeline_snapshot_visible: bool,
    governance_timeline_snapshot_validation_state: str,
    governance_timeline_snapshot_validation_visible: bool,
    governance_timeline_snapshot_summary_state: str,
    governance_timeline_snapshot_summary_visible: bool,
    governance_timeline_snapshot_summary_validation_state: str,
    governance_timeline_snapshot_summary_validation_visible: bool,
    governance_timeline_snapshot_delivery_state: str,
    governance_timeline_snapshot_delivery_visible: bool,
    governance_timeline_snapshot_delivery_validation_state: str,
    governance_timeline_snapshot_delivery_validation_visible: bool,
    governance_timeline_snapshot_delivery_summary_state: str,
    governance_timeline_snapshot_delivery_summary_visible: bool,
    governance_timeline_snapshot_delivery_summary_validation_state: str,
    governance_timeline_snapshot_delivery_summary_validation_visible: bool,
    governance_timeline_snapshot_delivery_status_state: str,
    governance_timeline_snapshot_delivery_status_visible: bool,
    governance_timeline_state: str,
    governance_timeline_visible: bool,
    governance_status_value: str,
    governance_status_visible: bool,
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
        f"readiness_status={readiness_status}; "
        f"readiness_visible={'yes' if readiness_visible else 'no'}; "
        f"health_status={health_status}; "
        f"health_visible={'yes' if health_visible else 'no'}; "
        f"governance_status={governance_status}; "
        f"governance_visible={'yes' if governance_visible else 'no'}; "
        f"governance_validation_state={governance_validation_state}; "
        f"governance_validation_visible={'yes' if governance_validation_visible else 'no'}; "
        f"governance_status_validation_state={governance_status_validation_state}; "
        f"governance_status_validation_visible={'yes' if governance_status_validation_visible else 'no'}; "
        f"governance_snapshot_validation_state={governance_snapshot_validation_state}; "
        f"governance_snapshot_validation_visible={'yes' if governance_snapshot_validation_visible else 'no'}; "
        f"governance_timeline_validation_state={governance_timeline_validation_state}; "
        f"governance_timeline_validation_visible={'yes' if governance_timeline_validation_visible else 'no'}; "
        f"governance_timeline_summary_state={governance_timeline_summary_state}; "
        f"governance_timeline_summary_visible={'yes' if governance_timeline_summary_visible else 'no'}; "
        f"governance_timeline_snapshot_state={governance_timeline_snapshot_state}; "
        f"governance_timeline_snapshot_visible={'yes' if governance_timeline_snapshot_visible else 'no'}; "
        f"governance_timeline_snapshot_validation_state={governance_timeline_snapshot_validation_state}; "
        f"governance_timeline_snapshot_validation_visible={'yes' if governance_timeline_snapshot_validation_visible else 'no'}; "
        f"governance_timeline_snapshot_summary_state={governance_timeline_snapshot_summary_state}; "
        f"governance_timeline_snapshot_summary_visible={'yes' if governance_timeline_snapshot_summary_visible else 'no'}; "
        f"governance_timeline_snapshot_summary_validation_state={governance_timeline_snapshot_summary_validation_state}; "
        f"governance_timeline_snapshot_summary_validation_visible={'yes' if governance_timeline_snapshot_summary_validation_visible else 'no'}; "
        f"governance_timeline_snapshot_delivery_state={governance_timeline_snapshot_delivery_state}; "
        f"governance_timeline_snapshot_delivery_visible={'yes' if governance_timeline_snapshot_delivery_visible else 'no'}; "
        f"governance_timeline_snapshot_delivery_validation_state={governance_timeline_snapshot_delivery_validation_state}; "
        f"governance_timeline_snapshot_delivery_validation_visible={'yes' if governance_timeline_snapshot_delivery_validation_visible else 'no'}; "
        f"governance_timeline_snapshot_delivery_summary_state={governance_timeline_snapshot_delivery_summary_state}; "
        f"governance_timeline_snapshot_delivery_summary_visible={'yes' if governance_timeline_snapshot_delivery_summary_visible else 'no'}; "
        f"governance_timeline_snapshot_delivery_summary_validation_state={governance_timeline_snapshot_delivery_summary_validation_state}; "
        f"governance_timeline_snapshot_delivery_summary_validation_visible={'yes' if governance_timeline_snapshot_delivery_summary_validation_visible else 'no'}; "
        f"governance_timeline_snapshot_delivery_status_state={governance_timeline_snapshot_delivery_status_state}; "
        f"governance_timeline_snapshot_delivery_status_visible={'yes' if governance_timeline_snapshot_delivery_status_visible else 'no'}; "
        f"governance_timeline_state={governance_timeline_state}; "
        f"governance_timeline_visible={'yes' if governance_timeline_visible else 'no'}; "
        f"governance_status_value={governance_status_value}; "
        f"governance_status_visible={'yes' if governance_status_visible else 'no'}; "
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

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDelivery,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_summary import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_summary_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryValidation,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary import (
    AIResearchContextConsumerGovernanceTimelineSnapshotSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot_delivery_status"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusContractMeta(BaseModel):
    version: str = (
        AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_VERSION
    )
    surface: str = (
        AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SURFACE
    )


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_delivery_status_consistent: bool = False
    governance_timeline_snapshot_delivery_status_state: Literal[
        "consistent",
        "partial",
        "inconsistent",
        "unknown",
    ] = "unknown"
    governance_timeline_snapshot_delivery_status_visible: bool = False
    validation_reference: str = "not available"
    governance_timeline_snapshot_delivery_status_reference: str = "not available"
    governance_timeline_snapshot_delivery_summary_reference: str = "not available"
    governance_timeline_snapshot_delivery_summary_visible: bool = False
    governance_timeline_snapshot_delivery_summary_validation_reference: str = "not available"
    governance_timeline_snapshot_delivery_summary_validation_visible: bool = False
    governance_timeline_snapshot_delivery_reference: str = "not available"
    governance_timeline_snapshot_delivery_visible: bool = False
    governance_timeline_snapshot_delivery_validation_reference: str = "not available"
    governance_timeline_snapshot_delivery_validation_visible: bool = False
    governance_timeline_snapshot_summary_reference: str = "not available"
    governance_timeline_snapshot_summary_visible: bool = False
    governance_timeline_snapshot_summary_validation_reference: str = "not available"
    governance_timeline_snapshot_summary_validation_visible: bool = False
    summary: str = (
        "AI research context consumer governance timeline snapshot delivery status is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusContractMeta = (
        Field(default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusContractMeta)
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status(
    *,
    available: bool,
    governance_timeline_snapshot_delivery_summary_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryValidation | None
    ),
    governance_timeline_snapshot_delivery_summary: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary | None
    ),
    governance_timeline_snapshot_delivery: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDelivery | None
    ),
    governance_timeline_snapshot_delivery_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation | None
    ),
    governance_timeline_snapshot_summary: (
        AIResearchContextConsumerGovernanceTimelineSnapshotSummary | None
    ),
    governance_timeline_snapshot_summary_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation | None
    ),
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus:
    delivery_summary_validation_available = bool(
        governance_timeline_snapshot_delivery_summary_validation is not None
        and governance_timeline_snapshot_delivery_summary_validation.available
    )
    delivery_summary_reference = _delivery_summary_reference(
        governance_timeline_snapshot_delivery_summary
    )
    delivery_summary_visible = bool(
        governance_timeline_snapshot_delivery_summary is not None
        and governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_summary_visible
    )
    delivery_summary_validation_reference = _delivery_summary_validation_reference(
        governance_timeline_snapshot_delivery_summary_validation
    )
    delivery_summary_validation_visible = bool(
        governance_timeline_snapshot_delivery_summary_validation is not None
        and governance_timeline_snapshot_delivery_summary_validation.governance_timeline_snapshot_delivery_summary_visible
    )
    delivery_reference = _delivery_reference(governance_timeline_snapshot_delivery)
    delivery_visible = bool(
        governance_timeline_snapshot_delivery is not None
        and governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_visible
    )
    delivery_validation_reference = _delivery_validation_reference(
        governance_timeline_snapshot_delivery_validation
    )
    delivery_validation_visible = bool(
        governance_timeline_snapshot_delivery_validation is not None
        and governance_timeline_snapshot_delivery_validation.governance_timeline_snapshot_delivery_visible
    )
    summary_reference = _summary_reference(governance_timeline_snapshot_summary)
    summary_visible = bool(
        governance_timeline_snapshot_summary is not None
        and governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_visible
    )
    summary_validation_reference = _summary_validation_reference(
        governance_timeline_snapshot_summary_validation
    )
    summary_validation_visible = bool(
        governance_timeline_snapshot_summary_validation is not None
        and governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_summary_visible
    )

    if not available:
        return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus(
            governance_timeline_snapshot_delivery_status_state="unknown",
            governance_timeline_snapshot_delivery_status_visible=False,
            validation_reference="not available",
            governance_timeline_snapshot_delivery_status_reference="not available",
            governance_timeline_snapshot_delivery_summary_reference=delivery_summary_reference,
            governance_timeline_snapshot_delivery_summary_visible=delivery_summary_visible,
            governance_timeline_snapshot_delivery_summary_validation_reference=delivery_summary_validation_reference,
            governance_timeline_snapshot_delivery_summary_validation_visible=delivery_summary_validation_visible,
            governance_timeline_snapshot_delivery_reference=delivery_reference,
            governance_timeline_snapshot_delivery_visible=delivery_visible,
            governance_timeline_snapshot_delivery_validation_reference=delivery_validation_reference,
            governance_timeline_snapshot_delivery_validation_visible=delivery_validation_visible,
            governance_timeline_snapshot_summary_reference=summary_reference,
            governance_timeline_snapshot_summary_visible=summary_visible,
            governance_timeline_snapshot_summary_validation_reference=summary_validation_reference,
            governance_timeline_snapshot_summary_validation_visible=summary_validation_visible,
            summary=(
                "AI research context consumer governance timeline snapshot delivery status is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusContractMeta(
                surface=surface
            ),
        )

    status_state = (
        governance_timeline_snapshot_delivery_summary_validation.validation_state
        if delivery_summary_validation_available
        else "unknown"
    )
    status_visible = (
        governance_timeline_snapshot_delivery_summary_validation.governance_timeline_snapshot_delivery_summary_visible
        if delivery_summary_validation_available
        else False
    )
    status_consistent = bool(
        governance_timeline_snapshot_delivery_summary_validation.governance_timeline_snapshot_delivery_summary_consistent
        if delivery_summary_validation_available
        else False
    )
    status_reference = (
        governance_timeline_snapshot_delivery_summary_validation.validation_reference
        if delivery_summary_validation_available
        else "not available"
    )
    summary = _summary_text(
        status_state=status_state,
        status_visible=status_visible,
        status_reference=status_reference,
        delivery_summary_reference=delivery_summary_reference,
        delivery_summary_visible=delivery_summary_visible,
        delivery_summary_validation_reference=delivery_summary_validation_reference,
        delivery_summary_validation_visible=delivery_summary_validation_visible,
        delivery_reference=delivery_reference,
        delivery_visible=delivery_visible,
        delivery_validation_reference=delivery_validation_reference,
        delivery_validation_visible=delivery_validation_visible,
        summary_reference=summary_reference,
        summary_visible=summary_visible,
        summary_validation_reference=summary_validation_reference,
        summary_validation_visible=summary_validation_visible,
    )
    return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus(
        available=True,
        governance_timeline_snapshot_delivery_status_consistent=status_consistent,
        governance_timeline_snapshot_delivery_status_state=status_state,
        governance_timeline_snapshot_delivery_status_visible=status_visible,
        validation_reference=status_reference,
        governance_timeline_snapshot_delivery_status_reference=status_reference,
        governance_timeline_snapshot_delivery_summary_reference=delivery_summary_reference,
        governance_timeline_snapshot_delivery_summary_visible=delivery_summary_visible,
        governance_timeline_snapshot_delivery_summary_validation_reference=delivery_summary_validation_reference,
        governance_timeline_snapshot_delivery_summary_validation_visible=delivery_summary_validation_visible,
        governance_timeline_snapshot_delivery_reference=delivery_reference,
        governance_timeline_snapshot_delivery_visible=delivery_visible,
        governance_timeline_snapshot_delivery_validation_reference=delivery_validation_reference,
        governance_timeline_snapshot_delivery_validation_visible=delivery_validation_visible,
        governance_timeline_snapshot_summary_reference=summary_reference,
        governance_timeline_snapshot_summary_visible=summary_visible,
        governance_timeline_snapshot_summary_validation_reference=summary_validation_reference,
        governance_timeline_snapshot_summary_validation_visible=summary_validation_visible,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status_markdown(
    governance_timeline_snapshot_delivery_status: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus | None
    ),
) -> str:
    if (
        governance_timeline_snapshot_delivery_status is None
        or not governance_timeline_snapshot_delivery_status.available
    ):
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot Delivery Status",
                "",
                "AI research context consumer governance timeline snapshot delivery status is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline snapshot delivery status consistent",
            "Yes"
            if governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_consistent
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status state",
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_state,
        ),
        (
            "Governance timeline snapshot delivery status visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status reference",
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_reference,
        ),
        (
            "Governance timeline snapshot delivery summary reference",
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_summary_reference,
        ),
        (
            "Governance timeline snapshot delivery summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery summary validation reference",
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_summary_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery reference",
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_reference,
        ),
        (
            "Governance timeline snapshot delivery visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery validation reference",
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary reference",
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_summary_reference,
        ),
        (
            "Governance timeline snapshot summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary validation reference",
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_summary_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status contract",
            f"{governance_timeline_snapshot_delivery_status.contract_meta.version} / {governance_timeline_snapshot_delivery_status.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot Delivery Status",
        "",
        f"*{governance_timeline_snapshot_delivery_status.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _summary_text(
    *,
    status_state: str,
    status_visible: bool,
    status_reference: str,
    delivery_summary_reference: str,
    delivery_summary_visible: bool,
    delivery_summary_validation_reference: str,
    delivery_summary_validation_visible: bool,
    delivery_reference: str,
    delivery_visible: bool,
    delivery_validation_reference: str,
    delivery_validation_visible: bool,
    summary_reference: str,
    summary_visible: bool,
    summary_validation_reference: str,
    summary_validation_visible: bool,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot delivery status: "
        f"state={status_state}; "
        f"visible={'yes' if status_visible else 'no'}; "
        "scope=timeline_snapshot_delivery_status"
    )


def _delivery_summary_reference(
    governance_timeline_snapshot_delivery_summary: AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary | None,
) -> str:
    if governance_timeline_snapshot_delivery_summary is None:
        return "not available"
    return (
        governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_summary_reference
    )


def _delivery_summary_validation_reference(
    governance_timeline_snapshot_delivery_summary_validation: AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryValidation | None,
) -> str:
    if governance_timeline_snapshot_delivery_summary_validation is None:
        return "not available"
    return governance_timeline_snapshot_delivery_summary_validation.validation_reference


def _delivery_reference(
    governance_timeline_snapshot_delivery: AIResearchContextConsumerGovernanceTimelineSnapshotDelivery | None,
) -> str:
    if governance_timeline_snapshot_delivery is None:
        return "not available"
    return governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_reference


def _delivery_validation_reference(
    governance_timeline_snapshot_delivery_validation: AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation | None,
) -> str:
    if governance_timeline_snapshot_delivery_validation is None:
        return "not available"
    return governance_timeline_snapshot_delivery_validation.validation_reference


def _summary_reference(
    governance_timeline_snapshot_summary: AIResearchContextConsumerGovernanceTimelineSnapshotSummary | None,
) -> str:
    if governance_timeline_snapshot_summary is None:
        return "not available"
    return governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_reference


def _summary_validation_reference(
    governance_timeline_snapshot_summary_validation: AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation | None,
) -> str:
    if governance_timeline_snapshot_summary_validation is None:
        return "not available"
    return governance_timeline_snapshot_summary_validation.validation_reference

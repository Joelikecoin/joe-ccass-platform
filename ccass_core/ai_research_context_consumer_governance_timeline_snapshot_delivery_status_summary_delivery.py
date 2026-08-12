from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_status_summary import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_status_summary_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidation,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_DELIVERY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_DELIVERY_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot_delivery_status_summary_delivery"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryDeliveryContractMeta(BaseModel):
    version: str = (
        AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_DELIVERY_VERSION
    )
    surface: str = (
        AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_DELIVERY_SURFACE
    )


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryDelivery(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_delivery_status_summary_delivery_state: Literal[
        "complete",
        "partial",
        "unavailable",
        "unknown",
    ] = "unknown"
    governance_timeline_snapshot_delivery_status_summary_delivery_visible: bool = False
    governance_timeline_snapshot_delivery_status_summary_delivery_reference: str = "not available"
    governance_timeline_snapshot_delivery_status_summary_reference: str = "not available"
    governance_timeline_snapshot_delivery_status_summary_visible: bool = False
    governance_timeline_snapshot_delivery_status_summary_validation_reference: str = "not available"
    governance_timeline_snapshot_delivery_status_summary_validation_visible: bool = False
    governance_timeline_snapshot_delivery_status_summary: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummary | None
    ) = None
    governance_timeline_snapshot_delivery_status_summary_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidation | None
    ) = None
    summary: str = (
        "AI research context consumer governance timeline snapshot delivery status summary delivery is unavailable."
    )
    governance_timeline_snapshot_delivery_status_summary_delivery: str = (
        "AI research context consumer governance timeline snapshot delivery status summary delivery is unavailable."
    )
    contract_meta: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryDeliveryContractMeta
    ) = Field(
        default_factory=(
            AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryDeliveryContractMeta
        )
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status_summary_delivery(
    *,
    available: bool,
    governance_timeline_snapshot_delivery_status_summary: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummary | None
    ),
    governance_timeline_snapshot_delivery_status_summary_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidation | None
    ),
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_DELIVERY_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryDelivery:
    summary_available = bool(
        governance_timeline_snapshot_delivery_status_summary is not None
        and governance_timeline_snapshot_delivery_status_summary.available
    )
    summary_validation_available = bool(
        governance_timeline_snapshot_delivery_status_summary_validation is not None
        and governance_timeline_snapshot_delivery_status_summary_validation.available
    )
    summary_reference = _summary_reference(
        governance_timeline_snapshot_delivery_status_summary
    )
    summary_visible = bool(
        governance_timeline_snapshot_delivery_status_summary is not None
        and governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_summary_visible
    )
    summary_validation_reference = _summary_validation_reference(
        governance_timeline_snapshot_delivery_status_summary_validation
    )
    summary_validation_visible = bool(
        governance_timeline_snapshot_delivery_status_summary_validation is not None
        and governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_status_summary_visible
    )

    if not available:
        return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryDelivery(
            governance_timeline_snapshot_delivery_status_summary=governance_timeline_snapshot_delivery_status_summary,
            governance_timeline_snapshot_delivery_status_summary_validation=governance_timeline_snapshot_delivery_status_summary_validation,
            governance_timeline_snapshot_delivery_status_summary_delivery_state="unavailable",
            governance_timeline_snapshot_delivery_status_summary_delivery_visible=False,
            governance_timeline_snapshot_delivery_status_summary_delivery_reference="not available",
            governance_timeline_snapshot_delivery_status_summary_reference=summary_reference,
            governance_timeline_snapshot_delivery_status_summary_visible=summary_visible,
            governance_timeline_snapshot_delivery_status_summary_validation_reference=summary_validation_reference,
            governance_timeline_snapshot_delivery_status_summary_validation_visible=summary_validation_visible,
            summary="AI research context consumer governance timeline snapshot delivery status summary delivery is unavailable.",
            governance_timeline_snapshot_delivery_status_summary_delivery=(
                "AI research context consumer governance timeline snapshot delivery status summary delivery is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryDeliveryContractMeta(
                surface=surface
            ),
        )

    delivery_state = _delivery_state(
        summary_available=summary_available,
        summary_validation_available=summary_validation_available,
        summary_validation_consistent=bool(
            governance_timeline_snapshot_delivery_status_summary_validation is not None
            and governance_timeline_snapshot_delivery_status_summary_validation.validation_state
            == "consistent"
        ),
        summary_visible=summary_visible,
        summary_validation_visible=summary_validation_visible,
    )
    delivery_visible = delivery_state in {"complete", "partial"}
    delivery_reference = _delivery_reference(
        delivery_state=delivery_state,
        summary_reference=summary_reference,
        summary_validation_reference=summary_validation_reference,
    )
    summary = _summary_text(
        delivery_state=delivery_state,
        delivery_visible=delivery_visible,
        delivery_reference=delivery_reference,
        summary_reference=summary_reference,
        summary_visible=summary_visible,
        summary_validation_reference=summary_validation_reference,
        summary_validation_visible=summary_validation_visible,
    )
    return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryDelivery(
        available=True,
        governance_timeline_snapshot_delivery_status_summary_delivery_state=delivery_state,
        governance_timeline_snapshot_delivery_status_summary_delivery_visible=delivery_visible,
        governance_timeline_snapshot_delivery_status_summary_delivery_reference=delivery_reference,
        governance_timeline_snapshot_delivery_status_summary_reference=summary_reference,
        governance_timeline_snapshot_delivery_status_summary_visible=summary_visible,
        governance_timeline_snapshot_delivery_status_summary_validation_reference=summary_validation_reference,
        governance_timeline_snapshot_delivery_status_summary_validation_visible=summary_validation_visible,
        governance_timeline_snapshot_delivery_status_summary=governance_timeline_snapshot_delivery_status_summary,
        governance_timeline_snapshot_delivery_status_summary_validation=governance_timeline_snapshot_delivery_status_summary_validation,
        summary=summary,
        governance_timeline_snapshot_delivery_status_summary_delivery=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryDeliveryContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status_summary_delivery_markdown(
    governance_timeline_snapshot_delivery_status_summary_delivery: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryDelivery | None
    ),
) -> str:
    if (
        governance_timeline_snapshot_delivery_status_summary_delivery is None
        or not governance_timeline_snapshot_delivery_status_summary_delivery.available
    ):
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot Delivery Status Summary Delivery",
                "",
                "AI research context consumer governance timeline snapshot delivery status summary delivery is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline snapshot delivery status summary delivery state",
            governance_timeline_snapshot_delivery_status_summary_delivery.governance_timeline_snapshot_delivery_status_summary_delivery_state,
        ),
        (
            "Governance timeline snapshot delivery status summary delivery visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_delivery.governance_timeline_snapshot_delivery_status_summary_delivery_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status summary delivery reference",
            governance_timeline_snapshot_delivery_status_summary_delivery.governance_timeline_snapshot_delivery_status_summary_delivery_reference,
        ),
        (
            "Governance timeline snapshot delivery status summary reference",
            governance_timeline_snapshot_delivery_status_summary_delivery.governance_timeline_snapshot_delivery_status_summary_reference,
        ),
        (
            "Governance timeline snapshot delivery status summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_delivery.governance_timeline_snapshot_delivery_status_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status summary validation reference",
            governance_timeline_snapshot_delivery_status_summary_delivery.governance_timeline_snapshot_delivery_status_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery status summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_delivery.governance_timeline_snapshot_delivery_status_summary_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status summary delivery contract",
            f"{governance_timeline_snapshot_delivery_status_summary_delivery.contract_meta.version} / {governance_timeline_snapshot_delivery_status_summary_delivery.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot Delivery Status Summary Delivery",
        "",
        f"*{governance_timeline_snapshot_delivery_status_summary_delivery.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _delivery_state(
    *,
    summary_available: bool,
    summary_validation_available: bool,
    summary_validation_consistent: bool,
    summary_visible: bool,
    summary_validation_visible: bool,
) -> Literal["complete", "partial", "unavailable", "unknown"]:
    if summary_available and summary_validation_available:
        if summary_validation_consistent and summary_visible and summary_validation_visible:
            return "complete"
        return "partial"
    if summary_available or summary_validation_available:
        return "partial"
    return "unknown"


def _delivery_reference(
    *,
    delivery_state: Literal["complete", "partial", "unavailable", "unknown"],
    summary_reference: str,
    summary_validation_reference: str,
) -> str:
    if delivery_state == "unavailable":
        return "not available"
    return (
        f"state={delivery_state}; "
        f"summary={summary_reference}; "
        f"summary_validation={summary_validation_reference}"
    )


def _summary_reference(
    governance_timeline_snapshot_delivery_status_summary: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummary | None
    ),
) -> str:
    if governance_timeline_snapshot_delivery_status_summary is None:
        return "not available"
    return (
        governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_summary_reference
    )


def _summary_validation_reference(
    governance_timeline_snapshot_delivery_status_summary_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidation | None
    ),
) -> str:
    if governance_timeline_snapshot_delivery_status_summary_validation is None:
        return "not available"
    return governance_timeline_snapshot_delivery_status_summary_validation.validation_reference


def _summary_text(
    *,
    delivery_state: str,
    delivery_visible: bool,
    delivery_reference: str,
    summary_reference: str,
    summary_visible: bool,
    summary_validation_reference: str,
    summary_validation_visible: bool,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot delivery status summary delivery: "
        f"state={delivery_state}; "
        f"visible={'yes' if delivery_visible else 'no'}; "
        f"reference={delivery_reference}; "
        f"summary_reference={summary_reference}; "
        f"summary_visible={'yes' if summary_visible else 'no'}; "
        f"summary_validation_reference={summary_validation_reference}; "
        f"summary_validation_visible={'yes' if summary_validation_visible else 'no'}"
    )

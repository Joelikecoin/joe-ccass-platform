from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary import (
    AIResearchContextConsumerGovernanceTimelineSnapshotSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot_delivery"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_SURFACE


class AIResearchContextConsumerGovernanceTimelineSnapshotDelivery(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_summary: (
        AIResearchContextConsumerGovernanceTimelineSnapshotSummary | None
    ) = None
    governance_timeline_snapshot_summary_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation | None
    ) = None
    governance_timeline_snapshot_delivery_state: Literal[
        "complete",
        "partial",
        "unavailable",
        "unknown",
    ] = "unknown"
    governance_timeline_snapshot_delivery_visible: bool = False
    governance_timeline_snapshot_delivery_reference: str = "not available"
    governance_timeline_snapshot_summary_reference: str = "not available"
    governance_timeline_snapshot_summary_visible: bool = False
    governance_timeline_snapshot_summary_validation_reference: str = "not available"
    governance_timeline_snapshot_summary_validation_visible: bool = False
    summary: str = (
        "AI research context consumer governance timeline snapshot delivery is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryContractMeta
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery(
    *,
    available: bool,
    governance_timeline_snapshot_summary: AIResearchContextConsumerGovernanceTimelineSnapshotSummary | None,
    governance_timeline_snapshot_summary_validation: AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshotDelivery:
    summary_available = bool(
        governance_timeline_snapshot_summary is not None
        and governance_timeline_snapshot_summary.available
    )
    summary_validation_available = bool(
        governance_timeline_snapshot_summary_validation is not None
        and governance_timeline_snapshot_summary_validation.available
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
        return AIResearchContextConsumerGovernanceTimelineSnapshotDelivery(
            governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
            governance_timeline_snapshot_summary_validation=governance_timeline_snapshot_summary_validation,
            governance_timeline_snapshot_delivery_state="unavailable",
            governance_timeline_snapshot_delivery_visible=False,
            governance_timeline_snapshot_delivery_reference="not available",
            governance_timeline_snapshot_summary_reference=summary_reference,
            governance_timeline_snapshot_summary_visible=summary_visible,
            governance_timeline_snapshot_summary_validation_reference=summary_validation_reference,
            governance_timeline_snapshot_summary_validation_visible=summary_validation_visible,
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryContractMeta(
                surface=surface
            ),
        )

    delivery_state = _delivery_state(
        summary_available=summary_available,
        summary_validation_available=summary_validation_available,
        governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
        governance_timeline_snapshot_summary_validation=governance_timeline_snapshot_summary_validation,
    )
    delivery_visible = delivery_state in {"complete", "partial"}
    delivery_reference = _delivery_reference(
        delivery_state=delivery_state,
        governance_timeline_snapshot_summary_reference=summary_reference,
        governance_timeline_snapshot_summary_validation_reference=summary_validation_reference,
    )
    summary = _summary_text(
        delivery_state=delivery_state,
        delivery_visible=delivery_visible,
        delivery_reference=delivery_reference,
        governance_timeline_snapshot_summary_reference=summary_reference,
        governance_timeline_snapshot_summary_visible=summary_visible,
        governance_timeline_snapshot_summary_validation_reference=summary_validation_reference,
        governance_timeline_snapshot_summary_validation_visible=summary_validation_visible,
    )
    return AIResearchContextConsumerGovernanceTimelineSnapshotDelivery(
        available=True,
        governance_timeline_snapshot_summary=governance_timeline_snapshot_summary,
        governance_timeline_snapshot_summary_validation=governance_timeline_snapshot_summary_validation,
        governance_timeline_snapshot_delivery_state=delivery_state,
        governance_timeline_snapshot_delivery_visible=delivery_visible,
        governance_timeline_snapshot_delivery_reference=delivery_reference,
        governance_timeline_snapshot_summary_reference=summary_reference,
        governance_timeline_snapshot_summary_visible=summary_visible,
        governance_timeline_snapshot_summary_validation_reference=summary_validation_reference,
        governance_timeline_snapshot_summary_validation_visible=summary_validation_visible,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_markdown(
    governance_timeline_snapshot_delivery: AIResearchContextConsumerGovernanceTimelineSnapshotDelivery | None,
) -> str:
    if (
        governance_timeline_snapshot_delivery is None
        or not governance_timeline_snapshot_delivery.available
    ):
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot Delivery",
                "",
                "AI research context consumer governance timeline snapshot delivery is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline snapshot delivery state",
            governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_state,
        ),
        (
            "Governance timeline snapshot delivery visible",
            "Yes"
            if governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery reference",
            governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_reference,
        ),
        (
            "Governance timeline snapshot summary reference",
            governance_timeline_snapshot_delivery.governance_timeline_snapshot_summary_reference,
        ),
        (
            "Governance timeline snapshot summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery.governance_timeline_snapshot_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary validation reference",
            governance_timeline_snapshot_delivery.governance_timeline_snapshot_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery.governance_timeline_snapshot_summary_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery contract",
            f"{governance_timeline_snapshot_delivery.contract_meta.version} / {governance_timeline_snapshot_delivery.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot Delivery",
        "",
        f"*{governance_timeline_snapshot_delivery.summary}*",
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
    governance_timeline_snapshot_summary: AIResearchContextConsumerGovernanceTimelineSnapshotSummary | None,
    governance_timeline_snapshot_summary_validation: AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation | None,
) -> Literal["complete", "partial", "unavailable", "unknown"]:
    states = [summary_available, summary_validation_available]
    if all(states):
        summary_validation_consistent = bool(
            governance_timeline_snapshot_summary_validation is not None
            and governance_timeline_snapshot_summary_validation.validation_state == "consistent"
        )
        summary_visible = bool(
            governance_timeline_snapshot_summary is not None
            and governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_visible
        )
        validation_visible = bool(
            governance_timeline_snapshot_summary_validation is not None
            and governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_summary_visible
        )
        if summary_validation_consistent and summary_visible and validation_visible:
            return "complete"
        return "partial"
    if any(states):
        return "partial"
    return "unknown"


def _delivery_reference(
    *,
    delivery_state: Literal["complete", "partial", "unavailable", "unknown"],
    governance_timeline_snapshot_summary_reference: str,
    governance_timeline_snapshot_summary_validation_reference: str,
) -> str:
    if delivery_state == "unavailable":
        return "not available"
    return (
        f"state={delivery_state}; "
        f"summary={governance_timeline_snapshot_summary_reference}; "
        f"validation={governance_timeline_snapshot_summary_validation_reference}"
    )


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
    return (
        governance_timeline_snapshot_summary_validation.validation_reference
    )


def _summary_text(
    *,
    delivery_state: Literal["complete", "partial", "unavailable", "unknown"],
    delivery_visible: bool,
    delivery_reference: str,
    governance_timeline_snapshot_summary_reference: str,
    governance_timeline_snapshot_summary_visible: bool,
    governance_timeline_snapshot_summary_validation_reference: str,
    governance_timeline_snapshot_summary_validation_visible: bool,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot delivery: "
        f"state={delivery_state}; "
        f"visible={'yes' if delivery_visible else 'no'}; "
        f"reference={delivery_reference}; "
        f"summary_reference={governance_timeline_snapshot_summary_reference}; "
        f"summary_visible={'yes' if governance_timeline_snapshot_summary_visible else 'no'}; "
        f"validation_reference={governance_timeline_snapshot_summary_validation_reference}; "
        f"validation_visible={'yes' if governance_timeline_snapshot_summary_validation_visible else 'no'}"
    )

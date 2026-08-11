from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDelivery,
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

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_SUMMARY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_SUMMARY_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot_delivery_summary"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_SUMMARY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_SUMMARY_SURFACE


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_delivery_summary_state: Literal[
        "complete",
        "partial",
        "unavailable",
        "unknown",
    ] = "unknown"
    governance_timeline_snapshot_delivery_summary_visible: bool = False
    governance_timeline_snapshot_delivery_summary_reference: str = "not available"
    governance_timeline_snapshot_delivery_reference: str = "not available"
    governance_timeline_snapshot_delivery_visible: bool = False
    governance_timeline_snapshot_delivery_validation_reference: str = "not available"
    governance_timeline_snapshot_delivery_validation_visible: bool = False
    governance_timeline_snapshot_summary_reference: str = "not available"
    governance_timeline_snapshot_summary_visible: bool = False
    governance_timeline_snapshot_summary_validation_reference: str = "not available"
    governance_timeline_snapshot_summary_validation_visible: bool = False
    summary: str = (
        "AI research context consumer governance timeline snapshot delivery summary is unavailable."
    )
    governance_timeline_snapshot_delivery_summary: str = (
        "AI research context consumer governance timeline snapshot delivery summary is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryContractMeta
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_summary(
    *,
    available: bool,
    governance_timeline_snapshot_delivery: AIResearchContextConsumerGovernanceTimelineSnapshotDelivery | None,
    governance_timeline_snapshot_delivery_validation: AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation | None,
    governance_timeline_snapshot_summary: AIResearchContextConsumerGovernanceTimelineSnapshotSummary | None,
    governance_timeline_snapshot_summary_validation: AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_SUMMARY_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary:
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
        return AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary(
            governance_timeline_snapshot_delivery_summary_state="unavailable",
            governance_timeline_snapshot_delivery_summary_visible=False,
            governance_timeline_snapshot_delivery_summary_reference="not available",
            governance_timeline_snapshot_delivery_reference=delivery_reference,
            governance_timeline_snapshot_delivery_visible=delivery_visible,
            governance_timeline_snapshot_delivery_validation_reference=delivery_validation_reference,
            governance_timeline_snapshot_delivery_validation_visible=delivery_validation_visible,
            governance_timeline_snapshot_summary_reference=summary_reference,
            governance_timeline_snapshot_summary_visible=summary_visible,
            governance_timeline_snapshot_summary_validation_reference=summary_validation_reference,
            governance_timeline_snapshot_summary_validation_visible=summary_validation_visible,
            summary="AI research context consumer governance timeline snapshot delivery summary is unavailable.",
            governance_timeline_snapshot_delivery_summary=(
                "AI research context consumer governance timeline snapshot delivery summary is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryContractMeta(
                surface=surface
            ),
        )

    delivery_state = (
        governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_state
        if governance_timeline_snapshot_delivery is not None
        else "unknown"
    )
    delivery_summary_visible = delivery_visible
    delivery_summary_reference = _summary_reference_text(
        delivery_state=delivery_state,
        delivery_reference=delivery_reference,
        delivery_validation_reference=delivery_validation_reference,
        summary_reference=summary_reference,
        summary_validation_reference=summary_validation_reference,
    )
    summary = _summary_text(
        delivery_state=delivery_state,
        delivery_summary_visible=delivery_summary_visible,
        delivery_summary_reference=delivery_summary_reference,
        delivery_reference=delivery_reference,
        delivery_visible=delivery_visible,
        delivery_validation_reference=delivery_validation_reference,
        delivery_validation_visible=delivery_validation_visible,
        summary_reference=summary_reference,
        summary_visible=summary_visible,
        summary_validation_reference=summary_validation_reference,
        summary_validation_visible=summary_validation_visible,
    )
    return AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary(
        available=True,
        governance_timeline_snapshot_delivery_summary_state=delivery_state,
        governance_timeline_snapshot_delivery_summary_visible=delivery_summary_visible,
        governance_timeline_snapshot_delivery_summary_reference=delivery_summary_reference,
        governance_timeline_snapshot_delivery_reference=delivery_reference,
        governance_timeline_snapshot_delivery_visible=delivery_visible,
        governance_timeline_snapshot_delivery_validation_reference=delivery_validation_reference,
        governance_timeline_snapshot_delivery_validation_visible=delivery_validation_visible,
        governance_timeline_snapshot_summary_reference=summary_reference,
        governance_timeline_snapshot_summary_visible=summary_visible,
        governance_timeline_snapshot_summary_validation_reference=summary_validation_reference,
        governance_timeline_snapshot_summary_validation_visible=summary_validation_visible,
        summary=summary,
        governance_timeline_snapshot_delivery_summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_summary_markdown(
    governance_timeline_snapshot_delivery_summary: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary | None
    ),
) -> str:
    if (
        governance_timeline_snapshot_delivery_summary is None
        or not governance_timeline_snapshot_delivery_summary.available
    ):
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot Delivery Summary",
                "",
                "AI research context consumer governance timeline snapshot delivery summary is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline snapshot delivery summary state",
            governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_summary_state,
        ),
        (
            "Governance timeline snapshot delivery summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery summary reference",
            governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_summary_reference,
        ),
        (
            "Governance timeline snapshot delivery reference",
            governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_reference,
        ),
        (
            "Governance timeline snapshot delivery visible",
            "Yes"
            if governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery validation reference",
            governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary reference",
            governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_summary_reference,
        ),
        (
            "Governance timeline snapshot summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary validation reference",
            governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_summary_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery summary contract",
            f"{governance_timeline_snapshot_delivery_summary.contract_meta.version} / {governance_timeline_snapshot_delivery_summary.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot Delivery Summary",
        "",
        f"*{governance_timeline_snapshot_delivery_summary.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _delivery_reference(
    governance_timeline_snapshot_delivery: AIResearchContextConsumerGovernanceTimelineSnapshotDelivery | None,
) -> str:
    if governance_timeline_snapshot_delivery is None:
        return "not available"
    return governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_reference


def _delivery_validation_reference(
    governance_timeline_snapshot_delivery_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation | None
    ),
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


def _summary_reference_text(
    *,
    delivery_state: str,
    delivery_reference: str,
    delivery_validation_reference: str,
    summary_reference: str,
    summary_validation_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot delivery summary: "
        f"state={delivery_state}; "
        f"delivery={delivery_reference}; "
        f"delivery_validation={delivery_validation_reference}; "
        f"summary={summary_reference}; "
        f"summary_validation={summary_validation_reference}"
    )


def _summary_text(
    *,
    delivery_state: str,
    delivery_summary_visible: bool,
    delivery_summary_reference: str,
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
        "AI research context consumer governance timeline snapshot delivery summary: "
        f"state={delivery_state}; "
        f"visible={'yes' if delivery_summary_visible else 'no'}; "
        f"reference={delivery_summary_reference}; "
        f"delivery_reference={delivery_reference}; "
        f"delivery_visible={'yes' if delivery_visible else 'no'}; "
        f"delivery_validation_reference={delivery_validation_reference}; "
        f"delivery_validation_visible={'yes' if delivery_validation_visible else 'no'}; "
        f"summary_reference={summary_reference}; "
        f"summary_visible={'yes' if summary_visible else 'no'}; "
        f"summary_validation_reference={summary_validation_reference}; "
        f"summary_validation_visible={'yes' if summary_validation_visible else 'no'}"
    )

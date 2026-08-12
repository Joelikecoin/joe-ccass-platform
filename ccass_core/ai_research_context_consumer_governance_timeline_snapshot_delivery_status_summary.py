from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDelivery,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_status import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_status_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidation,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_summary import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_summary_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryValidation,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary import (
    AIResearchContextConsumerGovernanceTimelineSnapshotSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot_delivery_status_summary"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_SURFACE


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_delivery_status_summary_state: Literal[
        "consistent",
        "partial",
        "inconsistent",
        "unknown",
        "unavailable",
    ] = "unknown"
    governance_timeline_snapshot_delivery_status_summary_visible: bool = False
    governance_timeline_snapshot_delivery_status_summary_reference: str = "not available"
    governance_timeline_snapshot_delivery_status_reference: str = "not available"
    governance_timeline_snapshot_delivery_status_visible: bool = False
    governance_timeline_snapshot_delivery_status_validation_reference: str = "not available"
    governance_timeline_snapshot_delivery_status_validation_visible: bool = False
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
        "AI research context consumer governance timeline snapshot delivery status summary is unavailable."
    )
    governance_timeline_snapshot_delivery_status_summary: str = (
        "AI research context consumer governance timeline snapshot delivery status summary is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryContractMeta = (
        Field(default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryContractMeta)
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status_summary(
    *,
    available: bool,
    governance_timeline_snapshot_delivery_status: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus | None
    ),
    governance_timeline_snapshot_delivery_status_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidation | None
    ),
    governance_timeline_snapshot_delivery_summary: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary | None
    ),
    governance_timeline_snapshot_delivery_summary_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryValidation | None
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
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummary:
    status_reference = _status_reference(governance_timeline_snapshot_delivery_status)
    status_visible = bool(
        governance_timeline_snapshot_delivery_status is not None
        and governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_visible
    )
    status_validation_reference = _status_validation_reference(
        governance_timeline_snapshot_delivery_status_validation
    )
    status_validation_visible = bool(
        governance_timeline_snapshot_delivery_status_validation is not None
        and governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_status_visible
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
        return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummary(
            governance_timeline_snapshot_delivery_status_summary_state="unavailable",
            governance_timeline_snapshot_delivery_status_summary_visible=False,
            governance_timeline_snapshot_delivery_status_summary_reference="not available",
            governance_timeline_snapshot_delivery_status_reference=status_reference,
            governance_timeline_snapshot_delivery_status_visible=status_visible,
            governance_timeline_snapshot_delivery_status_validation_reference=status_validation_reference,
            governance_timeline_snapshot_delivery_status_validation_visible=status_validation_visible,
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
            summary="AI research context consumer governance timeline snapshot delivery status summary is unavailable.",
            governance_timeline_snapshot_delivery_status_summary=(
                "AI research context consumer governance timeline snapshot delivery status summary is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryContractMeta(
                surface=surface
            ),
        )

    status_state = (
        governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_state
        if governance_timeline_snapshot_delivery_status is not None
        else "unknown"
    )
    summary_reference_text = _summary_reference_text(
        status_state=status_state,
        status_reference=status_reference,
        status_validation_reference=status_validation_reference,
        delivery_summary_reference=delivery_summary_reference,
        delivery_summary_validation_reference=delivery_summary_validation_reference,
        delivery_reference=delivery_reference,
        delivery_validation_reference=delivery_validation_reference,
        summary_reference=summary_reference,
        summary_validation_reference=summary_validation_reference,
    )
    summary = _summary_text(
        status_state=status_state,
        status_visible=status_visible,
        status_reference=status_reference,
        status_validation_reference=status_validation_reference,
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
    return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummary(
        available=True,
        governance_timeline_snapshot_delivery_status_summary_state=status_state,
        governance_timeline_snapshot_delivery_status_summary_visible=status_visible,
        governance_timeline_snapshot_delivery_status_summary_reference=summary_reference_text,
        governance_timeline_snapshot_delivery_status_reference=status_reference,
        governance_timeline_snapshot_delivery_status_visible=status_visible,
        governance_timeline_snapshot_delivery_status_validation_reference=status_validation_reference,
        governance_timeline_snapshot_delivery_status_validation_visible=status_validation_visible,
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
        governance_timeline_snapshot_delivery_status_summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status_summary_markdown(
    governance_timeline_snapshot_delivery_status_summary: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummary | None
    ),
) -> str:
    if (
        governance_timeline_snapshot_delivery_status_summary is None
        or not governance_timeline_snapshot_delivery_status_summary.available
    ):
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot Delivery Status Summary",
                "",
                "AI research context consumer governance timeline snapshot delivery status summary is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline snapshot delivery status summary state",
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_summary_state,
        ),
        (
            "Governance timeline snapshot delivery status summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status summary reference",
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_summary_reference,
        ),
        (
            "Governance timeline snapshot delivery status reference",
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_reference,
        ),
        (
            "Governance timeline snapshot delivery status visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status validation reference",
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery status validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery summary reference",
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_summary_reference,
        ),
        (
            "Governance timeline snapshot delivery summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery summary validation reference",
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_summary_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery reference",
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_reference,
        ),
        (
            "Governance timeline snapshot delivery visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery validation reference",
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary reference",
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_summary_reference,
        ),
        (
            "Governance timeline snapshot summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary validation reference",
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_summary_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status summary contract",
            f"{governance_timeline_snapshot_delivery_status_summary.contract_meta.version} / {governance_timeline_snapshot_delivery_status_summary.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot Delivery Status Summary",
        "",
        f"*{governance_timeline_snapshot_delivery_status_summary.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _summary_reference_text(
    *,
    status_state: str,
    status_reference: str,
    status_validation_reference: str,
    delivery_summary_reference: str,
    delivery_summary_validation_reference: str,
    delivery_reference: str,
    delivery_validation_reference: str,
    summary_reference: str,
    summary_validation_reference: str,
) -> str:
    return (
        f"{status_state} / "
        f"{status_reference} / "
        f"{status_validation_reference} / "
        f"{delivery_summary_reference} / "
        f"{delivery_summary_validation_reference} / "
        f"{delivery_reference} / "
        f"{delivery_validation_reference} / "
        f"{summary_reference} / "
        f"{summary_validation_reference}"
    )


def _summary_text(
    *,
    status_state: str,
    status_visible: bool,
    status_reference: str,
    status_validation_reference: str,
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
        "AI research context consumer governance timeline snapshot delivery status summary: "
        f"status_state={status_state}; "
        f"status_visible={'yes' if status_visible else 'no'}; "
        f"status_reference={status_reference}; "
        f"status_validation_reference={status_validation_reference}; "
        f"delivery_summary_reference={delivery_summary_reference}; "
        f"delivery_summary_visible={'yes' if delivery_summary_visible else 'no'}; "
        f"delivery_summary_validation_reference={delivery_summary_validation_reference}; "
        f"delivery_summary_validation_visible={'yes' if delivery_summary_validation_visible else 'no'}; "
        f"delivery_reference={delivery_reference}; "
        f"delivery_visible={'yes' if delivery_visible else 'no'}; "
        f"delivery_validation_reference={delivery_validation_reference}; "
        f"delivery_validation_visible={'yes' if delivery_validation_visible else 'no'}; "
        f"summary_reference={summary_reference}; "
        f"summary_visible={'yes' if summary_visible else 'no'}; "
        f"summary_validation_reference={summary_validation_reference}; "
        f"summary_validation_visible={'yes' if summary_validation_visible else 'no'}"
    )


def _status_reference(
    governance_timeline_snapshot_delivery_status: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus | None
    ),
) -> str:
    if governance_timeline_snapshot_delivery_status is None:
        return "not available"
    return (
        governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_reference
    )


def _status_validation_reference(
    governance_timeline_snapshot_delivery_status_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidation | None
    ),
) -> str:
    if governance_timeline_snapshot_delivery_status_validation is None:
        return "not available"
    return governance_timeline_snapshot_delivery_status_validation.validation_reference


def _delivery_summary_reference(
    governance_timeline_snapshot_delivery_summary: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary | None
    ),
) -> str:
    if governance_timeline_snapshot_delivery_summary is None:
        return "not available"
    return governance_timeline_snapshot_delivery_summary.governance_timeline_snapshot_delivery_summary_reference


def _delivery_summary_validation_reference(
    governance_timeline_snapshot_delivery_summary_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryValidation | None
    ),
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
    governance_timeline_snapshot_summary_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation | None
    ),
) -> str:
    if governance_timeline_snapshot_summary_validation is None:
        return "not available"
    return governance_timeline_snapshot_summary_validation.validation_reference

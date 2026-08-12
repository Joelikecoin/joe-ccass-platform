from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDelivery,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery_status import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus,
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

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_VALIDATION_VERSION = (
    "v0.1"
)
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_VALIDATION_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot_delivery_status_summary_validation"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidationContractMeta(
    BaseModel
):
    version: str = (
        AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_VALIDATION_VERSION
    )
    surface: str = (
        AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_VALIDATION_SURFACE
    )


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidation(
    BaseModel
):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_delivery_status_summary_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
    governance_timeline_snapshot_delivery_status_summary_visible: bool = False
    validation_reference: str = "not available"
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
    missing_governance_timeline_snapshot_delivery_status_summary_references: list[str] = Field(
        default_factory=list
    )
    consistency_warnings: list[str] = Field(default_factory=list)
    summary: str = (
        "AI research context consumer governance timeline snapshot delivery status summary validation is unavailable."
    )
    contract_meta: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidationContractMeta
    ) = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidationContractMeta
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status_summary_validation(
    *,
    available: bool,
    governance_timeline_snapshot_delivery_status_summary: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummary | None
    ),
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
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_SUMMARY_VALIDATION_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidation:
    summary_available = bool(
        governance_timeline_snapshot_delivery_status_summary is not None
        and governance_timeline_snapshot_delivery_status_summary.available
    )
    status_available = bool(
        governance_timeline_snapshot_delivery_status is not None
        and governance_timeline_snapshot_delivery_status.available
    )
    status_validation_available = bool(
        governance_timeline_snapshot_delivery_status_validation is not None
        and governance_timeline_snapshot_delivery_status_validation.available
    )
    delivery_summary_available = bool(
        governance_timeline_snapshot_delivery_summary is not None
        and governance_timeline_snapshot_delivery_summary.available
    )
    delivery_summary_validation_available = bool(
        governance_timeline_snapshot_delivery_summary_validation is not None
        and governance_timeline_snapshot_delivery_summary_validation.available
    )
    delivery_available = bool(
        governance_timeline_snapshot_delivery is not None
        and governance_timeline_snapshot_delivery.available
    )
    delivery_validation_available = bool(
        governance_timeline_snapshot_delivery_validation is not None
        and governance_timeline_snapshot_delivery_validation.available
    )
    snapshot_available = bool(
        governance_timeline_snapshot_summary is not None
        and governance_timeline_snapshot_summary.available
    )
    snapshot_validation_available = bool(
        governance_timeline_snapshot_summary_validation is not None
        and governance_timeline_snapshot_summary_validation.available
    )

    summary_reference = _summary_reference(governance_timeline_snapshot_delivery_status_summary)
    summary_visible = bool(
        governance_timeline_snapshot_delivery_status_summary is not None
        and governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_summary_visible
    )
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
    snapshot_reference = _snapshot_reference(governance_timeline_snapshot_summary)
    snapshot_visible = bool(
        governance_timeline_snapshot_summary is not None
        and governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_visible
    )
    snapshot_validation_reference = _snapshot_validation_reference(
        governance_timeline_snapshot_summary_validation
    )
    snapshot_validation_visible = bool(
        governance_timeline_snapshot_summary_validation is not None
        and governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_summary_visible
    )

    if not available:
        return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidation(
            validation_state="unknown",
            governance_timeline_snapshot_delivery_status_summary_visible=False,
            validation_reference="not available",
            governance_timeline_snapshot_delivery_status_summary_reference=summary_reference,
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
            governance_timeline_snapshot_summary_reference=snapshot_reference,
            governance_timeline_snapshot_summary_visible=snapshot_visible,
            governance_timeline_snapshot_summary_validation_reference=snapshot_validation_reference,
            governance_timeline_snapshot_summary_validation_visible=snapshot_validation_visible,
            summary=(
                "AI research context consumer governance timeline snapshot delivery status summary validation is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidationContractMeta(
                surface=surface
            ),
        )

    missing: list[str] = []
    if not _reference_present(summary_reference):
        missing.append("governance_timeline_snapshot_delivery_status_summary_reference")
    if not _reference_present(status_reference):
        missing.append("governance_timeline_snapshot_delivery_status_reference")
    if not _reference_present(status_validation_reference):
        missing.append("governance_timeline_snapshot_delivery_status_validation_reference")
    if not _reference_present(delivery_summary_reference):
        missing.append("governance_timeline_snapshot_delivery_summary_reference")
    if not _reference_present(delivery_summary_validation_reference):
        missing.append("governance_timeline_snapshot_delivery_summary_validation_reference")
    if not _reference_present(delivery_reference):
        missing.append("governance_timeline_snapshot_delivery_reference")
    if not _reference_present(delivery_validation_reference):
        missing.append("governance_timeline_snapshot_delivery_validation_reference")
    if not _reference_present(snapshot_reference):
        missing.append("governance_timeline_snapshot_summary_reference")
    if not _reference_present(snapshot_validation_reference):
        missing.append("governance_timeline_snapshot_summary_validation_reference")
    if not summary_available:
        missing.append("governance_timeline_snapshot_delivery_status_summary")

    expected_summary_state = _summary_state(
        summary_available=summary_available,
        status_available=status_available,
        status_validation_available=status_validation_available,
        delivery_summary_available=delivery_summary_available,
        delivery_summary_validation_available=delivery_summary_validation_available,
        delivery_available=delivery_available,
        delivery_validation_available=delivery_validation_available,
        snapshot_available=snapshot_available,
        snapshot_validation_available=snapshot_validation_available,
    )
    expected_visible = expected_summary_state in {"complete", "partial"}

    consistency_warnings: list[str] = []
    if summary_available and governance_timeline_snapshot_delivery_status_summary is not None:
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_summary_state
            != expected_summary_state
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery status summary state mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_summary_visible
            != expected_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery status summary visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_reference
            != status_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery status reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_visible
            != status_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery status visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_validation_reference
            != status_validation_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery status validation reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_status_validation_visible
            != status_validation_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery status validation visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_summary_reference
            != delivery_summary_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery summary reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_summary_visible
            != delivery_summary_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery summary visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_summary_validation_reference
            != delivery_summary_validation_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery summary validation reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_summary_validation_visible
            != delivery_summary_validation_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery summary validation visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_reference
            != delivery_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_visible
            != delivery_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_validation_reference
            != delivery_validation_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery validation reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_delivery_validation_visible
            != delivery_validation_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery validation visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_summary_reference
            != snapshot_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot summary reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_summary_visible
            != snapshot_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot summary visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_summary_validation_reference
            != snapshot_validation_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot summary validation reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status_summary.governance_timeline_snapshot_summary_validation_visible
            != snapshot_validation_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot summary validation visibility mismatch."
            )

    if consistency_warnings:
        validation_state = "inconsistent"
    elif missing:
        validation_state = "partial" if summary_available else "unknown"
    elif summary_available:
        validation_state = "consistent"
    else:
        validation_state = "unknown"

    summary_consistent = validation_state == "consistent"
    validation_reference = _validation_reference(
        validation_state=validation_state,
        summary_reference=summary_reference,
        status_reference=status_reference,
        status_validation_reference=status_validation_reference,
        delivery_summary_reference=delivery_summary_reference,
        delivery_summary_validation_reference=delivery_summary_validation_reference,
        delivery_reference=delivery_reference,
        delivery_validation_reference=delivery_validation_reference,
        snapshot_reference=snapshot_reference,
        snapshot_validation_reference=snapshot_validation_reference,
    )
    summary = _summary_text(
        validation_state=validation_state,
        summary_visible=expected_visible,
        validation_reference=validation_reference,
        summary_reference=summary_reference,
        status_reference=status_reference,
        status_visible=status_visible,
        status_validation_reference=status_validation_reference,
        status_validation_visible=status_validation_visible,
        delivery_summary_reference=delivery_summary_reference,
        delivery_summary_visible=delivery_summary_visible,
        delivery_summary_validation_reference=delivery_summary_validation_reference,
        delivery_summary_validation_visible=delivery_summary_validation_visible,
        delivery_reference=delivery_reference,
        delivery_visible=delivery_visible,
        delivery_validation_reference=delivery_validation_reference,
        delivery_validation_visible=delivery_validation_visible,
        snapshot_reference=snapshot_reference,
        snapshot_visible=snapshot_visible,
        snapshot_validation_reference=snapshot_validation_reference,
        snapshot_validation_visible=snapshot_validation_visible,
    )
    return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidation(
        available=True,
        governance_timeline_snapshot_delivery_status_summary_consistent=summary_consistent,
        validation_state=validation_state,
        governance_timeline_snapshot_delivery_status_summary_visible=expected_visible,
        validation_reference=validation_reference,
        governance_timeline_snapshot_delivery_status_summary_reference=summary_reference,
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
        governance_timeline_snapshot_summary_reference=snapshot_reference,
        governance_timeline_snapshot_summary_visible=snapshot_visible,
        governance_timeline_snapshot_summary_validation_reference=snapshot_validation_reference,
        governance_timeline_snapshot_summary_validation_visible=snapshot_validation_visible,
        missing_governance_timeline_snapshot_delivery_status_summary_references=missing,
        consistency_warnings=consistency_warnings,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidationContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status_summary_validation_markdown(
    governance_timeline_snapshot_delivery_status_summary_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusSummaryValidation | None
    ),
) -> str:
    if (
        governance_timeline_snapshot_delivery_status_summary_validation is None
        or not governance_timeline_snapshot_delivery_status_summary_validation.available
    ):
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot Delivery Status Summary Validation",
                "",
                "AI research context consumer governance timeline snapshot delivery status summary validation is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline snapshot delivery status summary consistent",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_status_summary_consistent
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status summary state",
            governance_timeline_snapshot_delivery_status_summary_validation.validation_state,
        ),
        (
            "Governance timeline snapshot delivery status summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_status_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status summary reference",
            governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_status_summary_reference,
        ),
        (
            "Governance timeline snapshot delivery status reference",
            governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_status_reference,
        ),
        (
            "Governance timeline snapshot delivery status visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_status_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status validation reference",
            governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_status_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery status validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_status_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery summary reference",
            governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_summary_reference,
        ),
        (
            "Governance timeline snapshot delivery summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery summary validation reference",
            governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_summary_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery reference",
            governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_reference,
        ),
        (
            "Governance timeline snapshot delivery visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery validation reference",
            governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_delivery_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary reference",
            governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_summary_reference,
        ),
        (
            "Governance timeline snapshot summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary validation reference",
            governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_summary_validation.governance_timeline_snapshot_summary_validation_visible
            else "No",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot Delivery Status Summary Validation",
        "",
        f"*{governance_timeline_snapshot_delivery_status_summary_validation.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _validation_reference(
    *,
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"],
    summary_reference: str,
    status_reference: str,
    status_validation_reference: str,
    delivery_summary_reference: str,
    delivery_summary_validation_reference: str,
    delivery_reference: str,
    delivery_validation_reference: str,
    snapshot_reference: str,
    snapshot_validation_reference: str,
) -> str:
    if validation_state == "unknown":
        return "not available"
    return (
        f"state={validation_state}; "
        f"summary={summary_reference}; "
        f"status={status_reference}; "
        f"status_validation={status_validation_reference}; "
        f"delivery_summary={delivery_summary_reference}; "
        f"delivery_summary_validation={delivery_summary_validation_reference}; "
        f"delivery={delivery_reference}; "
        f"delivery_validation={delivery_validation_reference}; "
        f"snapshot={snapshot_reference}; "
        f"snapshot_validation={snapshot_validation_reference}"
    )


def _summary_text(
    *,
    validation_state: str,
    summary_visible: bool,
    validation_reference: str,
    summary_reference: str,
    status_reference: str,
    status_visible: bool,
    status_validation_reference: str,
    status_validation_visible: bool,
    delivery_summary_reference: str,
    delivery_summary_visible: bool,
    delivery_summary_validation_reference: str,
    delivery_summary_validation_visible: bool,
    delivery_reference: str,
    delivery_visible: bool,
    delivery_validation_reference: str,
    delivery_validation_visible: bool,
    snapshot_reference: str,
    snapshot_visible: bool,
    snapshot_validation_reference: str,
    snapshot_validation_visible: bool,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot delivery status summary validation: "
        f"state={validation_state}; "
        f"visible={'yes' if summary_visible else 'no'}; "
        f"reference={validation_reference}; "
        f"summary={summary_reference}; "
        f"status={status_reference}; "
        f"status_visible={'yes' if status_visible else 'no'}; "
        f"status_validation={status_validation_reference}; "
        f"status_validation_visible={'yes' if status_validation_visible else 'no'}; "
        f"delivery_summary={delivery_summary_reference}; "
        f"delivery_summary_visible={'yes' if delivery_summary_visible else 'no'}; "
        f"delivery_summary_validation={delivery_summary_validation_reference}; "
        f"delivery_summary_validation_visible={'yes' if delivery_summary_validation_visible else 'no'}; "
        f"delivery={delivery_reference}; "
        f"delivery_visible={'yes' if delivery_visible else 'no'}; "
        f"delivery_validation={delivery_validation_reference}; "
        f"delivery_validation_visible={'yes' if delivery_validation_visible else 'no'}; "
        f"snapshot={snapshot_reference}; "
        f"snapshot_visible={'yes' if snapshot_visible else 'no'}; "
        f"snapshot_validation={snapshot_validation_reference}; "
        f"snapshot_validation_visible={'yes' if snapshot_validation_visible else 'no'}"
    )


def _reference_present(reference: str) -> bool:
    return bool(reference and reference.strip() and reference != "not available")


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


def _snapshot_reference(
    governance_timeline_snapshot_summary: AIResearchContextConsumerGovernanceTimelineSnapshotSummary | None,
) -> str:
    if governance_timeline_snapshot_summary is None:
        return "not available"
    return governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_reference


def _snapshot_validation_reference(
    governance_timeline_snapshot_summary_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation | None
    ),
) -> str:
    if governance_timeline_snapshot_summary_validation is None:
        return "not available"
    return governance_timeline_snapshot_summary_validation.validation_reference


def _summary_state(
    *,
    summary_available: bool,
    status_available: bool,
    status_validation_available: bool,
    delivery_summary_available: bool,
    delivery_summary_validation_available: bool,
    delivery_available: bool,
    delivery_validation_available: bool,
    snapshot_available: bool,
    snapshot_validation_available: bool,
) -> str:
    if not summary_available:
        return "unavailable"
    if not all(
        [
            status_available,
            status_validation_available,
            delivery_summary_available,
            delivery_summary_validation_available,
            delivery_available,
            delivery_validation_available,
            snapshot_available,
            snapshot_validation_available,
        ]
    ):
        return "partial"
    return "complete"

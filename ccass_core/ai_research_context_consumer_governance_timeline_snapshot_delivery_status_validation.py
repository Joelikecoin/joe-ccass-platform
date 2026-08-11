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

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_VALIDATION_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_VALIDATION_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot_delivery_status_validation"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidationContractMeta(
    BaseModel
):
    version: str = (
        AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_VALIDATION_VERSION
    )
    surface: str = (
        AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_VALIDATION_SURFACE
    )


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_delivery_status_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
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
    missing_governance_timeline_snapshot_delivery_status_references: list[str] = Field(
        default_factory=list
    )
    consistency_warnings: list[str] = Field(default_factory=list)
    summary: str = (
        "AI research context consumer governance timeline snapshot delivery status validation is unavailable."
    )
    contract_meta: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidationContractMeta
    ) = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidationContractMeta
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status_validation(
    *,
    available: bool,
    governance_timeline_snapshot_delivery_status: AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus | None,
    governance_timeline_snapshot_delivery_summary: AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummary | None,
    governance_timeline_snapshot_delivery_summary_validation: AIResearchContextConsumerGovernanceTimelineSnapshotDeliverySummaryValidation | None,
    governance_timeline_snapshot_delivery: AIResearchContextConsumerGovernanceTimelineSnapshotDelivery | None,
    governance_timeline_snapshot_delivery_validation: AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation | None,
    governance_timeline_snapshot_summary: AIResearchContextConsumerGovernanceTimelineSnapshotSummary | None,
    governance_timeline_snapshot_summary_validation: AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_STATUS_VALIDATION_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidation:
    status_available = bool(
        governance_timeline_snapshot_delivery_status is not None
        and governance_timeline_snapshot_delivery_status.available
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
    status_reference = _status_reference(governance_timeline_snapshot_delivery_status)
    status_visible = bool(
        governance_timeline_snapshot_delivery_status is not None
        and governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_visible
    )

    if not available:
        return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidation(
            validation_state="unknown",
            governance_timeline_snapshot_delivery_status_visible=False,
            validation_reference="not available",
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
            summary=(
                "AI research context consumer governance timeline snapshot delivery status validation is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidationContractMeta(
                surface=surface
            ),
        )

    missing: list[str] = []
    if not _reference_present(status_reference):
        missing.append("governance_timeline_snapshot_delivery_status_reference")
    if not _reference_present(delivery_summary_reference):
        missing.append("governance_timeline_snapshot_delivery_summary_reference")
    if not _reference_present(delivery_summary_validation_reference):
        missing.append("governance_timeline_snapshot_delivery_summary_validation_reference")
    if not _reference_present(delivery_reference):
        missing.append("governance_timeline_snapshot_delivery_reference")
    if not _reference_present(delivery_validation_reference):
        missing.append("governance_timeline_snapshot_delivery_validation_reference")
    if not _reference_present(summary_reference):
        missing.append("governance_timeline_snapshot_summary_reference")
    if not _reference_present(summary_validation_reference):
        missing.append("governance_timeline_snapshot_summary_validation_reference")
    if not status_available:
        missing.append("governance_timeline_snapshot_delivery_status")

    expected_state = _status_state(
        status_available=status_available,
        delivery_summary_validation_available=bool(
            governance_timeline_snapshot_delivery_summary_validation is not None
            and governance_timeline_snapshot_delivery_summary_validation.available
        ),
        delivery_summary_validation_state=(
            governance_timeline_snapshot_delivery_summary_validation.validation_state
            if governance_timeline_snapshot_delivery_summary_validation is not None
            and governance_timeline_snapshot_delivery_summary_validation.available
            else "unknown"
        ),
    )
    expected_visible = expected_state in {"consistent", "partial"}
    expected_reference = _validation_reference(
        validation_state=expected_state,
        status_reference=status_reference,
        delivery_summary_reference=delivery_summary_reference,
        delivery_summary_validation_reference=delivery_summary_validation_reference,
        delivery_reference=delivery_reference,
        delivery_validation_reference=delivery_validation_reference,
        summary_reference=summary_reference,
        summary_validation_reference=summary_validation_reference,
    )

    consistency_warnings: list[str] = []
    if status_available and governance_timeline_snapshot_delivery_status is not None:
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_state
            != expected_state
        ):
            consistency_warnings.append("Governance timeline snapshot delivery status state mismatch.")
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_visible
            != expected_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery status visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_reference
            != status_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery status reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_summary_reference
            != delivery_summary_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery summary reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_summary_visible
            != delivery_summary_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery summary visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_summary_validation_reference
            != delivery_summary_validation_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery summary validation reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_summary_validation_visible
            != delivery_summary_validation_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery summary validation visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_reference
            != delivery_reference
        ):
            consistency_warnings.append("Governance timeline snapshot delivery reference mismatch.")
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_visible
            != delivery_visible
        ):
            consistency_warnings.append("Governance timeline snapshot delivery visibility mismatch.")
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_validation_reference
            != delivery_validation_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery validation reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_validation_visible
            != delivery_validation_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot delivery validation visibility mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_summary_reference
            != summary_reference
        ):
            consistency_warnings.append("Governance timeline snapshot summary reference mismatch.")
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_summary_visible
            != summary_visible
        ):
            consistency_warnings.append("Governance timeline snapshot summary visibility mismatch.")
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_summary_validation_reference
            != summary_validation_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot summary validation reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_summary_validation_visible
            != summary_validation_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot summary validation visibility mismatch."
            )

    if consistency_warnings:
        validation_state = "inconsistent"
    elif missing:
        validation_state = "partial" if status_available else "unknown"
    elif status_available:
        validation_state = "consistent"
    else:
        validation_state = "unknown"

    status_consistent = validation_state == "consistent"
    validation_reference = _validation_reference(
        validation_state=validation_state,
        status_reference=status_reference,
        delivery_summary_reference=delivery_summary_reference,
        delivery_summary_validation_reference=delivery_summary_validation_reference,
        delivery_reference=delivery_reference,
        delivery_validation_reference=delivery_validation_reference,
        summary_reference=summary_reference,
        summary_validation_reference=summary_validation_reference,
    )
    summary = _summary_text(
        validation_state=validation_state,
        status_visible=expected_visible,
        validation_reference=validation_reference,
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
    return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidation(
        available=True,
        governance_timeline_snapshot_delivery_status_consistent=status_consistent,
        validation_state=validation_state,
        governance_timeline_snapshot_delivery_status_visible=expected_visible,
        validation_reference=validation_reference,
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
        missing_governance_timeline_snapshot_delivery_status_references=missing,
        consistency_warnings=consistency_warnings,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidationContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_status_validation_markdown(
    governance_timeline_snapshot_delivery_status_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatusValidation | None
    ),
) -> str:
    if (
        governance_timeline_snapshot_delivery_status_validation is None
        or not governance_timeline_snapshot_delivery_status_validation.available
    ):
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot Delivery Status Validation",
                "",
                "AI research context consumer governance timeline snapshot delivery status validation is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline snapshot delivery status consistent",
            "Yes"
            if governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_status_consistent
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status state",
            governance_timeline_snapshot_delivery_status_validation.validation_state,
        ),
        (
            "Governance timeline snapshot delivery status visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_status_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status reference",
            governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_status_reference,
        ),
        (
            "Governance timeline snapshot delivery summary reference",
            governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_summary_reference,
        ),
        (
            "Governance timeline snapshot delivery summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery summary validation reference",
            governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_summary_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery reference",
            governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_reference,
        ),
        (
            "Governance timeline snapshot delivery visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery validation reference",
            governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_validation_reference,
        ),
        (
            "Governance timeline snapshot delivery validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_delivery_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary reference",
            governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_summary_reference,
        ),
        (
            "Governance timeline snapshot summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary validation reference",
            governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_status_validation.governance_timeline_snapshot_summary_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery status contract",
            f"{governance_timeline_snapshot_delivery_status_validation.contract_meta.version} / {governance_timeline_snapshot_delivery_status_validation.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot Delivery Status Validation",
        "",
        f"*{governance_timeline_snapshot_delivery_status_validation.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _validation_reference(
    *,
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"],
    status_reference: str,
    delivery_summary_reference: str,
    delivery_summary_validation_reference: str,
    delivery_reference: str,
    delivery_validation_reference: str,
    summary_reference: str,
    summary_validation_reference: str,
) -> str:
    if validation_state == "unknown":
        return "not available"
    return (
        f"state={validation_state}; "
        f"status={status_reference}; "
        f"delivery_summary={delivery_summary_reference}; "
        f"delivery_summary_validation={delivery_summary_validation_reference}; "
        f"delivery={delivery_reference}; "
        f"delivery_validation={delivery_validation_reference}; "
        f"summary={summary_reference}; "
        f"summary_validation={summary_validation_reference}"
    )


def _summary_text(
    *,
    validation_state: str,
    status_visible: bool,
    validation_reference: str,
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
        "AI research context consumer governance timeline snapshot delivery status validation: "
        f"state={validation_state}; "
        f"visible={'yes' if status_visible else 'no'}; "
        f"reference={validation_reference}; "
        f"status={status_reference}; "
        f"delivery_summary={delivery_summary_reference}; "
        f"delivery_summary_visible={'yes' if delivery_summary_visible else 'no'}; "
        f"delivery_summary_validation={delivery_summary_validation_reference}; "
        f"delivery_summary_validation_visible={'yes' if delivery_summary_validation_visible else 'no'}; "
        f"delivery={delivery_reference}; "
        f"delivery_visible={'yes' if delivery_visible else 'no'}; "
        f"delivery_validation={delivery_validation_reference}; "
        f"delivery_validation_visible={'yes' if delivery_validation_visible else 'no'}; "
        f"summary={summary_reference}; "
        f"summary_visible={'yes' if summary_visible else 'no'}; "
        f"summary_validation={summary_validation_reference}; "
        f"summary_validation_visible={'yes' if summary_validation_visible else 'no'}"
    )


def _reference_present(reference: str) -> bool:
    return bool(reference and reference.strip() and reference != "not available")


def _status_reference(
    governance_timeline_snapshot_delivery_status: AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryStatus | None,
) -> str:
    if governance_timeline_snapshot_delivery_status is None:
        return "not available"
    return (
        governance_timeline_snapshot_delivery_status.governance_timeline_snapshot_delivery_status_reference
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


def _status_state(
    *,
    status_available: bool,
    delivery_summary_validation_available: bool,
    delivery_summary_validation_state: str,
) -> Literal["consistent", "partial", "inconsistent", "unknown"]:
    if not status_available:
        return "unknown"
    if delivery_summary_validation_available:
        if delivery_summary_validation_state == "consistent":
            return "consistent"
        if delivery_summary_validation_state in {"partial", "inconsistent"}:
            return "partial"
    return "partial"

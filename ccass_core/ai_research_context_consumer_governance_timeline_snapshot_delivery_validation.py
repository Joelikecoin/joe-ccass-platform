from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_delivery import (
    AIResearchContextConsumerGovernanceTimelineSnapshotDelivery,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary import (
    AIResearchContextConsumerGovernanceTimelineSnapshotSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotValidation,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_VALIDATION_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_VALIDATION_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot_delivery_validation"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidationContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_VALIDATION_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_VALIDATION_SURFACE


class AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_delivery_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
    governance_timeline_snapshot_delivery_visible: bool = False
    validation_reference: str = "not available"
    governance_timeline_snapshot_delivery_reference: str = "not available"
    governance_timeline_snapshot_summary_reference: str = "not available"
    governance_timeline_snapshot_summary_visible: bool = False
    governance_timeline_snapshot_summary_validation_reference: str = "not available"
    governance_timeline_snapshot_summary_validation_visible: bool = False
    governance_timeline_snapshot_reference: str = "not available"
    governance_timeline_snapshot_visible: bool = False
    governance_timeline_snapshot_validation_reference: str = "not available"
    governance_timeline_snapshot_validation_visible: bool = False
    missing_governance_timeline_snapshot_delivery_references: list[str] = Field(default_factory=list)
    consistency_warnings: list[str] = Field(default_factory=list)
    summary: str = (
        "AI research context consumer governance timeline snapshot delivery validation is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidationContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidationContractMeta
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_validation(
    *,
    available: bool,
    governance_timeline_snapshot_delivery: AIResearchContextConsumerGovernanceTimelineSnapshotDelivery | None,
    governance_timeline_snapshot_summary: AIResearchContextConsumerGovernanceTimelineSnapshotSummary | None,
    governance_timeline_snapshot_summary_validation: AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation | None,
    governance_timeline_snapshot_validation: AIResearchContextConsumerGovernanceTimelineSnapshotValidation | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_DELIVERY_VALIDATION_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation:
    delivery_available = bool(
        governance_timeline_snapshot_delivery is not None
        and governance_timeline_snapshot_delivery.available
    )
    summary_available = bool(
        governance_timeline_snapshot_summary is not None
        and governance_timeline_snapshot_summary.available
    )
    summary_validation_available = bool(
        governance_timeline_snapshot_summary_validation is not None
        and governance_timeline_snapshot_summary_validation.available
    )
    snapshot_validation_available = bool(
        governance_timeline_snapshot_validation is not None
        and governance_timeline_snapshot_validation.available
    )

    delivery_reference = _delivery_reference(governance_timeline_snapshot_delivery)
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
    snapshot_reference = _snapshot_reference(governance_timeline_snapshot_validation)
    snapshot_visible = bool(
        governance_timeline_snapshot_validation is not None
        and governance_timeline_snapshot_validation.governance_timeline_snapshot_visible
    )
    snapshot_validation_reference = _snapshot_validation_reference(
        governance_timeline_snapshot_validation
    )
    snapshot_validation_visible = bool(
        governance_timeline_snapshot_validation is not None
        and governance_timeline_snapshot_validation.governance_timeline_snapshot_visible
    )

    if not available:
        return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation(
            validation_state="unknown",
            governance_timeline_snapshot_delivery_visible=False,
            validation_reference="not available",
            governance_timeline_snapshot_delivery_reference=delivery_reference,
            governance_timeline_snapshot_summary_reference=summary_reference,
            governance_timeline_snapshot_summary_visible=summary_visible,
            governance_timeline_snapshot_summary_validation_reference=summary_validation_reference,
            governance_timeline_snapshot_summary_validation_visible=summary_validation_visible,
            governance_timeline_snapshot_reference=snapshot_reference,
            governance_timeline_snapshot_visible=snapshot_visible,
            governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
            governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
            summary="AI research context consumer governance timeline snapshot delivery validation is unavailable.",
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidationContractMeta(
                surface=surface
            ),
        )

    missing: list[str] = []
    if not _reference_present(delivery_reference):
        missing.append("governance_timeline_snapshot_delivery_reference")
    if not _reference_present(summary_reference):
        missing.append("governance_timeline_snapshot_summary_reference")
    if not _reference_present(summary_validation_reference):
        missing.append("governance_timeline_snapshot_summary_validation_reference")
    if not _reference_present(snapshot_reference):
        missing.append("governance_timeline_snapshot_reference")
    if not _reference_present(snapshot_validation_reference):
        missing.append("governance_timeline_snapshot_validation_reference")
    if not delivery_available:
        missing.append("governance_timeline_snapshot_delivery")

    expected_state = _delivery_state(
        delivery_available=delivery_available,
        summary_available=summary_available,
        summary_validation_available=summary_validation_available,
        summary_validation_consistent=bool(
            governance_timeline_snapshot_summary_validation is not None
            and governance_timeline_snapshot_summary_validation.validation_state == "consistent"
        ),
        summary_visible=summary_visible,
        summary_validation_visible=summary_validation_visible,
    )
    expected_visible = expected_state in {"complete", "partial"}
    expected_reference = _validation_reference(
        validation_state=expected_state,
        delivery_reference=delivery_reference,
        summary_reference=summary_reference,
        summary_validation_reference=summary_validation_reference,
        snapshot_reference=snapshot_reference,
        snapshot_validation_reference=snapshot_validation_reference,
    )

    consistency_warnings: list[str] = []
    if delivery_available and governance_timeline_snapshot_delivery is not None:
        if (
            governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_state
            != expected_state
        ):
            consistency_warnings.append("Governance timeline snapshot delivery state mismatch.")
        if (
            governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_visible
            != expected_visible
        ):
            consistency_warnings.append("Governance timeline snapshot delivery visibility mismatch.")
        if (
            governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_reference
            != delivery_reference
        ):
            consistency_warnings.append("Governance timeline snapshot delivery reference mismatch.")
        if (
            governance_timeline_snapshot_delivery.governance_timeline_snapshot_summary_reference
            != summary_reference
        ):
            consistency_warnings.append("Governance timeline snapshot summary reference mismatch.")
        if (
            governance_timeline_snapshot_delivery.governance_timeline_snapshot_summary_visible
            != summary_visible
        ):
            consistency_warnings.append("Governance timeline snapshot summary visibility mismatch.")
        if (
            governance_timeline_snapshot_delivery.governance_timeline_snapshot_summary_validation_reference
            != summary_validation_reference
        ):
            consistency_warnings.append(
                "Governance timeline snapshot summary validation reference mismatch."
            )
        if (
            governance_timeline_snapshot_delivery.governance_timeline_snapshot_summary_validation_visible
            != summary_validation_visible
        ):
            consistency_warnings.append(
                "Governance timeline snapshot summary validation visibility mismatch."
            )

    if (
        summary_validation_available
        and governance_timeline_snapshot_summary_validation is not None
        and snapshot_validation_available
        and governance_timeline_snapshot_validation is not None
    ):
        if (
            governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_reference
            != snapshot_reference
        ):
            consistency_warnings.append("Governance timeline snapshot reference mismatch.")
        if (
            governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_visible
            != snapshot_visible
        ):
            consistency_warnings.append("Governance timeline snapshot visibility mismatch.")
        if (
            governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_validation_reference
            != snapshot_validation_reference
        ):
            consistency_warnings.append("Governance timeline snapshot validation reference mismatch.")
        if (
            governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_validation_visible
            != snapshot_validation_visible
        ):
            consistency_warnings.append("Governance timeline snapshot validation visibility mismatch.")

    if consistency_warnings:
        validation_state = "inconsistent"
    elif missing:
        validation_state = "partial" if delivery_available else "unknown"
    elif delivery_available:
        validation_state = "consistent"
    else:
        validation_state = "unknown"

    delivery_consistent = validation_state == "consistent"
    validation_reference = _validation_reference(
        validation_state=validation_state,
        delivery_reference=delivery_reference,
        summary_reference=summary_reference,
        summary_validation_reference=summary_validation_reference,
        snapshot_reference=snapshot_reference,
        snapshot_validation_reference=snapshot_validation_reference,
    )
    summary = _summary_text(
        validation_state=validation_state,
        governance_timeline_snapshot_delivery_visible=expected_visible,
        validation_reference=validation_reference,
        governance_timeline_snapshot_delivery_reference=delivery_reference,
        governance_timeline_snapshot_summary_reference=summary_reference,
        governance_timeline_snapshot_summary_visible=summary_visible,
        governance_timeline_snapshot_summary_validation_reference=summary_validation_reference,
        governance_timeline_snapshot_summary_validation_visible=summary_validation_visible,
        governance_timeline_snapshot_reference=snapshot_reference,
        governance_timeline_snapshot_visible=snapshot_visible,
        governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
        governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
    )
    return AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation(
        available=True,
        governance_timeline_snapshot_delivery_consistent=delivery_consistent,
        validation_state=validation_state,
        governance_timeline_snapshot_delivery_visible=expected_visible,
        validation_reference=validation_reference,
        governance_timeline_snapshot_delivery_reference=delivery_reference,
        governance_timeline_snapshot_summary_reference=summary_reference,
        governance_timeline_snapshot_summary_visible=summary_visible,
        governance_timeline_snapshot_summary_validation_reference=summary_validation_reference,
        governance_timeline_snapshot_summary_validation_visible=summary_validation_visible,
        governance_timeline_snapshot_reference=snapshot_reference,
        governance_timeline_snapshot_visible=snapshot_visible,
        governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
        governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
        missing_governance_timeline_snapshot_delivery_references=missing,
        consistency_warnings=consistency_warnings,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidationContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_delivery_validation_markdown(
    governance_timeline_snapshot_delivery_validation: (
        AIResearchContextConsumerGovernanceTimelineSnapshotDeliveryValidation | None
    ),
) -> str:
    if (
        governance_timeline_snapshot_delivery_validation is None
        or not governance_timeline_snapshot_delivery_validation.available
    ):
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot Delivery Validation",
                "",
                "AI research context consumer governance timeline snapshot delivery validation is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline snapshot delivery consistent",
            "Yes"
            if governance_timeline_snapshot_delivery_validation.governance_timeline_snapshot_delivery_consistent
            else "No",
        ),
        (
            "Governance timeline snapshot delivery state",
            governance_timeline_snapshot_delivery_validation.validation_state,
        ),
        (
            "Governance timeline snapshot delivery visible",
            "Yes"
            if governance_timeline_snapshot_delivery_validation.governance_timeline_snapshot_delivery_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery reference",
            governance_timeline_snapshot_delivery_validation.governance_timeline_snapshot_delivery_reference,
        ),
        (
            "Governance timeline snapshot summary reference",
            governance_timeline_snapshot_delivery_validation.governance_timeline_snapshot_summary_reference,
        ),
        (
            "Governance timeline snapshot summary visible",
            "Yes"
            if governance_timeline_snapshot_delivery_validation.governance_timeline_snapshot_summary_visible
            else "No",
        ),
        (
            "Governance timeline snapshot summary validation reference",
            governance_timeline_snapshot_delivery_validation.governance_timeline_snapshot_summary_validation_reference,
        ),
        (
            "Governance timeline snapshot summary validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_validation.governance_timeline_snapshot_summary_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot validation reference",
            governance_timeline_snapshot_delivery_validation.governance_timeline_snapshot_validation_reference,
        ),
        (
            "Governance timeline snapshot validation visible",
            "Yes"
            if governance_timeline_snapshot_delivery_validation.governance_timeline_snapshot_validation_visible
            else "No",
        ),
        (
            "Governance timeline snapshot delivery contract",
            f"{governance_timeline_snapshot_delivery_validation.contract_meta.version} / {governance_timeline_snapshot_delivery_validation.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot Delivery Validation",
        "",
        f"*{governance_timeline_snapshot_delivery_validation.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _delivery_state(
    *,
    delivery_available: bool,
    summary_available: bool,
    summary_validation_available: bool,
    summary_validation_consistent: bool,
    summary_visible: bool,
    summary_validation_visible: bool,
) -> Literal["complete", "partial", "unavailable", "unknown"]:
    if delivery_available and summary_available and summary_validation_available:
        if summary_validation_consistent and summary_visible and summary_validation_visible:
            return "complete"
        return "partial"
    if delivery_available or summary_available or summary_validation_available:
        return "partial"
    return "unknown"


def _validation_reference(
    *,
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"],
    delivery_reference: str,
    summary_reference: str,
    summary_validation_reference: str,
    snapshot_reference: str,
    snapshot_validation_reference: str,
) -> str:
    if validation_state == "unknown":
        return "not available"
    return (
        f"state={validation_state}; "
        f"delivery={delivery_reference}; "
        f"summary={summary_reference}; "
        f"summary_validation={summary_validation_reference}; "
        f"snapshot={snapshot_reference}; "
        f"snapshot_validation={snapshot_validation_reference}"
    )


def _reference_present(reference: str) -> bool:
    return bool(reference and reference.strip() and reference != "not available")


def _delivery_reference(
    governance_timeline_snapshot_delivery: AIResearchContextConsumerGovernanceTimelineSnapshotDelivery | None,
) -> str:
    if governance_timeline_snapshot_delivery is None:
        return "not available"
    return governance_timeline_snapshot_delivery.governance_timeline_snapshot_delivery_reference


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


def _snapshot_reference(
    governance_timeline_snapshot_validation: AIResearchContextConsumerGovernanceTimelineSnapshotValidation | None,
) -> str:
    if governance_timeline_snapshot_validation is None:
        return "not available"
    return governance_timeline_snapshot_validation.governance_timeline_snapshot_reference


def _snapshot_validation_reference(
    governance_timeline_snapshot_validation: AIResearchContextConsumerGovernanceTimelineSnapshotValidation | None,
) -> str:
    if governance_timeline_snapshot_validation is None:
        return "not available"
    return governance_timeline_snapshot_validation.validation_reference


def _summary_text(
    *,
    validation_state: str,
    governance_timeline_snapshot_delivery_visible: bool,
    validation_reference: str,
    governance_timeline_snapshot_delivery_reference: str,
    governance_timeline_snapshot_summary_reference: str,
    governance_timeline_snapshot_summary_visible: bool,
    governance_timeline_snapshot_summary_validation_reference: str,
    governance_timeline_snapshot_summary_validation_visible: bool,
    governance_timeline_snapshot_reference: str,
    governance_timeline_snapshot_visible: bool,
    governance_timeline_snapshot_validation_reference: str,
    governance_timeline_snapshot_validation_visible: bool,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot delivery validation: "
        f"state={validation_state}; "
        f"visible={'yes' if governance_timeline_snapshot_delivery_visible else 'no'}; "
        f"reference={validation_reference}; "
        f"delivery_reference={governance_timeline_snapshot_delivery_reference}; "
        f"summary_reference={governance_timeline_snapshot_summary_reference}; "
        f"summary_visible={'yes' if governance_timeline_snapshot_summary_visible else 'no'}; "
        f"summary_validation_reference={governance_timeline_snapshot_summary_validation_reference}; "
        f"summary_validation_visible={'yes' if governance_timeline_snapshot_summary_validation_visible else 'no'}; "
        f"snapshot_reference={governance_timeline_snapshot_reference}; "
        f"snapshot_visible={'yes' if governance_timeline_snapshot_visible else 'no'}; "
        f"snapshot_validation_reference={governance_timeline_snapshot_validation_reference}; "
        f"snapshot_validation_visible={'yes' if governance_timeline_snapshot_validation_visible else 'no'}"
    )

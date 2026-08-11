from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_snapshot import (
    AIResearchContextConsumerGovernanceSnapshot,
)
from ccass_core.ai_research_context_consumer_governance_snapshot_validation import (
    AIResearchContextConsumerGovernanceSnapshotValidation,
)
from ccass_core.ai_research_context_consumer_governance_timeline_summary import (
    AIResearchContextConsumerGovernanceTimelineSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot import (
    AIResearchContextConsumerGovernanceTimelineSnapshot,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_validation import (
    AIResearchContextConsumerGovernanceTimelineSnapshotValidation,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SUMMARY_VALIDATION_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SUMMARY_VALIDATION_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot_summary_validation"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidationContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SUMMARY_VALIDATION_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SUMMARY_VALIDATION_SURFACE


class AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_summary_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
    governance_timeline_snapshot_summary_visible: bool = False
    validation_reference: str = "not available"
    governance_timeline_snapshot_summary_reference: str = "not available"
    governance_timeline_snapshot_reference: str = "not available"
    governance_timeline_snapshot_visible: bool = False
    governance_timeline_snapshot_validation_reference: str = "not available"
    governance_timeline_snapshot_validation_visible: bool = False
    governance_timeline_summary_reference: str = "not available"
    governance_snapshot_reference: str = "not available"
    governance_snapshot_validation_reference: str = "not available"
    governance_continuity_reference: str = "not available"
    missing_governance_timeline_snapshot_summary_references: list[str] = Field(default_factory=list)
    consistency_warnings: list[str] = Field(default_factory=list)
    summary: str = (
        "AI research context consumer governance timeline snapshot summary validation is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidationContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidationContractMeta
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_summary_validation(
    *,
    available: bool,
    governance_timeline_snapshot_summary: object | None,
    governance_timeline_snapshot: AIResearchContextConsumerGovernanceTimelineSnapshot | None,
    governance_timeline_snapshot_validation: AIResearchContextConsumerGovernanceTimelineSnapshotValidation | None,
    governance_timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary | None,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_SUMMARY_VALIDATION_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation:
    snapshot_summary_available = bool(
        governance_timeline_snapshot_summary is not None
        and getattr(governance_timeline_snapshot_summary, "available", False)
    )
    snapshot_available = bool(governance_timeline_snapshot is not None and governance_timeline_snapshot.available)
    snapshot_validation_available = bool(
        governance_timeline_snapshot_validation is not None
        and governance_timeline_snapshot_validation.available
    )
    timeline_summary_available = bool(
        governance_timeline_summary is not None and governance_timeline_summary.available
    )
    governance_snapshot_available = bool(governance_snapshot is not None and governance_snapshot.available)
    governance_snapshot_validation_available = bool(
        governance_snapshot_validation is not None
        and governance_snapshot_validation.available
    )

    summary_reference = _summary_reference(governance_timeline_snapshot_summary)
    snapshot_reference = _snapshot_reference(governance_timeline_snapshot)
    snapshot_visible = bool(
        governance_timeline_snapshot is not None and governance_timeline_snapshot.governance_timeline_snapshot_visible
    )
    snapshot_validation_reference = _snapshot_validation_reference(governance_timeline_snapshot_validation)
    snapshot_validation_visible = bool(
        governance_timeline_snapshot_validation is not None
        and governance_timeline_snapshot_validation.governance_timeline_snapshot_visible
    )
    timeline_summary_reference = _timeline_summary_reference(governance_timeline_summary)
    governance_snapshot_reference = _governance_snapshot_reference(governance_snapshot)
    governance_snapshot_validation_reference = _governance_snapshot_validation_reference(
        governance_snapshot_validation
    )
    continuity_reference = _continuity_reference(governance_snapshot)

    if not available:
        return AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation(
            validation_state="unknown",
            governance_timeline_snapshot_summary_visible=False,
            validation_reference="not available",
            governance_timeline_snapshot_summary_reference=summary_reference,
            governance_timeline_snapshot_reference=snapshot_reference,
            governance_timeline_snapshot_visible=snapshot_visible,
            governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
            governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
            governance_timeline_summary_reference=timeline_summary_reference,
            governance_snapshot_reference=governance_snapshot_reference,
            governance_snapshot_validation_reference=governance_snapshot_validation_reference,
            governance_continuity_reference=continuity_reference,
            summary="AI research context consumer governance timeline snapshot summary validation is unavailable.",
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidationContractMeta(
                surface=surface
            ),
        )

    missing: list[str] = []
    if not _reference_present(summary_reference):
        missing.append("governance_timeline_snapshot_summary_reference")
    if not _reference_present(snapshot_reference):
        missing.append("governance_timeline_snapshot_reference")
    if not _reference_present(snapshot_validation_reference):
        missing.append("governance_timeline_snapshot_validation_reference")
    if not _reference_present(timeline_summary_reference):
        missing.append("governance_timeline_summary_reference")
    if not _reference_present(governance_snapshot_reference):
        missing.append("governance_snapshot_reference")
    if not _reference_present(governance_snapshot_validation_reference):
        missing.append("governance_snapshot_validation_reference")
    if not _reference_present(continuity_reference):
        missing.append("governance_continuity_reference")
    if not snapshot_summary_available:
        missing.append("governance_timeline_snapshot_summary")

    summary_value = governance_timeline_snapshot_summary
    expected_state = (
        summary_value.governance_timeline_snapshot_summary_state
        if snapshot_summary_available and summary_value is not None
        else "unknown"
    )
    expected_visible = bool(
        summary_value.governance_timeline_snapshot_summary_visible
        if snapshot_summary_available and summary_value is not None
        else False
    )
    expected_reference = _validation_reference(
        validation_state=expected_state,
        governance_timeline_snapshot_summary_reference=summary_reference,
        governance_timeline_snapshot_reference=snapshot_reference,
        governance_timeline_snapshot_visible=snapshot_visible,
        governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
        governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
        governance_timeline_summary_reference=timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_continuity_reference=continuity_reference,
    )
    consistency_warnings: list[str] = []
    if snapshot_summary_available and summary_value is not None:
        if summary_value.governance_timeline_snapshot_summary_state != expected_state:
            consistency_warnings.append("Governance timeline snapshot summary state mismatch.")
        if summary_value.governance_timeline_snapshot_summary_visible != expected_visible:
            consistency_warnings.append("Governance timeline snapshot summary visibility mismatch.")
        if summary_value.governance_timeline_snapshot_summary_reference != summary_reference:
            consistency_warnings.append("Governance timeline snapshot summary reference mismatch.")
        if summary_value.governance_timeline_snapshot_reference != snapshot_reference:
            consistency_warnings.append("Governance timeline snapshot reference mismatch.")
        if summary_value.governance_timeline_snapshot_visible != snapshot_visible:
            consistency_warnings.append("Governance timeline snapshot visibility mismatch.")
        if (
            summary_value.governance_timeline_snapshot_validation_reference
            != snapshot_validation_reference
        ):
            consistency_warnings.append("Governance timeline snapshot validation reference mismatch.")
        if (
            summary_value.governance_timeline_snapshot_validation_visible
            != snapshot_validation_visible
        ):
            consistency_warnings.append("Governance timeline snapshot validation visibility mismatch.")
        if summary_value.governance_timeline_summary_reference != timeline_summary_reference:
            consistency_warnings.append("Governance timeline summary reference mismatch.")
        if summary_value.governance_snapshot_reference != governance_snapshot_reference:
            consistency_warnings.append("Governance snapshot reference mismatch.")
        if (
            summary_value.governance_snapshot_validation_reference
            != governance_snapshot_validation_reference
        ):
            consistency_warnings.append("Governance snapshot validation reference mismatch.")
        if summary_value.governance_continuity_reference != continuity_reference:
            consistency_warnings.append("Governance continuity reference mismatch.")

    if consistency_warnings:
        validation_state = "inconsistent"
    elif missing:
        validation_state = "partial" if snapshot_summary_available else "unknown"
    elif snapshot_summary_available:
        validation_state = "consistent"
    else:
        validation_state = "unknown"

    governance_timeline_snapshot_summary_consistent = validation_state == "consistent"
    validation_reference = _validation_reference(
        validation_state=validation_state,
        governance_timeline_snapshot_summary_reference=summary_reference,
        governance_timeline_snapshot_reference=snapshot_reference,
        governance_timeline_snapshot_visible=snapshot_visible,
        governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
        governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
        governance_timeline_summary_reference=timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_continuity_reference=continuity_reference,
    )
    summary = _summary_text(
        validation_state=validation_state,
        governance_timeline_snapshot_summary_visible=expected_visible,
        validation_reference=validation_reference,
        governance_timeline_snapshot_summary_reference=summary_reference,
        governance_timeline_snapshot_reference=snapshot_reference,
        governance_timeline_snapshot_visible=snapshot_visible,
        governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
        governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
        governance_timeline_summary_reference=timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_continuity_reference=continuity_reference,
    )
    return AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation(
        available=True,
        governance_timeline_snapshot_summary_consistent=governance_timeline_snapshot_summary_consistent,
        validation_state=validation_state,
        governance_timeline_snapshot_summary_visible=expected_visible,
        validation_reference=validation_reference,
        governance_timeline_snapshot_summary_reference=summary_reference,
        governance_timeline_snapshot_reference=snapshot_reference,
        governance_timeline_snapshot_visible=snapshot_visible,
        governance_timeline_snapshot_validation_reference=snapshot_validation_reference,
        governance_timeline_snapshot_validation_visible=snapshot_validation_visible,
        governance_timeline_summary_reference=timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_continuity_reference=continuity_reference,
        missing_governance_timeline_snapshot_summary_references=missing,
        consistency_warnings=consistency_warnings,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidationContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_summary_validation_markdown(
    governance_timeline_snapshot_summary_validation: AIResearchContextConsumerGovernanceTimelineSnapshotSummaryValidation | None,
) -> str:
    if (
        governance_timeline_snapshot_summary_validation is None
        or not governance_timeline_snapshot_summary_validation.available
    ):
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot Summary Validation",
                "",
                "AI research context consumer governance timeline snapshot summary validation is unavailable.",
            ]
        )

    rows = [
        (
            "Validation state",
            governance_timeline_snapshot_summary_validation.validation_state,
        ),
        (
            "Summary visible",
            "Yes"
            if governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_summary_visible
            else "No",
        ),
        (
            "Summary reference",
            governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_summary_reference,
        ),
        (
            "Snapshot reference",
            governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_reference,
        ),
        (
            "Snapshot visible",
            "Yes"
            if governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_visible
            else "No",
        ),
        (
            "Snapshot validation reference",
            governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_validation_reference,
        ),
        (
            "Snapshot validation visible",
            "Yes"
            if governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_validation_visible
            else "No",
        ),
        (
            "Timeline summary reference",
            governance_timeline_snapshot_summary_validation.governance_timeline_summary_reference,
        ),
        (
            "Snapshot governance reference",
            governance_timeline_snapshot_summary_validation.governance_snapshot_reference,
        ),
        (
            "Snapshot governance validation reference",
            governance_timeline_snapshot_summary_validation.governance_snapshot_validation_reference,
        ),
        (
            "Continuity reference",
            governance_timeline_snapshot_summary_validation.governance_continuity_reference,
        ),
        (
            "Consistency warnings",
            _join_list(governance_timeline_snapshot_summary_validation.consistency_warnings),
        ),
        (
            "Missing references",
            _join_list(
                governance_timeline_snapshot_summary_validation.missing_governance_timeline_snapshot_summary_references
            ),
        ),
        (
            "Summary validation contract",
            f"{governance_timeline_snapshot_summary_validation.contract_meta.version} / {governance_timeline_snapshot_summary_validation.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot Summary Validation",
        "",
        f"*{governance_timeline_snapshot_summary_validation.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _validation_reference(
    *,
    validation_state: str,
    governance_timeline_snapshot_summary_reference: str,
    governance_timeline_snapshot_reference: str,
    governance_timeline_snapshot_visible: bool,
    governance_timeline_snapshot_validation_reference: str,
    governance_timeline_snapshot_validation_visible: bool,
    governance_timeline_summary_reference: str,
    governance_snapshot_reference: str,
    governance_snapshot_validation_reference: str,
    governance_continuity_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot summary validation: "
        f"state={validation_state}; "
        f"summary={governance_timeline_snapshot_summary_reference}; "
        f"snapshot={governance_timeline_snapshot_reference}; "
        f"snapshot_visible={'yes' if governance_timeline_snapshot_visible else 'no'}; "
        f"snapshot_validation={governance_timeline_snapshot_validation_reference}; "
        f"snapshot_validation_visible={'yes' if governance_timeline_snapshot_validation_visible else 'no'}; "
        f"timeline_summary={governance_timeline_summary_reference}; "
        f"snapshot_reference={governance_snapshot_reference}; "
        f"snapshot_validation_reference={governance_snapshot_validation_reference}; "
        f"continuity={governance_continuity_reference}"
    )


def _summary_text(
    *,
    validation_state: str,
    governance_timeline_snapshot_summary_visible: bool,
    validation_reference: str,
    governance_timeline_snapshot_summary_reference: str,
    governance_timeline_snapshot_reference: str,
    governance_timeline_snapshot_visible: bool,
    governance_timeline_snapshot_validation_reference: str,
    governance_timeline_snapshot_validation_visible: bool,
    governance_timeline_summary_reference: str,
    governance_snapshot_reference: str,
    governance_snapshot_validation_reference: str,
    governance_continuity_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot summary validation: "
        f"state={validation_state}; "
        f"visible={'yes' if governance_timeline_snapshot_summary_visible else 'no'}; "
        f"reference={validation_reference}; "
        f"summary={governance_timeline_snapshot_summary_reference}; "
        f"snapshot={governance_timeline_snapshot_reference}; "
        f"snapshot_visible={'yes' if governance_timeline_snapshot_visible else 'no'}; "
        f"snapshot_validation={governance_timeline_snapshot_validation_reference}; "
        f"snapshot_validation_visible={'yes' if governance_timeline_snapshot_validation_visible else 'no'}; "
        f"timeline_summary={governance_timeline_summary_reference}; "
        f"snapshot_reference={governance_snapshot_reference}; "
        f"snapshot_validation_reference={governance_snapshot_validation_reference}; "
        f"continuity={governance_continuity_reference}"
    )


def _summary_reference(
    governance_timeline_snapshot_summary: object | None,
) -> str:
    if governance_timeline_snapshot_summary is None or not getattr(
        governance_timeline_snapshot_summary, "available", False
    ):
        return "not available"
    return governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_reference


def _snapshot_reference(snapshot: AIResearchContextConsumerGovernanceTimelineSnapshot | None) -> str:
    if snapshot is None or not snapshot.available:
        return "not available"
    return snapshot.governance_timeline_snapshot_reference


def _snapshot_validation_reference(
    snapshot_validation: AIResearchContextConsumerGovernanceTimelineSnapshotValidation | None,
) -> str:
    if snapshot_validation is None or not snapshot_validation.available:
        return "not available"
    return snapshot_validation.validation_reference


def _timeline_summary_reference(
    timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary | None,
) -> str:
    if timeline_summary is None or not timeline_summary.available:
        return "not available"
    return timeline_summary.governance_timeline_summary_reference


def _governance_snapshot_reference(
    snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
) -> str:
    if snapshot is None or not snapshot.available:
        return "not available"
    return snapshot.governance_snapshot_reference


def _governance_snapshot_validation_reference(
    snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
) -> str:
    if snapshot_validation is None or not snapshot_validation.available:
        return "not available"
    return snapshot_validation.validation_reference


def _continuity_reference(snapshot: AIResearchContextConsumerGovernanceSnapshot | None) -> str:
    if snapshot is None or not snapshot.available:
        return "not available"
    return snapshot.governance_continuity_reference


def _reference_present(reference: str | None) -> bool:
    if reference is None:
        return False
    return reference.strip() != "" and reference != "not available"


def _join_list(values: list[str]) -> str:
    return "none" if not values else " | ".join(values)

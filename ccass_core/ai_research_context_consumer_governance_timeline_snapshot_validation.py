from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_snapshot import (
    AIResearchContextConsumerGovernanceSnapshot,
)
from ccass_core.ai_research_context_consumer_governance_snapshot_validation import (
    AIResearchContextConsumerGovernanceSnapshotValidation,
)
from ccass_core.ai_research_context_consumer_governance_summary import (
    AIResearchContextConsumerGovernanceSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline import (
    AIResearchContextConsumerGovernanceTimeline,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot import (
    AIResearchContextConsumerGovernanceTimelineSnapshot,
)
from ccass_core.ai_research_context_consumer_governance_timeline_summary import (
    AIResearchContextConsumerGovernanceTimelineSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline_validation import (
    AIResearchContextConsumerGovernanceTimelineValidation,
)
from ccass_core.ai_research_context_consumer_health import (
    AIResearchContextConsumerHealthIndicator,
)
from ccass_core.ai_research_context_consumer_readiness import (
    AIResearchContextConsumerReadinessStatus,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_VALIDATION_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_VALIDATION_SURFACE = (
    "ai_research_context_consumer_governance_timeline_snapshot_validation"
)


class AIResearchContextConsumerGovernanceTimelineSnapshotValidationContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_VALIDATION_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_VALIDATION_SURFACE


class AIResearchContextConsumerGovernanceTimelineSnapshotValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_snapshot_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
    governance_timeline_snapshot_visible: bool = False
    validation_reference: str = "not available"
    governance_timeline_snapshot_reference: str = "not available"
    governance_timeline_reference: str = "not available"
    governance_timeline_validation_reference: str = "not available"
    governance_timeline_summary_reference: str = "not available"
    governance_snapshot_reference: str = "not available"
    governance_snapshot_validation_reference: str = "not available"
    governance_timeline_snapshot_summary_reference: str = "not available"
    governance_continuity_reference: str = "not available"
    readiness_reference: str = "not available"
    health_reference: str = "not available"
    version_reference: str = "not available"
    compatibility_reference: str = "not available"
    capability_reference: str = "not available"
    consumer_ready: bool = False
    timeline_continuity_consistent: bool = False
    readiness_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    health_status: Literal["healthy", "partial", "unavailable", "unknown"] = "unknown"
    missing_governance_timeline_snapshot_references: list[str] = Field(default_factory=list)
    consistency_warnings: list[str] = Field(default_factory=list)
    summary: str = (
        "AI research context consumer governance timeline snapshot validation is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceTimelineSnapshotValidationContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineSnapshotValidationContractMeta
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_validation(
    *,
    available: bool,
    governance_timeline_snapshot: AIResearchContextConsumerGovernanceTimelineSnapshot | None,
    governance_timeline: AIResearchContextConsumerGovernanceTimeline | None,
    governance_timeline_validation: AIResearchContextConsumerGovernanceTimelineValidation | None,
    governance_timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary | None,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    readiness_status: AIResearchContextConsumerReadinessStatus | None,
    health_indicator: AIResearchContextConsumerHealthIndicator | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_SNAPSHOT_VALIDATION_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineSnapshotValidation:
    timeline_snapshot_available = bool(
        governance_timeline_snapshot is not None and governance_timeline_snapshot.available
    )
    timeline_available = bool(governance_timeline is not None and governance_timeline.available)
    timeline_validation_available = bool(
        governance_timeline_validation is not None and governance_timeline_validation.available
    )
    timeline_summary_available = bool(
        governance_timeline_summary is not None and governance_timeline_summary.available
    )
    snapshot_available = bool(governance_snapshot is not None and governance_snapshot.available)
    snapshot_validation_available = bool(
        governance_snapshot_validation is not None and governance_snapshot_validation.available
    )
    readiness_reference = (
        readiness_status.readiness_reference if readiness_status is not None else "not available"
    )
    health_reference = (
        health_indicator.health_reference if health_indicator is not None else "not available"
    )
    consumer_ready = bool(readiness_status.consumer_ready if readiness_status is not None else False)
    readiness_state = (
        readiness_status.readiness_status if readiness_status is not None else "unknown"
    )
    health_state = health_indicator.health_status if health_indicator is not None else "unknown"
    governance_timeline_reference = _timeline_reference(governance_timeline)
    governance_timeline_validation_reference = _timeline_validation_reference(
        governance_timeline_validation
    )
    governance_timeline_summary_reference = _timeline_summary_reference(governance_timeline_summary)
    governance_snapshot_reference = _snapshot_reference(governance_snapshot)
    governance_snapshot_validation_reference = _snapshot_validation_reference(
        governance_snapshot_validation
    )
    governance_timeline_snapshot_summary_reference = _timeline_snapshot_summary_reference(
        governance_timeline_snapshot
    )
    governance_continuity_reference = _continuity_reference(governance_snapshot)

    if not available:
        return AIResearchContextConsumerGovernanceTimelineSnapshotValidation(
            governance_timeline_snapshot_consistent=False,
            validation_state="unknown",
            governance_timeline_snapshot_visible=False,
            validation_reference="not available",
            governance_timeline_snapshot_reference=(
                governance_timeline_snapshot.governance_timeline_snapshot_reference
                if governance_timeline_snapshot is not None
                else "not available"
            ),
            governance_timeline_reference=governance_timeline_reference,
            governance_timeline_validation_reference=governance_timeline_validation_reference,
            governance_timeline_summary_reference=governance_timeline_summary_reference,
            governance_snapshot_reference=governance_snapshot_reference,
            governance_snapshot_validation_reference=governance_snapshot_validation_reference,
            governance_timeline_snapshot_summary_reference=governance_timeline_snapshot_summary_reference,
            governance_continuity_reference=governance_continuity_reference,
            readiness_reference=readiness_reference,
            health_reference=health_reference,
            version_reference=version_reference,
            compatibility_reference=compatibility_reference,
            capability_reference=capability_reference,
            consumer_ready=consumer_ready,
            timeline_continuity_consistent=bool(
                governance_timeline_validation.timeline_continuity_consistent
                if governance_timeline_validation is not None
                else False
            ),
            readiness_status=readiness_state,
            health_status=health_state,
            summary=(
                "AI research context consumer governance timeline snapshot validation is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotValidationContractMeta(
                surface=surface
            ),
        )

    missing_governance_timeline_snapshot_references: list[str] = []
    if not _reference_present(
        governance_timeline_snapshot.governance_timeline_snapshot_reference
        if timeline_snapshot_available
        else None
    ):
        missing_governance_timeline_snapshot_references.append(
            "governance_timeline_snapshot_reference"
        )
    if not _reference_present(governance_timeline_reference):
        missing_governance_timeline_snapshot_references.append("governance_timeline_reference")
    if not _reference_present(governance_timeline_validation_reference):
        missing_governance_timeline_snapshot_references.append(
            "governance_timeline_validation_reference"
        )
    if not _reference_present(governance_timeline_summary_reference):
        missing_governance_timeline_snapshot_references.append(
            "governance_timeline_summary_reference"
        )
    if not _reference_present(governance_snapshot_reference):
        missing_governance_timeline_snapshot_references.append("governance_snapshot_reference")
    if not _reference_present(governance_snapshot_validation_reference):
        missing_governance_timeline_snapshot_references.append(
            "governance_snapshot_validation_reference"
        )
    if not _reference_present(governance_timeline_snapshot_summary_reference):
        missing_governance_timeline_snapshot_references.append(
            "governance_timeline_snapshot_summary_reference"
        )
    if not _reference_present(governance_continuity_reference):
        missing_governance_timeline_snapshot_references.append("governance_continuity_reference")
    if not _reference_present(readiness_reference):
        missing_governance_timeline_snapshot_references.append("readiness_reference")
    if not _reference_present(health_reference):
        missing_governance_timeline_snapshot_references.append("health_reference")
    if not _reference_present(version_reference):
        missing_governance_timeline_snapshot_references.append("version_reference")
    if not _reference_present(compatibility_reference):
        missing_governance_timeline_snapshot_references.append("compatibility_reference")
    if not _reference_present(capability_reference):
        missing_governance_timeline_snapshot_references.append("capability_reference")
    if governance_timeline_snapshot is None or not governance_timeline_snapshot.available:
        missing_governance_timeline_snapshot_references.append("governance_timeline_snapshot")

    expected_state = _expected_snapshot_state(
        governance_timeline=governance_timeline,
        governance_timeline_validation=governance_timeline_validation,
        governance_timeline_summary=governance_timeline_summary,
        governance_snapshot=governance_snapshot,
        governance_snapshot_validation=governance_snapshot_validation,
    )
    expected_visible = expected_state in {"complete", "partial"}
    expected_continuity_consistent = expected_state == "complete"
    expected_snapshot_reference = _snapshot_reference_text(
        governance_timeline_snapshot_state=expected_state,
        governance_timeline_reference=governance_timeline_reference,
        governance_timeline_validation_reference=governance_timeline_validation_reference,
        governance_timeline_summary_reference=governance_timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_continuity_reference=governance_continuity_reference,
    )
    expected_validation_reference = _validation_reference(
        validation_state=expected_state,
        governance_timeline_snapshot_reference=expected_snapshot_reference,
        governance_timeline_reference=governance_timeline_reference,
        governance_timeline_validation_reference=governance_timeline_validation_reference,
        governance_timeline_summary_reference=governance_timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_timeline_snapshot_summary_reference=governance_timeline_snapshot_summary_reference,
        governance_continuity_reference=governance_continuity_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        missing_governance_timeline_snapshot_references=missing_governance_timeline_snapshot_references,
    )
    expected_summary = _snapshot_summary_text(
        governance_timeline_snapshot_state=expected_state,
        governance_timeline_snapshot_visible=expected_visible,
        governance_timeline_snapshot_reference=expected_snapshot_reference,
        governance_timeline_reference=governance_timeline_reference,
        governance_timeline_validation_reference=governance_timeline_validation_reference,
        governance_timeline_summary_reference=governance_timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_continuity_reference=governance_continuity_reference,
    )

    consistency_warnings: list[str] = []
    if timeline_snapshot_available:
        if governance_timeline_snapshot.governance_timeline_snapshot_state != expected_state:
            consistency_warnings.append("Governance timeline snapshot state mismatch.")
        if governance_timeline_snapshot.governance_timeline_snapshot_visible != expected_visible:
            consistency_warnings.append("Governance timeline snapshot visibility mismatch.")
        if governance_timeline_snapshot.governance_timeline_snapshot_reference != expected_snapshot_reference:
            consistency_warnings.append("Governance timeline snapshot reference mismatch.")
        if governance_timeline_snapshot.summary != expected_summary:
            consistency_warnings.append("Governance timeline snapshot summary mismatch.")
        if (
            governance_timeline_snapshot.governance_timeline_snapshot_summary
            != expected_summary
        ):
            consistency_warnings.append(
                "Governance timeline snapshot summary reference mismatch."
            )
        if governance_timeline_snapshot.governance_timeline_reference != governance_timeline_reference:
            consistency_warnings.append("Governance timeline reference mismatch.")
        if (
            governance_timeline_snapshot.governance_timeline_validation_reference
            != governance_timeline_validation_reference
        ):
            consistency_warnings.append("Governance timeline validation reference mismatch.")
        if (
            governance_timeline_snapshot.governance_timeline_summary_reference
            != governance_timeline_summary_reference
        ):
            consistency_warnings.append("Governance timeline summary reference mismatch.")
        if governance_timeline_snapshot.governance_snapshot_reference != governance_snapshot_reference:
            consistency_warnings.append("Governance snapshot reference mismatch.")
        if (
            governance_timeline_snapshot.governance_snapshot_validation_reference
            != governance_snapshot_validation_reference
        ):
            consistency_warnings.append("Governance snapshot validation reference mismatch.")
        if (
            governance_timeline_snapshot.governance_continuity_reference
            != governance_continuity_reference
        ):
            consistency_warnings.append("Governance continuity reference mismatch.")

    all_missing_present = not missing_governance_timeline_snapshot_references
    no_warnings = not consistency_warnings
    timeline_snapshot_consistent = bool(
        timeline_snapshot_available and all_missing_present and no_warnings
    )
    timeline_continuity_consistent = bool(
        governance_timeline_validation.timeline_continuity_consistent
        if governance_timeline_validation is not None
        else expected_continuity_consistent
    )
    if timeline_snapshot_consistent:
        validation_state = "consistent"
    elif consistency_warnings:
        validation_state = "inconsistent"
    elif timeline_snapshot_available:
        validation_state = "partial"
    else:
        validation_state = "unknown"
    validation_reference = _validation_reference(
        validation_state=validation_state,
        governance_timeline_snapshot_reference=expected_snapshot_reference,
        governance_timeline_reference=governance_timeline_reference,
        governance_timeline_validation_reference=governance_timeline_validation_reference,
        governance_timeline_summary_reference=governance_timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_timeline_snapshot_summary_reference=governance_timeline_snapshot_summary_reference,
        governance_continuity_reference=governance_continuity_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        missing_governance_timeline_snapshot_references=missing_governance_timeline_snapshot_references,
    )
    summary = _summary_text(
        governance_timeline_snapshot_state=validation_state,
        governance_timeline_snapshot_visible=validation_state in {"consistent", "partial"},
        governance_timeline_snapshot_reference=validation_reference,
        governance_timeline_reference=governance_timeline_reference,
        governance_timeline_validation_reference=governance_timeline_validation_reference,
        governance_timeline_summary_reference=governance_timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_timeline_snapshot_summary_reference=governance_timeline_snapshot_summary_reference,
        governance_continuity_reference=governance_continuity_reference,
        consumer_ready=consumer_ready,
        timeline_continuity_consistent=timeline_continuity_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
    )
    return AIResearchContextConsumerGovernanceTimelineSnapshotValidation(
        available=True,
        governance_timeline_snapshot_consistent=timeline_snapshot_consistent,
        validation_state=validation_state,
        governance_timeline_snapshot_visible=validation_state in {"consistent", "partial"},
        validation_reference=validation_reference,
        governance_timeline_snapshot_reference=expected_snapshot_reference,
        governance_timeline_reference=governance_timeline_reference,
        governance_timeline_validation_reference=governance_timeline_validation_reference,
        governance_timeline_summary_reference=governance_timeline_summary_reference,
        governance_snapshot_reference=governance_snapshot_reference,
        governance_snapshot_validation_reference=governance_snapshot_validation_reference,
        governance_timeline_snapshot_summary_reference=governance_timeline_snapshot_summary_reference,
        governance_continuity_reference=governance_continuity_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        consumer_ready=consumer_ready,
        timeline_continuity_consistent=timeline_continuity_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
        missing_governance_timeline_snapshot_references=missing_governance_timeline_snapshot_references,
        consistency_warnings=consistency_warnings,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineSnapshotValidationContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_snapshot_validation_markdown(
    governance_timeline_snapshot_validation: AIResearchContextConsumerGovernanceTimelineSnapshotValidation | None,
) -> str:
    if (
        governance_timeline_snapshot_validation is None
        or not governance_timeline_snapshot_validation.available
    ):
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Snapshot Validation",
                "",
                "AI research context consumer governance timeline snapshot validation is unavailable.",
            ]
        )

    rows = [
        (
            "Governance timeline snapshot validation state",
            governance_timeline_snapshot_validation.validation_state,
        ),
        (
            "Governance timeline snapshot validation visible",
            "Yes"
            if governance_timeline_snapshot_validation.governance_timeline_snapshot_visible
            else "No",
        ),
        (
            "Governance timeline snapshot validation reference",
            governance_timeline_snapshot_validation.validation_reference,
        ),
        (
            "Governance timeline snapshot reference",
            governance_timeline_snapshot_validation.governance_timeline_snapshot_reference,
        ),
        (
            "Governance timeline reference",
            governance_timeline_snapshot_validation.governance_timeline_reference,
        ),
        (
            "Governance timeline validation reference",
            governance_timeline_snapshot_validation.governance_timeline_validation_reference,
        ),
        (
            "Governance timeline summary reference",
            governance_timeline_snapshot_validation.governance_timeline_summary_reference,
        ),
        (
            "Governance snapshot reference",
            governance_timeline_snapshot_validation.governance_snapshot_reference,
        ),
        (
            "Governance snapshot validation reference",
            governance_timeline_snapshot_validation.governance_snapshot_validation_reference,
        ),
        (
            "Governance timeline snapshot summary reference",
            governance_timeline_snapshot_validation.governance_timeline_snapshot_summary_reference,
        ),
        (
            "Governance continuity reference",
            governance_timeline_snapshot_validation.governance_continuity_reference,
        ),
        ("Readiness reference", governance_timeline_snapshot_validation.readiness_reference),
        ("Health reference", governance_timeline_snapshot_validation.health_reference),
        (
            "Missing references",
            _join_list(
                tuple(
                    governance_timeline_snapshot_validation.missing_governance_timeline_snapshot_references
                )
            ),
        ),
        (
            "Consistency warnings",
            _join_list(tuple(governance_timeline_snapshot_validation.consistency_warnings)),
        ),
        (
            "Governance timeline snapshot validation contract",
            f"{governance_timeline_snapshot_validation.contract_meta.version} / {governance_timeline_snapshot_validation.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Snapshot Validation",
        "",
        f"*{governance_timeline_snapshot_validation.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _expected_snapshot_state(
    *,
    governance_timeline: AIResearchContextConsumerGovernanceTimeline | None,
    governance_timeline_validation: AIResearchContextConsumerGovernanceTimelineValidation | None,
    governance_timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary | None,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
) -> Literal["complete", "partial", "unavailable", "unknown"]:
    if governance_timeline is None or not governance_timeline.available:
        return "unavailable"
    if (
        governance_timeline_validation is not None
        and governance_timeline_validation.available
        and governance_timeline_validation.validation_state == "consistent"
        and governance_snapshot_validation is not None
        and governance_snapshot_validation.available
        and governance_snapshot_validation.validation_state == "consistent"
        and governance_timeline_summary is not None
        and governance_timeline_summary.available
        and governance_snapshot is not None
        and governance_snapshot.available
    ):
        return "complete"
    if (
        governance_timeline_validation is not None
        and governance_timeline_validation.available
    ) or (
        governance_snapshot_validation is not None and governance_snapshot_validation.available
    ) or (
        governance_timeline_summary is not None and governance_timeline_summary.available
    ) or (governance_snapshot is not None and governance_snapshot.available):
        return "partial"
    return "unknown"


def _validation_reference(
    *,
    validation_state: str,
    governance_timeline_snapshot_reference: str,
    governance_timeline_reference: str,
    governance_timeline_validation_reference: str,
    governance_timeline_summary_reference: str,
    governance_snapshot_reference: str,
    governance_snapshot_validation_reference: str,
    governance_timeline_snapshot_summary_reference: str,
    governance_continuity_reference: str,
    readiness_reference: str,
    health_reference: str,
    missing_governance_timeline_snapshot_references: list[str],
) -> str:
    return (
        "AI research context consumer governance timeline snapshot validation: "
        f"state={validation_state}; "
        f"snapshot={governance_timeline_snapshot_reference}; "
        f"timeline={governance_timeline_reference}; "
        f"timeline_validation={governance_timeline_validation_reference}; "
        f"timeline_summary={governance_timeline_summary_reference}; "
        f"snapshot_reference={governance_snapshot_reference}; "
        f"snapshot_validation={governance_snapshot_validation_reference}; "
        f"timeline_snapshot_summary={governance_timeline_snapshot_summary_reference}; "
        f"continuity={governance_continuity_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"missing={_join_list(tuple(missing_governance_timeline_snapshot_references))}"
    )


def _snapshot_reference_text(
    *,
    governance_timeline_snapshot_state: str,
    governance_timeline_reference: str,
    governance_timeline_validation_reference: str,
    governance_timeline_summary_reference: str,
    governance_snapshot_reference: str,
    governance_snapshot_validation_reference: str,
    governance_continuity_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot: "
        f"state={governance_timeline_snapshot_state}; "
        f"timeline={governance_timeline_reference}; "
        f"timeline_validation={governance_timeline_validation_reference}; "
        f"timeline_summary={governance_timeline_summary_reference}; "
        f"snapshot={governance_snapshot_reference}; "
        f"snapshot_validation={governance_snapshot_validation_reference}; "
        f"continuity={governance_continuity_reference}"
    )


def _snapshot_summary_text(
    *,
    governance_timeline_snapshot_state: str,
    governance_timeline_snapshot_visible: bool,
    governance_timeline_snapshot_reference: str,
    governance_timeline_reference: str,
    governance_timeline_validation_reference: str,
    governance_timeline_summary_reference: str,
    governance_snapshot_reference: str,
    governance_snapshot_validation_reference: str,
    governance_continuity_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot: "
        f"state={governance_timeline_snapshot_state}; "
        f"visible={'yes' if governance_timeline_snapshot_visible else 'no'}; "
        f"reference={governance_timeline_snapshot_reference}; "
        f"timeline={governance_timeline_reference}; "
        f"timeline_validation={governance_timeline_validation_reference}; "
        f"timeline_summary={governance_timeline_summary_reference}; "
        f"snapshot={governance_snapshot_reference}; "
        f"snapshot_validation={governance_snapshot_validation_reference}; "
        f"continuity={governance_continuity_reference}"
    )


def _snapshot_reference(
    snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
) -> str:
    if snapshot is None or not snapshot.available:
        return "not available"
    return snapshot.governance_snapshot_reference


def _snapshot_validation_reference(
    snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
) -> str:
    if snapshot_validation is None or not snapshot_validation.available:
        return "not available"
    return snapshot_validation.validation_reference


def _timeline_reference(
    timeline: AIResearchContextConsumerGovernanceTimeline | None,
) -> str:
    if timeline is None or not timeline.available:
        return "not available"
    return timeline.governance_timeline_reference


def _timeline_validation_reference(
    timeline_validation: AIResearchContextConsumerGovernanceTimelineValidation | None,
) -> str:
    if timeline_validation is None or not timeline_validation.available:
        return "not available"
    return timeline_validation.validation_reference


def _timeline_summary_reference(
    timeline_summary: AIResearchContextConsumerGovernanceTimelineSummary | None,
) -> str:
    if timeline_summary is None or not timeline_summary.available:
        return "not available"
    return timeline_summary.governance_timeline_summary_reference


def _timeline_snapshot_summary_reference(
    timeline_snapshot: AIResearchContextConsumerGovernanceTimelineSnapshot | None,
) -> str:
    if timeline_snapshot is None or not timeline_snapshot.available:
        return "not available"
    return timeline_snapshot.summary


def _continuity_reference(
    snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
) -> str:
    if snapshot is None or not snapshot.available:
        return "not available"
    return snapshot.governance_continuity_reference


def _reference_present(value: str | None) -> bool:
    return bool(value is not None and str(value).strip() and value != "not available")


def _join_list(values: tuple[str, ...]) -> str:
    if not values:
        return "not available"
    return " | ".join(values)


def _summary_text(
    *,
    governance_timeline_snapshot_state: str,
    governance_timeline_snapshot_visible: bool,
    governance_timeline_snapshot_reference: str,
    governance_timeline_reference: str,
    governance_timeline_validation_reference: str,
    governance_timeline_summary_reference: str,
    governance_snapshot_reference: str,
    governance_snapshot_validation_reference: str,
    governance_timeline_snapshot_summary_reference: str,
    governance_continuity_reference: str,
    consumer_ready: bool,
    timeline_continuity_consistent: bool,
    readiness_status: str,
    health_status: str,
) -> str:
    return (
        "AI research context consumer governance timeline snapshot validation: "
        f"state={governance_timeline_snapshot_state}; "
        f"visible={'yes' if governance_timeline_snapshot_visible else 'no'}; "
        f"reference={governance_timeline_snapshot_reference}; "
        f"timeline={governance_timeline_reference}; "
        f"timeline_validation={governance_timeline_validation_reference}; "
        f"timeline_summary={governance_timeline_summary_reference}; "
        f"snapshot={governance_snapshot_reference}; "
        f"snapshot_validation={governance_snapshot_validation_reference}; "
        f"timeline_snapshot_summary={governance_timeline_snapshot_summary_reference}; "
        f"continuity={governance_continuity_reference}; "
        f"consumer_ready={'yes' if consumer_ready else 'no'}; "
        f"timeline_continuity_consistent={'yes' if timeline_continuity_consistent else 'no'}; "
        f"readiness={readiness_status}; "
        f"health={health_status}"
    )

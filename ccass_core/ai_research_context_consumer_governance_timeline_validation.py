from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_snapshot import (
    AIResearchContextConsumerGovernanceSnapshot,
)
from ccass_core.ai_research_context_consumer_governance_snapshot_validation import (
    AIResearchContextConsumerGovernanceSnapshotValidation,
)
from ccass_core.ai_research_context_consumer_governance_status import (
    AIResearchContextConsumerGovernanceStatus,
)
from ccass_core.ai_research_context_consumer_governance_status_validation import (
    AIResearchContextConsumerGovernanceStatusValidation,
)
from ccass_core.ai_research_context_consumer_governance_summary import (
    AIResearchContextConsumerGovernanceSummary,
)
from ccass_core.ai_research_context_consumer_governance_timeline import (
    AIResearchContextConsumerGovernanceTimeline,
)
from ccass_core.ai_research_context_consumer_health import (
    AIResearchContextConsumerHealthIndicator,
)
from ccass_core.ai_research_context_consumer_readiness import (
    AIResearchContextConsumerReadinessStatus,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_VALIDATION_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_VALIDATION_SURFACE = (
    "ai_research_context_consumer_governance_timeline_validation"
)


class AIResearchContextConsumerGovernanceTimelineValidationContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_VALIDATION_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_VALIDATION_SURFACE


class AIResearchContextConsumerGovernanceTimelineValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_timeline_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
    governance_timeline_visible: bool = False
    validation_reference: str = "not available"
    governance_timeline_reference: str = "not available"
    governance_state_sequence_reference: str = "not available"
    governance_continuity_reference: str = "not available"
    governance_summary_reference: str = "not available"
    governance_status_reference: str = "not available"
    governance_status_validation_reference: str = "not available"
    governance_snapshot_validation_reference: str = "not available"
    governance_snapshot_reference: str = "not available"
    readiness_reference: str = "not available"
    health_reference: str = "not available"
    version_reference: str = "not available"
    compatibility_reference: str = "not available"
    capability_reference: str = "not available"
    consumer_ready: bool = False
    timeline_continuity_consistent: bool = False
    readiness_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    health_status: Literal["healthy", "partial", "unavailable", "unknown"] = "unknown"
    missing_governance_timeline_references: list[str] = Field(default_factory=list)
    consistency_warnings: list[str] = Field(default_factory=list)
    summary: str = (
        "AI research context consumer governance timeline validation is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceTimelineValidationContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceTimelineValidationContractMeta
    )


def build_ai_research_context_consumer_governance_timeline_validation(
    *,
    available: bool,
    governance_timeline: AIResearchContextConsumerGovernanceTimeline | None,
    governance_summary: AIResearchContextConsumerGovernanceSummary | None,
    governance_status: AIResearchContextConsumerGovernanceStatus | None,
    governance_status_validation: AIResearchContextConsumerGovernanceStatusValidation | None,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    readiness_status: AIResearchContextConsumerReadinessStatus | None,
    health_indicator: AIResearchContextConsumerHealthIndicator | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_TIMELINE_VALIDATION_SURFACE,
) -> AIResearchContextConsumerGovernanceTimelineValidation:
    timeline_available = bool(governance_timeline is not None and governance_timeline.available)
    summary_available = bool(governance_summary is not None and governance_summary.available)
    status_available = bool(governance_status is not None and governance_status.available)
    status_validation_available = bool(
        governance_status_validation is not None and governance_status_validation.available
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
    summary_reference = (
        governance_summary.summary if summary_available else "not available"
    )
    status_reference = (
        governance_status.governance_reference if status_available else "not available"
    )
    status_validation_reference = (
        governance_status_validation.validation_reference
        if status_validation_available
        else "not available"
    )
    snapshot_validation_reference = (
        governance_snapshot_validation.validation_reference
        if snapshot_validation_available
        else "not available"
    )
    snapshot_reference = (
        governance_snapshot.governance_snapshot_reference if snapshot_available else "not available"
    )
    continuity_reference = (
        governance_snapshot.governance_continuity_reference if snapshot_available else "not available"
    )
    sequence_reference = (
        governance_timeline.governance_state_sequence_reference
        if timeline_available
        else "not available"
    )
    timeline_reference = (
        governance_timeline.governance_timeline_reference if timeline_available else "not available"
    )

    if not available:
        return AIResearchContextConsumerGovernanceTimelineValidation(
            governance_timeline_consistent=False,
            validation_state="unknown",
            governance_timeline_visible=False,
            validation_reference="not available",
            governance_timeline_reference=timeline_reference,
            governance_state_sequence_reference=sequence_reference,
            governance_continuity_reference=continuity_reference,
            governance_summary_reference=summary_reference,
            governance_status_reference=status_reference,
            governance_status_validation_reference=status_validation_reference,
            governance_snapshot_validation_reference=snapshot_validation_reference,
            governance_snapshot_reference=snapshot_reference,
            readiness_reference=readiness_reference,
            health_reference=health_reference,
            version_reference=version_reference,
            compatibility_reference=compatibility_reference,
            capability_reference=capability_reference,
            consumer_ready=consumer_ready,
            timeline_continuity_consistent=bool(
                governance_timeline.timeline_continuity_consistent
                if governance_timeline is not None
                else False
            ),
            readiness_status=readiness_state,
            health_status=health_state,
            summary=(
                "AI research context consumer governance timeline validation is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceTimelineValidationContractMeta(
                surface=surface
            ),
        )

    missing_governance_timeline_references: list[str] = []
    if not _reference_present(timeline_reference):
        missing_governance_timeline_references.append("governance_timeline_reference")
    if not _reference_present(sequence_reference):
        missing_governance_timeline_references.append("governance_state_sequence_reference")
    if not _reference_present(continuity_reference):
        missing_governance_timeline_references.append("governance_continuity_reference")
    if not _reference_present(summary_reference):
        missing_governance_timeline_references.append("governance_summary_reference")
    if not _reference_present(status_reference):
        missing_governance_timeline_references.append("governance_status_reference")
    if not _reference_present(status_validation_reference):
        missing_governance_timeline_references.append("governance_status_validation_reference")
    if not _reference_present(snapshot_validation_reference):
        missing_governance_timeline_references.append("governance_snapshot_validation_reference")
    if not _reference_present(snapshot_reference):
        missing_governance_timeline_references.append("governance_snapshot_reference")
    if not _reference_present(readiness_reference):
        missing_governance_timeline_references.append("readiness_reference")
    if not _reference_present(health_reference):
        missing_governance_timeline_references.append("health_reference")
    if not _reference_present(version_reference):
        missing_governance_timeline_references.append("version_reference")
    if not _reference_present(compatibility_reference):
        missing_governance_timeline_references.append("compatibility_reference")
    if not _reference_present(capability_reference):
        missing_governance_timeline_references.append("capability_reference")
    if governance_timeline is None or not governance_timeline.available:
        missing_governance_timeline_references.append("governance_timeline")

    expected_timeline_continuity_consistent = bool(
        status_validation_available
        and snapshot_validation_available
        and governance_status_validation.governance_status_consistent
        and governance_snapshot_validation.governance_snapshot_consistent
    )
    expected_timeline_state = _expected_timeline_state(
        governance_summary_available=summary_available,
        governance_status_available=status_available,
        governance_status_validation_available=status_validation_available,
        governance_snapshot_available=snapshot_available,
        governance_snapshot_validation_available=snapshot_validation_available,
        timeline_continuity_consistent=expected_timeline_continuity_consistent,
    )
    expected_timeline_visible = expected_timeline_state in {"complete", "partial"}
    expected_continuity_visible = bool(snapshot_available or snapshot_validation_available)
    expected_state_sequence_reference = _state_sequence_reference(
        governance_summary_reference=summary_reference,
        governance_status_reference=status_reference,
        governance_status_validation_reference=status_validation_reference,
        governance_snapshot_validation_reference=snapshot_validation_reference,
        governance_snapshot_reference=snapshot_reference,
    )
    expected_timeline_reference = _timeline_reference(
        governance_timeline_state=expected_timeline_state,
        governance_timeline_visible=expected_timeline_visible,
        governance_continuity_visible=expected_continuity_visible,
        governance_state_sequence_reference=expected_state_sequence_reference,
        governance_continuity_reference=continuity_reference,
        governance_summary_reference=summary_reference,
        governance_status_reference=status_reference,
        governance_status_validation_reference=status_validation_reference,
        governance_snapshot_validation_reference=snapshot_validation_reference,
        governance_snapshot_reference=snapshot_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        consumer_ready=consumer_ready,
        timeline_continuity_consistent=expected_timeline_continuity_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
    )

    consistency_warnings: list[str] = []
    if timeline_available:
        if governance_timeline.governance_timeline_state != expected_timeline_state:
            consistency_warnings.append("Governance timeline state mismatch.")
        if governance_timeline.governance_timeline_visible != expected_timeline_visible:
            consistency_warnings.append("Governance timeline visibility mismatch.")
        if governance_timeline.governance_continuity_visible != expected_continuity_visible:
            consistency_warnings.append("Governance continuity visibility mismatch.")
        if governance_timeline.governance_timeline_reference != expected_timeline_reference:
            consistency_warnings.append("Governance timeline reference mismatch.")
        if governance_timeline.governance_state_sequence_reference != expected_state_sequence_reference:
            consistency_warnings.append("Governance state sequence reference mismatch.")
        if governance_timeline.governance_continuity_reference != continuity_reference:
            consistency_warnings.append("Governance continuity reference mismatch.")
        if governance_timeline.governance_summary_reference != summary_reference:
            consistency_warnings.append("Governance summary reference mismatch.")
        if governance_timeline.governance_status_reference != status_reference:
            consistency_warnings.append("Governance status reference mismatch.")
        if (
            governance_timeline.governance_status_validation_reference
            != status_validation_reference
        ):
            consistency_warnings.append("Governance status validation reference mismatch.")
        if (
            governance_timeline.governance_snapshot_validation_reference
            != snapshot_validation_reference
        ):
            consistency_warnings.append("Governance snapshot validation reference mismatch.")
        if governance_timeline.governance_snapshot_reference != snapshot_reference:
            consistency_warnings.append("Governance snapshot reference mismatch.")
        if governance_timeline.readiness_reference != readiness_reference:
            consistency_warnings.append("Readiness reference mismatch.")
        if governance_timeline.health_reference != health_reference:
            consistency_warnings.append("Health reference mismatch.")
        if governance_timeline.version_reference != version_reference:
            consistency_warnings.append("Version reference mismatch.")
        if governance_timeline.compatibility_reference != compatibility_reference:
            consistency_warnings.append("Compatibility reference mismatch.")
        if governance_timeline.capability_reference != capability_reference:
            consistency_warnings.append("Capability reference mismatch.")
        if governance_timeline.consumer_ready != consumer_ready:
            consistency_warnings.append("Consumer ready mismatch.")
        if (
            governance_timeline.timeline_continuity_consistent
            != expected_timeline_continuity_consistent
        ):
            consistency_warnings.append("Timeline continuity consistency mismatch.")
        if governance_timeline.readiness_status != readiness_state:
            consistency_warnings.append("Readiness state mismatch.")
        if governance_timeline.health_status != health_state:
            consistency_warnings.append("Health state mismatch.")
    # Summary is derived from the same governance references and warnings below;
    # we do not add an additional summary mismatch warning here to keep the
    # validation layer minimal and stable.

    governance_timeline_consistent = (
        timeline_available
        and not missing_governance_timeline_references
        and not consistency_warnings
    )

    if governance_timeline_consistent:
        validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "consistent"
    elif consistency_warnings:
        validation_state = "inconsistent"
    elif missing_governance_timeline_references:
        validation_state = "partial"
    else:
        validation_state = "unknown"

    governance_timeline_visible = validation_state in {"consistent", "partial"}
    validation_reference = _validation_reference(
        validation_state=validation_state,
        governance_timeline_reference=timeline_reference,
        governance_state_sequence_reference=sequence_reference,
        governance_continuity_reference=continuity_reference,
        governance_summary_reference=summary_reference,
        governance_status_reference=status_reference,
        governance_status_validation_reference=status_validation_reference,
        governance_snapshot_validation_reference=snapshot_validation_reference,
        governance_snapshot_reference=snapshot_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
    )
    summary = _summary_text(
        governance_timeline_state=validation_state,
        governance_timeline_visible=governance_timeline_visible,
        governance_continuity_visible=bool(snapshot_available or snapshot_validation_available),
        governance_timeline_consistent=governance_timeline_consistent,
        validation_reference=validation_reference,
        governance_timeline_reference=timeline_reference,
        governance_state_sequence_reference=sequence_reference,
        governance_continuity_reference=continuity_reference,
        governance_summary_reference=summary_reference,
        governance_status_reference=status_reference,
        governance_status_validation_reference=status_validation_reference,
        governance_snapshot_validation_reference=snapshot_validation_reference,
        governance_snapshot_reference=snapshot_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        consumer_ready=consumer_ready,
        timeline_continuity_consistent=expected_timeline_continuity_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
        missing_governance_timeline_references=missing_governance_timeline_references,
        consistency_warnings=consistency_warnings,
    )
    return AIResearchContextConsumerGovernanceTimelineValidation(
        available=True,
        governance_timeline_consistent=governance_timeline_consistent,
        validation_state=validation_state,
        governance_timeline_visible=governance_timeline_visible,
        validation_reference=validation_reference,
        governance_timeline_reference=timeline_reference,
        governance_state_sequence_reference=sequence_reference,
        governance_continuity_reference=continuity_reference,
        governance_summary_reference=summary_reference,
        governance_status_reference=status_reference,
        governance_status_validation_reference=status_validation_reference,
        governance_snapshot_validation_reference=snapshot_validation_reference,
        governance_snapshot_reference=snapshot_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        consumer_ready=consumer_ready,
        timeline_continuity_consistent=expected_timeline_continuity_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
        missing_governance_timeline_references=missing_governance_timeline_references,
        consistency_warnings=consistency_warnings,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceTimelineValidationContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_timeline_validation_markdown(
    governance_timeline_validation: AIResearchContextConsumerGovernanceTimelineValidation | None,
) -> str:
    if governance_timeline_validation is None or not governance_timeline_validation.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Timeline Validation",
                "",
                "AI research context consumer governance timeline validation is unavailable.",
            ]
        )

    rows = [
        ("Validation state", governance_timeline_validation.validation_state),
        (
            "Governance timeline visible",
            "Yes" if governance_timeline_validation.governance_timeline_visible else "No",
        ),
        (
            "Governance timeline consistent",
            "Yes" if governance_timeline_validation.governance_timeline_consistent else "No",
        ),
        ("Validation reference", governance_timeline_validation.validation_reference),
        (
            "Governance timeline reference",
            governance_timeline_validation.governance_timeline_reference,
        ),
        (
            "Governance state sequence reference",
            governance_timeline_validation.governance_state_sequence_reference,
        ),
        (
            "Governance continuity reference",
            governance_timeline_validation.governance_continuity_reference,
        ),
        (
            "Governance summary reference",
            governance_timeline_validation.governance_summary_reference,
        ),
        (
            "Governance status reference",
            governance_timeline_validation.governance_status_reference,
        ),
        (
            "Governance status validation reference",
            governance_timeline_validation.governance_status_validation_reference,
        ),
        (
            "Governance snapshot validation reference",
            governance_timeline_validation.governance_snapshot_validation_reference,
        ),
        (
            "Governance snapshot reference",
            governance_timeline_validation.governance_snapshot_reference,
        ),
        ("Readiness reference", governance_timeline_validation.readiness_reference),
        ("Health reference", governance_timeline_validation.health_reference),
        ("Version reference", governance_timeline_validation.version_reference),
        ("Compatibility reference", governance_timeline_validation.compatibility_reference),
        ("Capability reference", governance_timeline_validation.capability_reference),
        (
            "Timeline continuity consistent",
            "Yes" if governance_timeline_validation.timeline_continuity_consistent else "No",
        ),
        ("Readiness status", governance_timeline_validation.readiness_status),
        ("Health status", governance_timeline_validation.health_status),
        (
            "Missing governance timeline references",
            _join_list(governance_timeline_validation.missing_governance_timeline_references),
        ),
        (
            "Consistency warnings",
            _join_list(governance_timeline_validation.consistency_warnings),
        ),
        (
            "Governance timeline validation contract",
            f"{governance_timeline_validation.contract_meta.version} / {governance_timeline_validation.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Timeline Validation",
        "",
        f"*{governance_timeline_validation.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _expected_timeline_state(
    *,
    governance_summary_available: bool,
    governance_status_available: bool,
    governance_status_validation_available: bool,
    governance_snapshot_available: bool,
    governance_snapshot_validation_available: bool,
    timeline_continuity_consistent: bool,
) -> Literal["complete", "partial", "unavailable", "unknown"]:
    if not any(
        [
            governance_summary_available,
            governance_status_available,
            governance_status_validation_available,
            governance_snapshot_available,
            governance_snapshot_validation_available,
        ]
    ):
        return "unknown"
    if (
        governance_summary_available
        and governance_status_available
        and governance_status_validation_available
        and governance_snapshot_available
        and governance_snapshot_validation_available
        and timeline_continuity_consistent
    ):
        return "complete"
    return "partial"


def _state_sequence_reference(
    *,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    governance_snapshot_validation_reference: str,
    governance_snapshot_reference: str,
) -> str:
    return (
        "governance_summary="
        f"{governance_summary_reference}; "
        "governance_status="
        f"{governance_status_reference}; "
        "governance_status_validation="
        f"{governance_status_validation_reference}; "
        "governance_snapshot_validation="
        f"{governance_snapshot_validation_reference}; "
        "governance_snapshot="
        f"{governance_snapshot_reference}"
    )


def _timeline_reference(
    *,
    governance_timeline_state: str,
    governance_timeline_visible: bool,
    governance_continuity_visible: bool,
    governance_state_sequence_reference: str,
    governance_continuity_reference: str,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    governance_snapshot_validation_reference: str,
    governance_snapshot_reference: str,
    readiness_reference: str,
    health_reference: str,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    consumer_ready: bool,
    timeline_continuity_consistent: bool,
    readiness_status: str,
    health_status: str,
) -> str:
    return (
        "AI research context consumer governance timeline: "
        f"state={governance_timeline_state}; "
        f"visible={'yes' if governance_timeline_visible else 'no'}; "
        f"continuity_visible={'yes' if governance_continuity_visible else 'no'}; "
        f"sequence={governance_state_sequence_reference}; "
        f"continuity={governance_continuity_reference}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"governance_snapshot_validation={governance_snapshot_validation_reference}; "
        f"governance_snapshot={governance_snapshot_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"version={version_reference}; "
        f"compatibility={compatibility_reference}; "
        f"capability={capability_reference}; "
        f"ready={'yes' if consumer_ready else 'no'}; "
        f"continuity_consistent={'yes' if timeline_continuity_consistent else 'no'}; "
        f"readiness_status={readiness_status}; "
        f"health_status={health_status}"
    )


def _validation_reference(
    *,
    validation_state: str,
    governance_timeline_reference: str,
    governance_state_sequence_reference: str,
    governance_continuity_reference: str,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    governance_snapshot_validation_reference: str,
    governance_snapshot_reference: str,
    readiness_reference: str,
    health_reference: str,
) -> str:
    return (
        "AI research context consumer governance timeline validation: "
        f"state={validation_state}; "
        f"timeline={governance_timeline_reference}; "
        f"sequence={governance_state_sequence_reference}; "
        f"continuity={governance_continuity_reference}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"governance_snapshot_validation={governance_snapshot_validation_reference}; "
        f"governance_snapshot={governance_snapshot_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}"
    )


def _summary_text(
    *,
    governance_timeline_state: str,
    governance_timeline_visible: bool,
    governance_continuity_visible: bool,
    governance_timeline_consistent: bool,
    validation_reference: str,
    governance_timeline_reference: str,
    governance_state_sequence_reference: str,
    governance_continuity_reference: str,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    governance_snapshot_validation_reference: str,
    governance_snapshot_reference: str,
    readiness_reference: str,
    health_reference: str,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    consumer_ready: bool,
    timeline_continuity_consistent: bool,
    readiness_status: str,
    health_status: str,
    missing_governance_timeline_references: list[str],
    consistency_warnings: list[str],
) -> str:
    return (
        "AI research context consumer governance timeline validation: "
        f"state={governance_timeline_state}; "
        f"visible={'yes' if governance_timeline_visible else 'no'}; "
        f"continuity_visible={'yes' if governance_continuity_visible else 'no'}; "
        f"consistent={'yes' if governance_timeline_consistent else 'no'}; "
        f"validation={validation_reference}; "
        f"timeline={governance_timeline_reference}; "
        f"sequence={governance_state_sequence_reference}; "
        f"continuity={governance_continuity_reference}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"governance_snapshot_validation={governance_snapshot_validation_reference}; "
        f"governance_snapshot={governance_snapshot_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"version={version_reference}; "
        f"compatibility={compatibility_reference}; "
        f"capability={capability_reference}; "
        f"ready={'yes' if consumer_ready else 'no'}; "
        f"continuity_consistent={'yes' if timeline_continuity_consistent else 'no'}; "
        f"readiness_status={readiness_status}; "
        f"health_status={health_status}; "
        f"missing={_join_list(missing_governance_timeline_references)}; "
        f"warnings={_join_list(consistency_warnings)}"
    )


def _reference_present(value: object | None) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text not in {"not available", "unavailable", "unknown"}


def _join_list(values: list[str]) -> str:
    if not values:
        return "none"
    return " | ".join(str(value) for value in values if str(value).strip()) or "none"

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_consumer_governance_snapshot import (
    AIResearchContextConsumerGovernanceSnapshot,
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
from ccass_core.ai_research_context_consumer_health import (
    AIResearchContextConsumerHealthIndicator,
)
from ccass_core.ai_research_context_consumer_readiness import (
    AIResearchContextConsumerReadinessStatus,
)

AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SNAPSHOT_VALIDATION_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SNAPSHOT_VALIDATION_SURFACE = (
    "ai_research_context_consumer_governance_snapshot_validation"
)


class AIResearchContextConsumerGovernanceSnapshotValidationContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SNAPSHOT_VALIDATION_VERSION
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SNAPSHOT_VALIDATION_SURFACE


class AIResearchContextConsumerGovernanceSnapshotValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    governance_snapshot_consistent: bool = False
    validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "unknown"
    governance_snapshot_visible: bool = False
    validation_reference: str = "not available"
    governance_snapshot_reference: str = "not available"
    governance_continuity_reference: str = "not available"
    governance_snapshot_summary_reference: str = "not available"
    governance_summary_reference: str = "not available"
    governance_status_reference: str = "not available"
    governance_status_validation_reference: str = "not available"
    readiness_reference: str = "not available"
    health_reference: str = "not available"
    version_reference: str = "not available"
    compatibility_reference: str = "not available"
    capability_reference: str = "not available"
    consumer_ready: bool = False
    snapshot_continuity_consistent: bool = False
    readiness_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    health_status: Literal["healthy", "partial", "unavailable", "unknown"] = "unknown"
    missing_governance_snapshot_references: list[str] = Field(default_factory=list)
    consistency_warnings: list[str] = Field(default_factory=list)
    summary: str = (
        "AI research context consumer governance snapshot validation is unavailable."
    )
    contract_meta: AIResearchContextConsumerGovernanceSnapshotValidationContractMeta = Field(
        default_factory=AIResearchContextConsumerGovernanceSnapshotValidationContractMeta
    )


def build_ai_research_context_consumer_governance_snapshot_validation(
    *,
    available: bool,
    governance_snapshot: AIResearchContextConsumerGovernanceSnapshot | None,
    governance_summary: AIResearchContextConsumerGovernanceSummary | None,
    governance_status: AIResearchContextConsumerGovernanceStatus | None,
    governance_status_validation: AIResearchContextConsumerGovernanceStatusValidation | None,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
    readiness_status: AIResearchContextConsumerReadinessStatus | None,
    health_indicator: AIResearchContextConsumerHealthIndicator | None,
    surface: str = AI_RESEARCH_CONTEXT_CONSUMER_GOVERNANCE_SNAPSHOT_VALIDATION_SURFACE,
) -> AIResearchContextConsumerGovernanceSnapshotValidation:
    snapshot_available = bool(governance_snapshot is not None and governance_snapshot.available)
    governance_summary_reference = (
        governance_summary.summary
        if governance_summary is not None and governance_summary.available
        else "not available"
    )
    governance_status_reference = (
        governance_status.governance_reference
        if governance_status is not None and governance_status.available
        else "not available"
    )
    governance_status_validation_reference = (
        governance_status_validation.validation_reference
        if governance_status_validation is not None and governance_status_validation.available
        else "not available"
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
    governance_snapshot_summary_reference = (
        governance_snapshot.governance_snapshot_summary if snapshot_available else "not available"
    )

    if not available:
        return AIResearchContextConsumerGovernanceSnapshotValidation(
            governance_snapshot_consistent=False,
            validation_state="unknown",
            governance_snapshot_visible=False,
            validation_reference="not available",
            governance_snapshot_reference=(
                governance_snapshot.governance_snapshot_reference
                if governance_snapshot is not None
                else "not available"
            ),
            governance_continuity_reference=(
                governance_snapshot.governance_continuity_reference
                if governance_snapshot is not None
                else "not available"
            ),
            governance_snapshot_summary_reference=governance_snapshot_summary_reference,
            governance_summary_reference=governance_summary_reference,
            governance_status_reference=governance_status_reference,
            governance_status_validation_reference=governance_status_validation_reference,
            readiness_reference=readiness_reference,
            health_reference=health_reference,
            version_reference=version_reference,
            compatibility_reference=compatibility_reference,
            capability_reference=capability_reference,
            consumer_ready=consumer_ready,
            snapshot_continuity_consistent=bool(
                governance_snapshot.snapshot_continuity_consistent
                if governance_snapshot is not None
                else False
            ),
            readiness_status=readiness_state,
            health_status=health_state,
            summary=(
                "AI research context consumer governance snapshot validation is unavailable."
            ),
            contract_meta=AIResearchContextConsumerGovernanceSnapshotValidationContractMeta(
                surface=surface
            ),
        )

    missing_governance_snapshot_references: list[str] = []
    if not _reference_present(
        governance_snapshot.governance_snapshot_reference if snapshot_available else None
    ):
        missing_governance_snapshot_references.append("governance_snapshot_reference")
    if not _reference_present(
        governance_snapshot.governance_continuity_reference if snapshot_available else None
    ):
        missing_governance_snapshot_references.append("governance_continuity_reference")
    if not _reference_present(governance_snapshot_summary_reference):
        missing_governance_snapshot_references.append("governance_snapshot_summary_reference")
    if not _reference_present(governance_summary_reference):
        missing_governance_snapshot_references.append("governance_summary_reference")
    if not _reference_present(governance_status_reference):
        missing_governance_snapshot_references.append("governance_status_reference")
    if not _reference_present(governance_status_validation_reference):
        missing_governance_snapshot_references.append("governance_status_validation_reference")
    if not _reference_present(readiness_reference):
        missing_governance_snapshot_references.append("readiness_reference")
    if not _reference_present(health_reference):
        missing_governance_snapshot_references.append("health_reference")
    if not _reference_present(version_reference):
        missing_governance_snapshot_references.append("version_reference")
    if not _reference_present(compatibility_reference):
        missing_governance_snapshot_references.append("compatibility_reference")
    if not _reference_present(capability_reference):
        missing_governance_snapshot_references.append("capability_reference")
    if governance_snapshot is None or not governance_snapshot.available:
        missing_governance_snapshot_references.append("governance_snapshot")

    expected_snapshot_state = _expected_snapshot_state(
        governance_status=governance_status,
        governance_status_validation=governance_status_validation,
    )
    expected_snapshot_visible = expected_snapshot_state in {"complete", "partial"}
    expected_snapshot_continuity_consistent = expected_snapshot_state == "complete"
    expected_snapshot_reference = _snapshot_reference(
        governance_snapshot_state=expected_snapshot_state,
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
    )
    expected_continuity_reference = _continuity_reference(
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
    )
    expected_summary = _snapshot_summary_text(
        governance_snapshot_state=expected_snapshot_state,
        governance_snapshot_visible=expected_snapshot_visible,
        governance_snapshot_reference=expected_snapshot_reference,
        governance_continuity_reference=expected_continuity_reference,
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        consumer_ready=consumer_ready,
        snapshot_continuity_consistent=expected_snapshot_continuity_consistent,
        readiness_status=readiness_state,
        health_status=health_state,
    )

    consistency_warnings: list[str] = []
    if snapshot_available:
        if governance_snapshot.governance_snapshot_state != expected_snapshot_state:
            consistency_warnings.append("Governance snapshot state mismatch.")
        if governance_snapshot.governance_snapshot_visible != expected_snapshot_visible:
            consistency_warnings.append("Governance snapshot visibility mismatch.")
        if governance_snapshot.governance_snapshot_reference != expected_snapshot_reference:
            consistency_warnings.append("Governance snapshot reference mismatch.")
        if governance_snapshot.governance_continuity_reference != expected_continuity_reference:
            consistency_warnings.append("Governance continuity reference mismatch.")
        if governance_snapshot.governance_snapshot_summary != expected_summary:
            consistency_warnings.append("Governance snapshot summary mismatch.")
        if governance_snapshot.governance_summary_reference != governance_summary_reference:
            consistency_warnings.append("Governance snapshot summary reference mismatch.")
        if governance_snapshot.governance_status_reference != governance_status_reference:
            consistency_warnings.append("Governance snapshot status reference mismatch.")
        if (
            governance_snapshot.governance_status_validation_reference
            != governance_status_validation_reference
        ):
            consistency_warnings.append(
                "Governance snapshot status validation reference mismatch."
            )
        if governance_snapshot.readiness_reference != readiness_reference:
            consistency_warnings.append("Governance snapshot readiness reference mismatch.")
        if governance_snapshot.health_reference != health_reference:
            consistency_warnings.append("Governance snapshot health reference mismatch.")
        if governance_snapshot.version_reference != version_reference:
            consistency_warnings.append("Governance snapshot version reference mismatch.")
        if governance_snapshot.compatibility_reference != compatibility_reference:
            consistency_warnings.append("Governance snapshot compatibility reference mismatch.")
        if governance_snapshot.capability_reference != capability_reference:
            consistency_warnings.append("Governance snapshot capability reference mismatch.")
        if governance_snapshot.consumer_ready != consumer_ready:
            consistency_warnings.append("Governance snapshot consumer ready mismatch.")
        if governance_snapshot.snapshot_continuity_consistent != expected_snapshot_continuity_consistent:
            consistency_warnings.append(
                "Governance snapshot continuity consistency mismatch."
            )
        if governance_snapshot.readiness_status != readiness_state:
            consistency_warnings.append("Governance snapshot readiness state mismatch.")
        if governance_snapshot.health_status != health_state:
            consistency_warnings.append("Governance snapshot health state mismatch.")

    governance_snapshot_consistent = (
        snapshot_available
        and not missing_governance_snapshot_references
        and not consistency_warnings
    )

    if governance_snapshot_consistent:
        validation_state: Literal["consistent", "partial", "inconsistent", "unknown"] = "consistent"
    elif consistency_warnings:
        validation_state = "inconsistent"
    elif missing_governance_snapshot_references:
        validation_state = "partial"
    else:
        validation_state = "unknown"

    governance_snapshot_visible = validation_state in {"consistent", "partial"}
    validation_reference = _validation_reference(
        validation_state=validation_state,
        governance_snapshot_reference=(
            governance_snapshot.governance_snapshot_reference
            if governance_snapshot is not None
            else "not available"
        ),
        governance_continuity_reference=(
            governance_snapshot.governance_continuity_reference
            if governance_snapshot is not None
            else "not available"
        ),
        governance_snapshot_summary_reference=governance_snapshot_summary_reference,
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
    )
    summary = _summary_text(
        governance_snapshot_state=validation_state,
        governance_snapshot_visible=governance_snapshot_visible,
        governance_snapshot_consistent=governance_snapshot_consistent,
        validation_reference=validation_reference,
        governance_snapshot_reference=(
            governance_snapshot.governance_snapshot_reference
            if governance_snapshot is not None
            else "not available"
        ),
        governance_continuity_reference=(
            governance_snapshot.governance_continuity_reference
            if governance_snapshot is not None
            else "not available"
        ),
        governance_snapshot_summary_reference=governance_snapshot_summary_reference,
        missing_governance_snapshot_references=missing_governance_snapshot_references,
        consistency_warnings=consistency_warnings,
    )
    return AIResearchContextConsumerGovernanceSnapshotValidation(
        available=True,
        governance_snapshot_consistent=governance_snapshot_consistent,
        validation_state=validation_state,
        governance_snapshot_visible=governance_snapshot_visible,
        validation_reference=validation_reference,
        governance_snapshot_reference=(
            governance_snapshot.governance_snapshot_reference
            if governance_snapshot is not None
            else "not available"
        ),
        governance_continuity_reference=(
            governance_snapshot.governance_continuity_reference
            if governance_snapshot is not None
            else "not available"
        ),
        governance_snapshot_summary_reference=governance_snapshot_summary_reference,
        governance_summary_reference=governance_summary_reference,
        governance_status_reference=governance_status_reference,
        governance_status_validation_reference=governance_status_validation_reference,
        readiness_reference=readiness_reference,
        health_reference=health_reference,
        version_reference=version_reference,
        compatibility_reference=compatibility_reference,
        capability_reference=capability_reference,
        consumer_ready=consumer_ready,
        snapshot_continuity_consistent=bool(
            governance_snapshot.snapshot_continuity_consistent
            if governance_snapshot is not None
            else False
        ),
        readiness_status=readiness_state,
        health_status=health_state,
        missing_governance_snapshot_references=missing_governance_snapshot_references,
        consistency_warnings=consistency_warnings,
        summary=summary,
        contract_meta=AIResearchContextConsumerGovernanceSnapshotValidationContractMeta(
            surface=surface
        ),
    )


def build_ai_research_context_consumer_governance_snapshot_validation_markdown(
    governance_snapshot_validation: AIResearchContextConsumerGovernanceSnapshotValidation | None,
) -> str:
    if governance_snapshot_validation is None or not governance_snapshot_validation.available:
        return "\n".join(
            [
                "### AI Research Context Consumer Governance Snapshot Validation",
                "",
                "AI research context consumer governance snapshot validation is unavailable.",
            ]
        )

    rows = [
        ("Validation state", governance_snapshot_validation.validation_state),
        (
            "Governance snapshot visible",
            "Yes" if governance_snapshot_validation.governance_snapshot_visible else "No",
        ),
        (
            "Governance snapshot consistent",
            "Yes" if governance_snapshot_validation.governance_snapshot_consistent else "No",
        ),
        ("Validation reference", governance_snapshot_validation.validation_reference),
        ("Governance snapshot reference", governance_snapshot_validation.governance_snapshot_reference),
        (
            "Governance continuity reference",
            governance_snapshot_validation.governance_continuity_reference,
        ),
        (
            "Governance snapshot summary reference",
            governance_snapshot_validation.governance_snapshot_summary_reference,
        ),
        ("Governance summary reference", governance_snapshot_validation.governance_summary_reference),
        ("Governance status reference", governance_snapshot_validation.governance_status_reference),
        (
            "Governance status validation reference",
            governance_snapshot_validation.governance_status_validation_reference,
        ),
        ("Readiness reference", governance_snapshot_validation.readiness_reference),
        ("Health reference", governance_snapshot_validation.health_reference),
        ("Version reference", governance_snapshot_validation.version_reference),
        ("Compatibility reference", governance_snapshot_validation.compatibility_reference),
        ("Capability reference", governance_snapshot_validation.capability_reference),
        ("Consumer ready", "Yes" if governance_snapshot_validation.consumer_ready else "No"),
        (
            "Snapshot continuity consistent",
            "Yes" if governance_snapshot_validation.snapshot_continuity_consistent else "No",
        ),
        ("Readiness status", governance_snapshot_validation.readiness_status),
        ("Health status", governance_snapshot_validation.health_status),
        (
            "Missing governance snapshot references",
            _join_list(governance_snapshot_validation.missing_governance_snapshot_references),
        ),
        (
            "Consistency warnings",
            _join_list(governance_snapshot_validation.consistency_warnings),
        ),
        (
            "Governance snapshot validation contract",
            f"{governance_snapshot_validation.contract_meta.version} / "
            f"{governance_snapshot_validation.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Consumer Governance Snapshot Validation",
        "",
        f"*{governance_snapshot_validation.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def _expected_snapshot_state(
    *,
    governance_status: AIResearchContextConsumerGovernanceStatus | None,
    governance_status_validation: AIResearchContextConsumerGovernanceStatusValidation | None,
) -> Literal["complete", "partial", "unavailable", "unknown"]:
    if governance_status is None or not governance_status.available:
        return "unavailable"
    if governance_status_validation is not None and governance_status_validation.available:
        if governance_status_validation.validation_state == "consistent":
            return "complete"
        return "partial"
    if governance_status.governance_status == "complete":
        return "complete"
    if governance_status.governance_status == "partial":
        return "partial"
    return "unknown"


def _validation_reference(
    *,
    validation_state: str,
    governance_snapshot_reference: str,
    governance_continuity_reference: str,
    governance_snapshot_summary_reference: str,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    readiness_reference: str,
    health_reference: str,
) -> str:
    return (
        "AI research context consumer governance snapshot validation: "
        f"state={validation_state}; "
        f"snapshot={governance_snapshot_reference}; "
        f"continuity={governance_continuity_reference}; "
        f"snapshot_summary={governance_snapshot_summary_reference}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}"
    )


def _snapshot_summary_text(
    *,
    governance_snapshot_state: str,
    governance_snapshot_visible: bool,
    governance_snapshot_reference: str,
    governance_continuity_reference: str,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    readiness_reference: str,
    health_reference: str,
    consumer_ready: bool,
    snapshot_continuity_consistent: bool,
    readiness_status: str,
    health_status: str,
) -> str:
    return (
        "AI research context consumer governance snapshot: "
        f"state={governance_snapshot_state}; "
        f"visible={'yes' if governance_snapshot_visible else 'no'}; "
        f"snapshot={governance_snapshot_reference}; "
        f"continuity={governance_continuity_reference}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"ready={'yes' if consumer_ready else 'no'}; "
        f"continuity_consistent={'yes' if snapshot_continuity_consistent else 'no'}; "
        f"readiness_status={readiness_status}; "
        f"health_status={health_status}"
    )


def _summary_text(
    *,
    governance_snapshot_state: str,
    governance_snapshot_visible: bool,
    governance_snapshot_consistent: bool,
    validation_reference: str,
    governance_snapshot_reference: str,
    governance_continuity_reference: str,
    governance_snapshot_summary_reference: str,
    missing_governance_snapshot_references: list[str],
    consistency_warnings: list[str],
) -> str:
    return (
        "AI research context consumer governance snapshot validation: "
        f"state={governance_snapshot_state}; "
        f"visible={'yes' if governance_snapshot_visible else 'no'}; "
        f"consistent={'yes' if governance_snapshot_consistent else 'no'}; "
        f"validation={validation_reference}; "
        f"snapshot={governance_snapshot_reference}; "
        f"continuity={governance_continuity_reference}; "
        f"snapshot_summary={governance_snapshot_summary_reference}; "
        f"missing={_join_list(tuple(missing_governance_snapshot_references))}; "
        f"warnings={_join_list(tuple(consistency_warnings))}"
    )


def _snapshot_reference(
    *,
    governance_snapshot_state: str,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    readiness_reference: str,
    health_reference: str,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
) -> str:
    return (
        "AI research context consumer governance snapshot: "
        f"state={governance_snapshot_state}; "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"version={version_reference}; "
        f"compatibility={compatibility_reference}; "
        f"capability={capability_reference}"
    )


def _continuity_reference(
    *,
    governance_summary_reference: str,
    governance_status_reference: str,
    governance_status_validation_reference: str,
    readiness_reference: str,
    health_reference: str,
    version_reference: str,
    compatibility_reference: str,
    capability_reference: str,
) -> str:
    return (
        "AI research context consumer governance continuity: "
        f"governance_summary={governance_summary_reference}; "
        f"governance_status={governance_status_reference}; "
        f"governance_status_validation={governance_status_validation_reference}; "
        f"readiness={readiness_reference}; "
        f"health={health_reference}; "
        f"version={version_reference}; "
        f"compatibility={compatibility_reference}; "
        f"capability={capability_reference}"
    )


def _reference_present(value: object | None) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text not in {"not available", "unavailable", "unknown"}


def _join_list(values: tuple[str, ...] | list[str]) -> str:
    if not values:
        return "none"
    return " | ".join(str(value) for value in values if str(value).strip()) or "none"

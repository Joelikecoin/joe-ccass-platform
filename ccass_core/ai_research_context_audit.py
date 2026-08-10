from __future__ import annotations

from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field

AI_RESEARCH_CONTEXT_AUDIT_TRAIL_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_AUDIT_TRAIL_SURFACE = "ai_research_context_audit_trail"


class AIResearchContextAuditTrailContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_AUDIT_TRAIL_VERSION
    surface: str = AI_RESEARCH_CONTEXT_AUDIT_TRAIL_SURFACE


class AIResearchContextAuditTrail(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    creation_reference: str = "not available"
    provenance_reference: str = "not available"
    governance_reference: str = "unavailable"
    validation_reference: str = "unavailable"
    quality_summary_reference: str = "unavailable"
    warnings_reference: str = "0 warning(s)"
    warnings: list[str] = Field(default_factory=list)
    summary: str = "AI research context audit trail is unavailable."
    contract_meta: AIResearchContextAuditTrailContractMeta = Field(
        default_factory=AIResearchContextAuditTrailContractMeta
    )


def build_ai_research_context_audit_trail(
    *,
    available: bool,
    creation_reference: str,
    provenance_reference: str,
    governance_reference: str,
    validation_reference: str,
    quality_summary_reference: str,
    warnings_reference: str,
    warnings: Sequence[str] = (),
    surface: str = AI_RESEARCH_CONTEXT_AUDIT_TRAIL_SURFACE,
) -> AIResearchContextAuditTrail:
    warning_list = list(dict.fromkeys(warnings))
    summary = _summary_text(
        creation_reference=creation_reference,
        provenance_reference=provenance_reference,
        governance_reference=governance_reference,
        validation_reference=validation_reference,
        quality_summary_reference=quality_summary_reference,
        warnings_reference=warnings_reference,
    )
    return AIResearchContextAuditTrail(
        available=available,
        creation_reference=creation_reference,
        provenance_reference=provenance_reference,
        governance_reference=governance_reference,
        validation_reference=validation_reference,
        quality_summary_reference=quality_summary_reference,
        warnings_reference=warnings_reference,
        warnings=warning_list,
        summary=summary,
        contract_meta=AIResearchContextAuditTrailContractMeta(surface=surface),
    )


def build_ai_research_context_audit_trail_markdown(
    audit_trail: AIResearchContextAuditTrail | None,
) -> str:
    if audit_trail is None or not audit_trail.available:
        return "\n".join(
            [
                "### AI Research Context Audit Trail",
                "",
                "AI research context audit trail is unavailable.",
            ]
        )

    rows = [
        ("Creation reference", audit_trail.creation_reference),
        ("Provenance reference", audit_trail.provenance_reference),
        ("Governance reference", audit_trail.governance_reference),
        ("Validation reference", audit_trail.validation_reference),
        ("Quality summary reference", audit_trail.quality_summary_reference),
        ("Warnings reference", audit_trail.warnings_reference),
        ("Audit trail contract", f"{audit_trail.contract_meta.version} / {audit_trail.contract_meta.surface}"),
    ]
    lines = [
        "### AI Research Context Audit Trail",
        "",
        f"*{audit_trail.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    if audit_trail.warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {warning}" for warning in audit_trail.warnings)
    return "\n".join(lines)


def _summary_text(
    *,
    creation_reference: str,
    provenance_reference: str,
    governance_reference: str,
    validation_reference: str,
    quality_summary_reference: str,
    warnings_reference: str,
) -> str:
    return (
        "AI research context audit trail: "
        f"creation={creation_reference}; "
        f"provenance={provenance_reference}; "
        f"governance={governance_reference}; "
        f"validation={validation_reference}; "
        f"quality={quality_summary_reference}; "
        f"warnings={warnings_reference}"
    )

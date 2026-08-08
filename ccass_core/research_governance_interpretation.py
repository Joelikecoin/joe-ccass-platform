from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.research_governance_bridge import ResearchGovernanceContext


class ResearchGovernanceInterpretation(BaseModel):
    model_config = ConfigDict(frozen=True)

    data_availability_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    freshness_state: Literal[
        "fresh",
        "cached",
        "stale",
        "partial",
        "unavailable",
        "unknown",
    ] = "unknown"
    provenance_summary: str = "unavailable"
    warning_summary: str = "0 warning(s)"
    limitation_summary: str = "Governance interpretation is unavailable."
    source_trace_reference: str = "not available"
    summary: str = "Governance interpretation is unavailable."
    warnings: list[str] = Field(default_factory=list)


def build_research_governance_interpretation(
    consumer_view: Any,
    governance_context: ResearchGovernanceContext | None = None,
) -> ResearchGovernanceInterpretation:
    if consumer_view is None or not getattr(consumer_view, "available", False):
        return ResearchGovernanceInterpretation(
            data_availability_state="unavailable",
            freshness_state="unavailable",
            limitation_summary="Research context is unavailable.",
            summary="Research context is unavailable.",
        )

    quality_context = getattr(consumer_view, "quality_context", None)
    freshness_state = getattr(quality_context, "freshness_status", "unknown") or "unknown"
    provenance_summary = _provenance_summary(
        governance_context,
        getattr(quality_context, "provenance", None),
    )
    warnings = list(getattr(consumer_view, "warnings", []) or [])
    warning_summary = (
        governance_context.warnings_summary
        if governance_context is not None
        else f"{len(warnings)} warning(s)"
    )
    data_availability_state = _data_availability_state(freshness_state, warnings)
    limitation_summary = _limitation_summary(
        data_availability_state=data_availability_state,
        freshness_state=freshness_state,
        warnings=warnings,
    )
    source_trace_reference = (
        governance_context.source_trace_reference
        if governance_context is not None
        else "not available"
    )
    summary = _summary_text(
        data_availability_state=data_availability_state,
        freshness_state=freshness_state,
        provenance_summary=provenance_summary,
        warning_summary=warning_summary,
        limitation_summary=limitation_summary,
    )
    return ResearchGovernanceInterpretation(
        data_availability_state=data_availability_state,
        freshness_state=freshness_state,
        provenance_summary=provenance_summary,
        warning_summary=warning_summary,
        limitation_summary=limitation_summary,
        source_trace_reference=source_trace_reference,
        summary=summary,
        warnings=warnings,
    )


def _provenance_summary(
    governance_context: ResearchGovernanceContext | None,
    provenance: Any,
) -> str:
    if governance_context is not None and governance_context.provenance_summary:
        return governance_context.provenance_summary
    if provenance is None:
        return "unavailable"
    return f"{provenance.source} / {provenance.source_type} / {provenance.primary_or_fallback}"


def _data_availability_state(freshness_state: str, warnings: list[str]) -> str:
    if freshness_state == "unavailable":
        return "unavailable"
    if freshness_state == "partial":
        return "partial"
    if any("PARTIAL" in warning.upper() for warning in warnings):
        return "partial"
    return "available"


def _limitation_summary(
    *,
    data_availability_state: str,
    freshness_state: str,
    warnings: list[str],
) -> str:
    if data_availability_state == "unavailable":
        return "Research context is unavailable."
    if freshness_state == "partial":
        return "Freshness is partial; review original warnings."
    if freshness_state == "stale":
        return "Freshness is stale; review original warnings."
    if warnings:
        return "Warnings are present; review original warning messages."
    return "No additional limitations reported."


def _summary_text(
    *,
    data_availability_state: str,
    freshness_state: str,
    provenance_summary: str,
    warning_summary: str,
    limitation_summary: str,
) -> str:
    return (
        "Governance interpretation: "
        f"availability={data_availability_state}; "
        f"freshness={freshness_state}; "
        f"provenance={provenance_summary}; "
        f"warnings={warning_summary}; "
        f"limitations={limitation_summary}"
    )

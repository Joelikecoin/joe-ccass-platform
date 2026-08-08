from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_read_model import AIReadModelV0_1
from ccass_core.source_trace import SourceTraceView


class AIReadModelGovernanceContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str = "unavailable"
    source_type: str = "unavailable"
    primary_or_fallback: Literal["primary", "fallback", "unknown"] = "unknown"
    freshness_status: Literal["fresh", "cached", "stale", "partial", "unavailable", "unknown"] = (
        "unknown"
    )
    availability_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    warnings: list[str] = Field(default_factory=list)
    warning_summary: str = "0 warning(s)"
    limitation_summary: str = "Governance context is unavailable."
    source_trace_reference: str = "not available"
    summary: str = "Governance context is unavailable."


class AIReadModelGovernanceInterpretation(BaseModel):
    model_config = ConfigDict(frozen=True)

    data_availability_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    freshness_state: Literal["fresh", "cached", "stale", "partial", "unavailable", "unknown"] = (
        "unknown"
    )
    provenance_summary: str = "unavailable"
    warning_summary: str = "0 warning(s)"
    limitation_summary: str = "Governance interpretation is unavailable."
    source_trace_reference: str = "not available"
    summary: str = "Governance interpretation is unavailable."
    warnings: list[str] = Field(default_factory=list)


class AIReadModelConsumerView(BaseModel):
    available: bool = False
    read_model: AIReadModelV0_1 | None = None
    governance_context: AIReadModelGovernanceContext | None = None
    governance_interpretation: AIReadModelGovernanceInterpretation | None = None
    warnings: list[str] = Field(default_factory=list)
    summary: str | None = None


def build_ai_read_model_governance_context(
    read_model: AIReadModelV0_1 | None,
    *,
    source_trace: SourceTraceView | None = None,
) -> AIReadModelGovernanceContext:
    if read_model is None:
        return AIReadModelGovernanceContext()

    provenance = read_model.provenance
    quality = read_model.quality
    warnings = list(dict.fromkeys(quality.warnings))
    source_trace_reference = _source_trace_reference(source_trace)
    availability_state = _availability_state(quality.freshness_status, warnings)
    warning_summary = f"{len(warnings)} warning(s)"
    limitation_summary = _limitation_summary(
        availability_state=availability_state,
        freshness_status=quality.freshness_status,
        warnings=warnings,
    )
    summary = _summary_text(
        source=provenance.source,
        source_type=provenance.source_type,
        primary_or_fallback=provenance.primary_or_fallback,
        freshness_status=quality.freshness_status,
        availability_state=availability_state,
        warning_summary=warning_summary,
        limitation_summary=limitation_summary,
    )
    return AIReadModelGovernanceContext(
        source=provenance.source,
        source_type=provenance.source_type,
        primary_or_fallback=provenance.primary_or_fallback,
        freshness_status=quality.freshness_status,
        availability_state=availability_state,
        warnings=warnings,
        warning_summary=warning_summary,
        limitation_summary=limitation_summary,
        source_trace_reference=source_trace_reference,
        summary=summary,
    )


def build_ai_read_model_governance_interpretation(
    governance_context: AIReadModelGovernanceContext | None,
) -> AIReadModelGovernanceInterpretation:
    if governance_context is None:
        return AIReadModelGovernanceInterpretation()

    return AIReadModelGovernanceInterpretation(
        data_availability_state=governance_context.availability_state,
        freshness_state=governance_context.freshness_status,
        provenance_summary=_provenance_summary(governance_context),
        warning_summary=governance_context.warning_summary,
        limitation_summary=governance_context.limitation_summary,
        source_trace_reference=governance_context.source_trace_reference,
        summary=_interpretation_summary(governance_context),
        warnings=list(governance_context.warnings),
    )


def build_ai_read_model_consumer_view(
    read_model: AIReadModelV0_1 | None,
    *,
    source_trace: SourceTraceView | None = None,
) -> AIReadModelConsumerView:
    if read_model is None:
        return AIReadModelConsumerView()

    governance_context = build_ai_read_model_governance_context(
        read_model,
        source_trace=source_trace,
    )
    governance_interpretation = build_ai_read_model_governance_interpretation(governance_context)
    warnings = list(dict.fromkeys(read_model.quality.warnings))
    return AIReadModelConsumerView(
        available=True,
        read_model=read_model,
        governance_context=governance_context,
        governance_interpretation=governance_interpretation,
        warnings=warnings,
        summary=governance_interpretation.summary,
    )


def _availability_state(freshness_status: str, warnings: list[str]) -> str:
    if freshness_status == "unavailable":
        return "unavailable"
    if freshness_status == "partial":
        return "partial"
    if any("UNAVAILABLE" in warning.upper() for warning in warnings):
        return "partial"
    if freshness_status in {"fresh", "cached", "stale"}:
        return "available"
    return "unknown"


def _limitation_summary(
    *,
    availability_state: str,
    freshness_status: str,
    warnings: list[str],
) -> str:
    if availability_state == "unavailable":
        return "AI Read Model is unavailable."
    if freshness_status == "partial":
        return "Freshness is partial; review original warnings."
    if freshness_status == "stale":
        return "Freshness is stale; review original warnings."
    if warnings:
        return "Warnings are present; review original warning messages."
    return "No additional limitations reported."


def _summary_text(
    *,
    source: str,
    source_type: str,
    primary_or_fallback: str,
    freshness_status: str,
    availability_state: str,
    warning_summary: str,
    limitation_summary: str,
) -> str:
    return (
        "Governance context: "
        f"provenance={source} / {source_type} / {primary_or_fallback}; "
        f"freshness={freshness_status}; "
        f"availability={availability_state}; "
        f"warnings={warning_summary}; "
        f"limitations={limitation_summary}"
    )


def _provenance_summary(context: AIReadModelGovernanceContext) -> str:
    return f"{context.source} / {context.source_type} / {context.primary_or_fallback}"


def _interpretation_summary(context: AIReadModelGovernanceContext) -> str:
    return (
        "Governance interpretation: "
        f"availability={context.availability_state}; "
        f"freshness={context.freshness_status}; "
        f"provenance={_provenance_summary(context)}; "
        f"warnings={context.warning_summary}; "
        f"limitations={context.limitation_summary}"
    )


def _source_trace_reference(source_trace: SourceTraceView | None) -> str:
    if source_trace is None:
        return "not available"
    selected_source = source_trace.selection.selected_source_id or source_trace.source_identity.source_id
    return f"{source_trace.request_id} / {source_trace.route} / {selected_source}"

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.research_context import ResearchContextPackage
from ccass_core.source_trace import SourceTraceView


class ResearchGovernanceContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_trace: SourceTraceView | None = None
    provenance_summary: str = "unavailable"
    freshness_summary: str = "unavailable"
    date_convention_status: str = "unavailable"
    warnings_summary: str = "0 warning(s)"
    source_trace_reference: str = "not available"
    summary: str = "Governance context is unavailable."
    warnings: list[str] = Field(default_factory=list)


def build_research_governance_context(
    package: ResearchContextPackage | None,
    source_trace: SourceTraceView | None = None,
) -> ResearchGovernanceContext:
    if package is None and source_trace is None:
        return ResearchGovernanceContext()

    quality_context = package.quality_context if package is not None else None
    provenance = quality_context.provenance if quality_context else None
    warnings = list(quality_context.warnings) if quality_context else []
    provenance_summary = _provenance_summary(provenance)
    freshness_summary = _freshness_summary(quality_context.freshness_status if quality_context else None, source_trace)
    date_convention_status = _date_convention_status(source_trace)
    source_trace_reference = _source_trace_reference(source_trace)
    warnings_summary = f"{len(warnings)} warning(s)"
    summary = _summary_text(
        provenance_summary=provenance_summary,
        freshness_summary=freshness_summary,
        date_convention_status=date_convention_status,
        warnings_summary=warnings_summary,
    )
    return ResearchGovernanceContext(
        source_trace=source_trace,
        provenance_summary=provenance_summary,
        freshness_summary=freshness_summary,
        date_convention_status=date_convention_status,
        warnings_summary=warnings_summary,
        source_trace_reference=source_trace_reference,
        summary=summary,
        warnings=warnings,
    )


def _provenance_summary(provenance) -> str:
    if provenance is None:
        return "unavailable"
    return f"{provenance.source} / {provenance.source_type} / {provenance.primary_or_fallback}"


def _freshness_summary(freshness_status: str | None, source_trace: SourceTraceView | None) -> str:
    if freshness_status is None:
        return "unavailable"
    if source_trace is None:
        return freshness_status
    return f"{freshness_status} / cache:{source_trace.cache_usage_state}"


def _date_convention_status(source_trace: SourceTraceView | None) -> str:
    if source_trace is None:
        return "unavailable"
    return (
        f"{source_trace.date_governance.source_date_type} / "
        f"{source_trace.date_governance.date_convention_reference}"
    )


def _source_trace_reference(source_trace: SourceTraceView | None) -> str:
    if source_trace is None:
        return "not available"
    selected_source = source_trace.selection.selected_source_id or source_trace.source_identity.source_id
    return f"{source_trace.request_id} / {source_trace.route} / {selected_source}"


def _summary_text(
    *,
    provenance_summary: str,
    freshness_summary: str,
    date_convention_status: str,
    warnings_summary: str,
) -> str:
    return (
        "Governance context: "
        f"provenance={provenance_summary}; "
        f"freshness={freshness_summary}; "
        f"date_convention={date_convention_status}; "
        f"warnings={warnings_summary}."
    )

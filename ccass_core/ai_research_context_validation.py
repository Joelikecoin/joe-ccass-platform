from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_assembly import AIResearchContextAssembly

AI_RESEARCH_CONTEXT_VALIDATION_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_VALIDATION_SURFACE = "ai_research_context_validation"


class AIResearchContextValidationContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_VALIDATION_VERSION
    surface: str = AI_RESEARCH_CONTEXT_VALIDATION_SURFACE


class AIResearchContextValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    consumer_ready: bool = False
    context_available: bool = False
    provenance_present: bool = False
    freshness_metadata_present: bool = False
    warnings_consistent: bool = False
    limitation_visible: bool = False
    warnings: list[str] = Field(default_factory=list)
    summary: str = "AI research context validation is unavailable."
    contract_meta: AIResearchContextValidationContractMeta = Field(
        default_factory=AIResearchContextValidationContractMeta
    )


def build_ai_research_context_validation(
    assembly: AIResearchContextAssembly | None,
) -> AIResearchContextValidationResult:
    if assembly is None:
        return AIResearchContextValidationResult(
            status="unavailable",
            warnings=["AI research context assembly is unavailable."],
            summary="AI research context validation is unavailable.",
        )

    context_available = _context_available(assembly)
    provenance_present = _provenance_present(assembly)
    freshness_metadata_present = _freshness_metadata_present(assembly)
    warnings_consistent = _warnings_consistent(assembly)
    limitation_visible = _limitation_visible(assembly)

    warnings = _validation_warnings(
        assembly=assembly,
        context_available=context_available,
        provenance_present=provenance_present,
        freshness_metadata_present=freshness_metadata_present,
        warnings_consistent=warnings_consistent,
        limitation_visible=limitation_visible,
    )
    consumer_ready = (
        context_available
        and provenance_present
        and freshness_metadata_present
        and warnings_consistent
        and limitation_visible
    )
    status = _status(
        assembly=assembly,
        consumer_ready=consumer_ready,
        warnings=warnings,
    )
    summary = _summary_text(
        status=status,
        context_available=context_available,
        provenance_present=provenance_present,
        freshness_metadata_present=freshness_metadata_present,
        warnings_consistent=warnings_consistent,
        limitation_visible=limitation_visible,
        warnings=warnings,
    )
    return AIResearchContextValidationResult(
        status=status,
        consumer_ready=consumer_ready,
        context_available=context_available,
        provenance_present=provenance_present,
        freshness_metadata_present=freshness_metadata_present,
        warnings_consistent=warnings_consistent,
        limitation_visible=limitation_visible,
        warnings=warnings,
        summary=summary,
    )


def _context_available(assembly: AIResearchContextAssembly) -> bool:
    return bool(
        assembly.available
        and assembly.research_context_available
        and assembly.ai_read_model_available
        and assembly.governance_available
    )


def _provenance_present(assembly: AIResearchContextAssembly) -> bool:
    return all(
        [
            _non_empty_reference(
                assembly.research_governance_context.source_trace_reference
                if assembly.research_governance_context is not None
                else None
            ),
            _non_empty_reference(
                assembly.ai_read_model_governance_context.source_trace_reference
                if assembly.ai_read_model_governance_context is not None
                else None
            ),
        ]
    )


def _freshness_metadata_present(assembly: AIResearchContextAssembly) -> bool:
    research_freshness = (
        assembly.research_governance_context.freshness_summary
        if assembly.research_governance_context is not None
        else None
    )
    ai_freshness = (
        assembly.ai_read_model_governance_context.freshness_status
        if assembly.ai_read_model_governance_context is not None
        else None
    )
    return all(
        [
            _non_empty_reference(research_freshness),
            _non_empty_reference(ai_freshness),
            research_freshness != "unavailable",
            ai_freshness != "unknown",
        ]
    )


def _warnings_consistent(assembly: AIResearchContextAssembly) -> bool:
    return assembly.warnings == _merged_warnings(assembly)


def _limitation_visible(assembly: AIResearchContextAssembly) -> bool:
    limitation_sources = [
        assembly.research_governance_interpretation.limitation_summary
        if assembly.research_governance_interpretation is not None
        else None,
        assembly.ai_read_model_governance_interpretation.limitation_summary
        if assembly.ai_read_model_governance_interpretation is not None
        else None,
        assembly.ai_read_model_consumer_guidance.limitation_summary
        if assembly.ai_read_model_consumer_guidance is not None
        else None,
    ]
    return any(_non_empty_reference(source) for source in limitation_sources)


def _validation_warnings(
    *,
    assembly: AIResearchContextAssembly,
    context_available: bool,
    provenance_present: bool,
    freshness_metadata_present: bool,
    warnings_consistent: bool,
    limitation_visible: bool,
) -> list[str]:
    warnings = list(assembly.warnings)
    if not context_available:
        warnings.append("AI research context is incomplete for consumer use.")
    if not provenance_present:
        warnings.append("AI research context provenance is missing or unavailable.")
    if not freshness_metadata_present:
        warnings.append("AI research context freshness metadata is missing or unavailable.")
    if not warnings_consistent:
        warnings.append("AI research context warnings are inconsistent across consumer surfaces.")
    if not limitation_visible:
        warnings.append("AI research context limitation summary is not visible to consumers.")
    return list(dict.fromkeys(warnings))


def _status(
    *,
    assembly: AIResearchContextAssembly,
    consumer_ready: bool,
    warnings: list[str],
) -> Literal["ready", "partial", "unavailable", "unknown"]:
    if not assembly.available:
        return "unavailable"
    if consumer_ready:
        return "ready" if not warnings else "partial"
    return "partial" if warnings else "unknown"


def _summary_text(
    *,
    status: str,
    context_available: bool,
    provenance_present: bool,
    freshness_metadata_present: bool,
    warnings_consistent: bool,
    limitation_visible: bool,
    warnings: list[str],
) -> str:
    return (
        "AI research context validation: "
        f"status={status}; "
        f"context={'available' if context_available else 'unavailable'}; "
        f"provenance={'present' if provenance_present else 'missing'}; "
        f"freshness={'present' if freshness_metadata_present else 'missing'}; "
        f"warnings={'consistent' if warnings_consistent else 'inconsistent'}; "
        f"limitations={'visible' if limitation_visible else 'hidden'}; "
        f"warnings_count={len(warnings)}"
    )


def _merged_warnings(assembly: AIResearchContextAssembly) -> list[str]:
    warning_sets = [
        assembly.research_context_consumer_view.warnings
        if assembly.research_context_consumer_view is not None
        else [],
        assembly.research_governance_context.warnings
        if assembly.research_governance_context is not None
        else [],
        assembly.ai_read_model_consumer_view.warnings
        if assembly.ai_read_model_consumer_view is not None
        else [],
        assembly.ai_read_model_governance_context.warnings
        if assembly.ai_read_model_governance_context is not None
        else [],
        assembly.ai_read_model_consumer_guidance.warnings
        if assembly.ai_read_model_consumer_guidance is not None
        else [],
    ]
    flattened = [warning for warning_group in warning_sets for warning in warning_group]
    return list(dict.fromkeys(flattened))


def _non_empty_reference(value: object | None) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text not in {"not available", "unavailable", "unknown"}

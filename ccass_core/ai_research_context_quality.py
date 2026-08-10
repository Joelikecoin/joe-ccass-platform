from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AI_RESEARCH_CONTEXT_QUALITY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_QUALITY_SURFACE = "ai_research_context_quality"


class AIResearchContextQualityContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_QUALITY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_QUALITY_SURFACE


class AIResearchContextQualitySummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    overall_context_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown"
    availability_summary: str = "Context availability is unavailable."
    freshness_summary: str = "Freshness summary is unavailable."
    provenance_summary: str = "Provenance summary is unavailable."
    validation_summary: str = "Validation summary is unavailable."
    warning_summary: str = "0 warning(s)"
    limitation_summary: str = "Limitation summary is unavailable."
    consumer_ready: bool = False
    warnings: list[str] = Field(default_factory=list)
    summary: str = "AI research context quality summary is unavailable."
    contract_meta: AIResearchContextQualityContractMeta = Field(
        default_factory=AIResearchContextQualityContractMeta
    )


def build_ai_research_context_quality_summary(
    *,
    validation_status: Literal["ready", "partial", "unavailable", "unknown"] = "unknown",
    consumer_ready: bool = False,
    context_available: bool = False,
    provenance_reference: str = "not available",
    freshness_reference: str = "unavailable",
    validation_summary: str = "Validation summary is unavailable.",
    warning_summary: str = "0 warning(s)",
    limitation_summary: str = "Limitation summary is unavailable.",
    warnings: list[str] | None = None,
    surface: str = AI_RESEARCH_CONTEXT_QUALITY_SURFACE,
) -> AIResearchContextQualitySummary:
    warnings = list(dict.fromkeys(warnings or []))
    availability_summary = (
        "Consumer context is available."
        if context_available
        else "Consumer context is unavailable."
    )
    summary = (
        "AI research context quality: "
        f"status={validation_status}; "
        f"availability={availability_summary}; "
        f"freshness={freshness_reference}; "
        f"provenance={provenance_reference}; "
        f"validation={validation_summary}; "
        f"warnings={warning_summary}; "
        f"limitations={limitation_summary}"
    )
    return AIResearchContextQualitySummary(
        overall_context_status=validation_status,
        availability_summary=availability_summary,
        freshness_summary=freshness_reference,
        provenance_summary=provenance_reference,
        validation_summary=validation_summary,
        warning_summary=warning_summary,
        limitation_summary=limitation_summary,
        consumer_ready=consumer_ready,
        warnings=warnings,
        summary=summary,
        contract_meta=AIResearchContextQualityContractMeta(surface=surface),
    )

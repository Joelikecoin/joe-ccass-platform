from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_research_context_assembly import (
    AIResearchContextAssembly,
    AIResearchContextAssemblyContractMeta,
    AIResearchInputBlock,
)
from ccass_core.ai_research_context_quality import (
    AIResearchContextQualitySummary,
    build_ai_research_context_quality_summary,
)
from ccass_core.ai_research_context_validation import (
    AIResearchContextValidationResult,
    build_ai_research_context_validation,
)


class AIResearchContextConsumerView(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    assembly: AIResearchContextAssembly | None = None
    context_available: bool = False
    availability_state: Literal["available", "partial", "unavailable", "unknown"] = "unknown"
    freshness_state: Literal[
        "fresh",
        "cached",
        "stale",
        "partial",
        "unavailable",
        "unknown",
    ] = "unknown"
    governance_summary: str = "AI research context assembly is unavailable."
    provenance_reference: str = "not available"
    freshness_reference: str = "unavailable"
    warning_summary: str = "0 warning(s)"
    limitation_summary: str = "Consumer guidance is unavailable."
    usage_steps: list[str] = Field(default_factory=list)
    input_blocks: list[AIResearchInputBlock] = Field(default_factory=list)
    validation: AIResearchContextValidationResult | None = None
    quality_summary: AIResearchContextQualitySummary | None = None
    warnings: list[str] = Field(default_factory=list)
    summary: str = "AI research context consumer view is unavailable."
    contract_meta: AIResearchContextAssemblyContractMeta | None = None


def build_ai_research_context_consumer_view(
    assembly: AIResearchContextAssembly | None,
) -> AIResearchContextConsumerView:
    if assembly is None:
        return AIResearchContextConsumerView(
            availability_state="unavailable",
            freshness_state="unavailable",
        )

    research_context_consumer_view = assembly.research_context_consumer_view
    research_governance_context = assembly.research_governance_context
    research_governance_interpretation = assembly.research_governance_interpretation
    ai_read_model_consumer_view = assembly.ai_read_model_consumer_view
    ai_read_model_governance_context = assembly.ai_read_model_governance_context
    ai_read_model_governance_interpretation = assembly.ai_read_model_governance_interpretation
    ai_read_model_consumer_guidance = assembly.ai_read_model_consumer_guidance

    context_available = assembly.available
    provenance_reference = _provenance_reference(
        research_governance_context=research_governance_context,
        ai_read_model_governance_context=ai_read_model_governance_context,
    )
    freshness_reference = _freshness_reference(
        research_governance_context=research_governance_context,
        ai_read_model_governance_context=ai_read_model_governance_context,
    )
    validation = build_ai_research_context_validation(assembly)
    availability_state = _availability_state(assembly=assembly, validation=validation)
    freshness_state = _freshness_state(assembly)
    warning_summary = f"{len(assembly.warnings)} warning(s)"
    limitation_summary = _limitation_summary(
        research_governance_interpretation=research_governance_interpretation,
        ai_read_model_governance_interpretation=ai_read_model_governance_interpretation,
        ai_read_model_consumer_guidance=ai_read_model_consumer_guidance,
    )
    quality_summary = build_ai_research_context_quality_summary(
        validation_status=validation.status,
        consumer_ready=validation.consumer_ready,
        context_available=context_available,
        provenance_reference=provenance_reference,
        freshness_reference=freshness_reference,
        validation_summary=validation.summary,
        warning_summary=warning_summary,
        limitation_summary=limitation_summary,
        warnings=validation.warnings,
    )
    usage_steps = [
        "Check context availability first.",
        "Read the governance summary before consuming the payload.",
        "Use provenance and freshness references as trust metadata, not conclusions.",
        "Review warnings and limitation summary before downstream use.",
        "Use the assembly and input blocks as the consumer input bundle.",
    ]
    summary = _summary_text(
        context_available=context_available,
        availability_state=availability_state,
        freshness_state=freshness_state,
        governance_summary=assembly.summary,
        provenance_reference=provenance_reference,
        freshness_reference=freshness_reference,
        warning_summary=warning_summary,
        limitation_summary=limitation_summary,
    )
    return AIResearchContextConsumerView(
        available=True,
        assembly=assembly,
        context_available=context_available,
        availability_state=availability_state,
        freshness_state=freshness_state,
        governance_summary=assembly.summary,
        provenance_reference=provenance_reference,
        freshness_reference=freshness_reference,
        warning_summary=warning_summary,
        limitation_summary=limitation_summary,
        usage_steps=usage_steps,
        input_blocks=list(assembly.input_blocks),
        validation=validation,
        quality_summary=quality_summary,
        warnings=list(assembly.warnings),
        summary=summary,
        contract_meta=assembly.contract_meta,
    )


def build_ai_research_context_usage_markdown(
    consumer_view: AIResearchContextConsumerView | None,
) -> str:
    if consumer_view is None or not consumer_view.available:
        return "\n".join(
            [
                "### AI Research Context Consumer",
                "",
                "AI research context consumer view is unavailable.",
            ]
        )

    rows = [
        ("Context availability", "available" if consumer_view.context_available else "unavailable"),
        ("Availability state", consumer_view.availability_state),
        ("Freshness state", consumer_view.freshness_state),
        ("Governance summary", consumer_view.governance_summary),
        ("Provenance reference", consumer_view.provenance_reference),
        ("Freshness reference", consumer_view.freshness_reference),
        ("Warning summary", consumer_view.warning_summary),
        ("Limitation summary", consumer_view.limitation_summary),
        (
            "Validation status",
            consumer_view.validation.status if consumer_view.validation is not None else "unknown",
        ),
        (
            "Consumer ready",
            "Yes" if consumer_view.validation and consumer_view.validation.consumer_ready else "No",
        ),
        (
            "Quality overall status",
            (
                consumer_view.quality_summary.overall_context_status
                if consumer_view.quality_summary is not None
                else "unknown"
            ),
        ),
        (
            "Quality availability summary",
            (
                consumer_view.quality_summary.availability_summary
                if consumer_view.quality_summary is not None
                else "Context availability is unavailable."
            ),
        ),
        (
            "Contract reference",
            (
                f"{consumer_view.contract_meta.version} / {consumer_view.contract_meta.surface}"
                if consumer_view.contract_meta is not None
                else "not available"
            ),
        ),
    ]
    lines = [
        "### AI Research Context Consumer",
        "",
        f"*{consumer_view.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    if consumer_view.usage_steps:
        lines.extend(["", "Usage steps:"])
        lines.extend(f"- {step}" for step in consumer_view.usage_steps)
    if consumer_view.validation is not None:
        lines.extend(["", "Validation warnings:"])
        if consumer_view.validation.warnings:
            lines.extend(f"- {warning}" for warning in consumer_view.validation.warnings)
        else:
            lines.append("- none")
    if consumer_view.quality_summary is not None:
        lines.extend(["", "Quality summary:"])
        lines.extend(f"- {label}: {value}" for label, value in [
            ("Overall status", consumer_view.quality_summary.overall_context_status),
            ("Availability", consumer_view.quality_summary.availability_summary),
            ("Freshness", consumer_view.quality_summary.freshness_summary),
            ("Provenance", consumer_view.quality_summary.provenance_summary),
            ("Validation", consumer_view.quality_summary.validation_summary),
            ("Warning", consumer_view.quality_summary.warning_summary),
            ("Limitation", consumer_view.quality_summary.limitation_summary),
        ])
    if consumer_view.warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {warning}" for warning in consumer_view.warnings)
    return "\n".join(lines)


def _provenance_reference(
    *,
    research_governance_context,
    ai_read_model_governance_context,
) -> str:
    references: list[str] = []
    if research_governance_context is not None:
        references.append(research_governance_context.source_trace_reference)
    if ai_read_model_governance_context is not None:
        references.append(ai_read_model_governance_context.source_trace_reference)
    references = [reference for reference in references if reference and reference != "not available"]
    if not references:
        return "not available"
    return " | ".join(dict.fromkeys(references))


def _freshness_reference(
    *,
    research_governance_context,
    ai_read_model_governance_context,
) -> str:
    references: list[str] = []
    if research_governance_context is not None:
        references.append(research_governance_context.freshness_summary)
    if ai_read_model_governance_context is not None:
        references.append(ai_read_model_governance_context.freshness_status)
    references = [reference for reference in references if reference and reference != "unavailable"]
    if not references:
        return "unavailable"
    return " | ".join(dict.fromkeys(references))


def _availability_state(
    *,
    assembly: AIResearchContextAssembly,
    validation: AIResearchContextValidationResult | None,
) -> Literal["available", "partial", "unavailable", "unknown"]:
    if not assembly.available:
        return "unavailable"
    if validation is None:
        return "unknown"
    if validation.status == "ready":
        return "available"
    if validation.status == "partial":
        return "partial"
    if validation.status == "unavailable":
        return "unavailable"
    return "unknown"


def _freshness_state(
    assembly: AIResearchContextAssembly,
) -> Literal["fresh", "cached", "stale", "partial", "unavailable", "unknown"]:
    states = [
        getattr(
            assembly.research_governance_interpretation,
            "freshness_state",
            None,
        ),
        getattr(
            assembly.ai_read_model_governance_interpretation,
            "freshness_state",
            None,
        ),
        getattr(
            assembly.ai_read_model_consumer_guidance,
            "freshness_state",
            None,
        ),
    ]
    normalized = [state for state in states if state]
    for candidate in ("stale", "partial", "cached", "fresh", "unavailable", "unknown"):
        if candidate in normalized:
            return candidate  # type: ignore[return-value]
    return "unknown"


def _limitation_summary(
    *,
    research_governance_interpretation,
    ai_read_model_governance_interpretation,
    ai_read_model_consumer_guidance,
) -> str:
    references: list[str] = []
    if research_governance_interpretation is not None:
        references.append(research_governance_interpretation.limitation_summary)
    if ai_read_model_governance_interpretation is not None:
        references.append(ai_read_model_governance_interpretation.limitation_summary)
    if ai_read_model_consumer_guidance is not None:
        references.append(ai_read_model_consumer_guidance.limitation_summary)
    references = [reference for reference in references if reference]
    if not references:
        return "Consumer guidance is unavailable."
    return " | ".join(dict.fromkeys(references))


def _summary_text(
    *,
    context_available: bool,
    availability_state: str,
    freshness_state: str,
    governance_summary: str,
    provenance_reference: str,
    freshness_reference: str,
    warning_summary: str,
    limitation_summary: str,
) -> str:
    context_state = "available" if context_available else "unavailable"
    return (
        "AI research context consumer view: "
        f"context={context_state}; "
        f"availability={availability_state}; "
        f"freshness_state={freshness_state}; "
        f"governance={governance_summary}; "
        f"provenance={provenance_reference}; "
        f"freshness_reference={freshness_reference}; "
        f"warnings={warning_summary}; "
        f"limitations={limitation_summary}"
    )

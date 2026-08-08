from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_read_model import AIReadModelIdentity
from ccass_core.ai_read_model_governance import (
    AIReadModelConsumerUsageGuidance,
    AIReadModelConsumerView,
    AIReadModelGovernanceContext,
    AIReadModelGovernanceInterpretation,
    build_ai_read_model_consumer_guidance,
    build_ai_read_model_governance_context,
    build_ai_read_model_governance_interpretation,
)
from ccass_core.research_context import ResearchContextPackage
from ccass_core.research_context_consumer import (
    ResearchContextConsumerView,
    build_research_context_consumer_view,
)
from ccass_core.research_governance_bridge import (
    ResearchGovernanceContext,
    build_research_governance_context,
)
from ccass_core.research_governance_interpretation import (
    ResearchGovernanceInterpretation,
    build_research_governance_interpretation,
)
from ccass_core.source_trace import SourceTraceView

AI_RESEARCH_CONTEXT_ASSEMBLY_VERSION = "v0.1"
AI_RESEARCH_CONTEXT_ASSEMBLY_SURFACE = "ai_research_context_assembly"


class AIResearchContextAssemblyContractMeta(BaseModel):
    version: str = AI_RESEARCH_CONTEXT_ASSEMBLY_VERSION
    surface: str = AI_RESEARCH_CONTEXT_ASSEMBLY_SURFACE


class AIResearchInputBlock(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    available: bool = False
    summary: str = "unavailable"
    reference: str = "not available"
    warnings: list[str] = Field(default_factory=list)


class AIResearchContextAssembly(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    identity: AIReadModelIdentity | None = None
    research_context_available: bool = False
    ai_read_model_available: bool = False
    governance_available: bool = False
    research_context_consumer_view: ResearchContextConsumerView | None = None
    research_governance_context: ResearchGovernanceContext | None = None
    research_governance_interpretation: ResearchGovernanceInterpretation | None = None
    ai_read_model_consumer_view: AIReadModelConsumerView | None = None
    ai_read_model_governance_context: AIReadModelGovernanceContext | None = None
    ai_read_model_governance_interpretation: AIReadModelGovernanceInterpretation | None = None
    ai_read_model_consumer_guidance: AIReadModelConsumerUsageGuidance | None = None
    input_blocks: list[AIResearchInputBlock] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str = "AI research context assembly is unavailable."
    contract_meta: AIResearchContextAssemblyContractMeta = Field(
        default_factory=AIResearchContextAssemblyContractMeta
    )


def build_ai_research_context_assembly(
    *,
    research_context_package: ResearchContextPackage | None = None,
    research_context_consumer_view: ResearchContextConsumerView | None = None,
    ai_read_model_consumer_view: AIReadModelConsumerView | None = None,
    source_trace: SourceTraceView | None = None,
    surface: str = AI_RESEARCH_CONTEXT_ASSEMBLY_SURFACE,
) -> AIResearchContextAssembly:
    if research_context_consumer_view is None and research_context_package is not None:
        research_context_consumer_view = build_research_context_consumer_view(
            research_context_package,
            source_trace=source_trace,
        )

    research_governance_context = (
        research_context_consumer_view.governance_context
        if research_context_consumer_view is not None
        else None
    )
    research_governance_interpretation = (
        research_context_consumer_view.governance_interpretation
        if research_context_consumer_view is not None
        else None
    )
    if (
        research_context_consumer_view is not None
        and research_context_package is not None
        and (
            research_governance_context is None
            or research_governance_interpretation is None
        )
    ):
        research_governance_context = build_research_governance_context(
            research_context_package,
            source_trace=source_trace,
        )
        research_governance_interpretation = build_research_governance_interpretation(
            research_context_consumer_view.model_copy(
                update={"governance_context": research_governance_context}
            ),
            research_governance_context,
        )
        research_context_consumer_view = research_context_consumer_view.model_copy(
            update={
                "governance_context": research_governance_context,
                "governance_interpretation": research_governance_interpretation,
            }
        )

    ai_read_model_governance_context = (
        ai_read_model_consumer_view.governance_context
        if ai_read_model_consumer_view is not None
        else None
    )
    ai_read_model_governance_interpretation = (
        ai_read_model_consumer_view.governance_interpretation
        if ai_read_model_consumer_view is not None
        else None
    )
    ai_read_model_consumer_guidance = (
        ai_read_model_consumer_view.consumer_guidance
        if ai_read_model_consumer_view is not None
        else None
    )
    if (
        ai_read_model_consumer_view is not None
        and ai_read_model_consumer_view.read_model is not None
        and (
            ai_read_model_governance_context is None
            or ai_read_model_governance_interpretation is None
            or ai_read_model_consumer_guidance is None
        )
    ):
        ai_read_model_governance_context = build_ai_read_model_governance_context(
            ai_read_model_consumer_view.read_model,
            source_trace=source_trace,
        )
        ai_read_model_governance_interpretation = build_ai_read_model_governance_interpretation(
            ai_read_model_governance_context
        )
        ai_read_model_consumer_guidance = build_ai_read_model_consumer_guidance(
            ai_read_model_governance_context,
            ai_read_model_governance_interpretation,
        )
        ai_read_model_consumer_view = ai_read_model_consumer_view.model_copy(
            update={
                "governance_context": ai_read_model_governance_context,
                "governance_interpretation": ai_read_model_governance_interpretation,
                "consumer_guidance": ai_read_model_consumer_guidance,
            }
        )

    identity = _identity(
        research_context_consumer_view=research_context_consumer_view,
        ai_read_model_consumer_view=ai_read_model_consumer_view,
    )
    research_context_available = bool(
        research_context_consumer_view is not None and research_context_consumer_view.available
    )
    ai_read_model_available = bool(
        ai_read_model_consumer_view is not None and ai_read_model_consumer_view.available
    )
    governance_available = bool(
        research_governance_context is not None or ai_read_model_governance_context is not None
    )
    input_blocks = _input_blocks(
        research_context_consumer_view=research_context_consumer_view,
        research_governance_context=research_governance_context,
        research_governance_interpretation=research_governance_interpretation,
        ai_read_model_consumer_view=ai_read_model_consumer_view,
        ai_read_model_governance_context=ai_read_model_governance_context,
        ai_read_model_governance_interpretation=ai_read_model_governance_interpretation,
        ai_read_model_consumer_guidance=ai_read_model_consumer_guidance,
    )
    warnings = _warnings(
        research_context_consumer_view=research_context_consumer_view,
        research_governance_context=research_governance_context,
        ai_read_model_consumer_view=ai_read_model_consumer_view,
        ai_read_model_governance_context=ai_read_model_governance_context,
        ai_read_model_consumer_guidance=ai_read_model_consumer_guidance,
    )
    available = research_context_available or ai_read_model_available
    summary = _summary_text(
        identity=identity,
        research_context_available=research_context_available,
        ai_read_model_available=ai_read_model_available,
        governance_available=governance_available,
        warnings=warnings,
        research_governance_interpretation=research_governance_interpretation,
        ai_read_model_governance_interpretation=ai_read_model_governance_interpretation,
    )
    return AIResearchContextAssembly(
        available=available,
        identity=identity,
        research_context_available=research_context_available,
        ai_read_model_available=ai_read_model_available,
        governance_available=governance_available,
        research_context_consumer_view=research_context_consumer_view,
        research_governance_context=research_governance_context,
        research_governance_interpretation=research_governance_interpretation,
        ai_read_model_consumer_view=ai_read_model_consumer_view,
        ai_read_model_governance_context=ai_read_model_governance_context,
        ai_read_model_governance_interpretation=ai_read_model_governance_interpretation,
        ai_read_model_consumer_guidance=ai_read_model_consumer_guidance,
        input_blocks=input_blocks,
        warnings=warnings,
        summary=summary,
        contract_meta=AIResearchContextAssemblyContractMeta(surface=surface),
    )


def _identity(
    *,
    research_context_consumer_view: ResearchContextConsumerView | None,
    ai_read_model_consumer_view: AIReadModelConsumerView | None,
) -> AIReadModelIdentity | None:
    if research_context_consumer_view is not None and isinstance(
        research_context_consumer_view.identity, AIReadModelIdentity
    ):
        return research_context_consumer_view.identity
    if ai_read_model_consumer_view is not None and ai_read_model_consumer_view.read_model is not None:
        return ai_read_model_consumer_view.read_model.identity
    return None


def _input_blocks(
    *,
    research_context_consumer_view: ResearchContextConsumerView | None,
    research_governance_context: ResearchGovernanceContext | None,
    research_governance_interpretation: ResearchGovernanceInterpretation | None,
    ai_read_model_consumer_view: AIReadModelConsumerView | None,
    ai_read_model_governance_context: AIReadModelGovernanceContext | None,
    ai_read_model_governance_interpretation: AIReadModelGovernanceInterpretation | None,
    ai_read_model_consumer_guidance: AIReadModelConsumerUsageGuidance | None,
) -> list[AIResearchInputBlock]:
    blocks: list[AIResearchInputBlock] = []
    if research_context_consumer_view is not None:
        blocks.append(
            AIResearchInputBlock(
                name="research_context",
                available=research_context_consumer_view.available,
                summary=(
                    research_governance_interpretation.summary
                    if research_governance_interpretation is not None
                    else (
                        research_governance_context.summary
                        if research_governance_context is not None
                        else "Research context is unavailable."
                    )
                ),
                reference=_reference_from_research_context(research_context_consumer_view),
                warnings=list(research_context_consumer_view.warnings),
            )
        )
    if research_governance_context is not None:
        blocks.append(
            AIResearchInputBlock(
                name="research_governance",
                available=True,
                summary=(
                    research_governance_interpretation.summary
                    if research_governance_interpretation is not None
                    else research_governance_context.summary
                ),
                reference=research_governance_context.source_trace_reference,
                warnings=list(research_governance_context.warnings),
            )
        )
    if ai_read_model_consumer_view is not None:
        blocks.append(
            AIResearchInputBlock(
                name="ai_read_model",
                available=ai_read_model_consumer_view.available,
                summary=ai_read_model_consumer_view.summary or "AI Read Model is unavailable.",
                reference=_reference_from_ai_read_model(ai_read_model_consumer_view),
                warnings=list(ai_read_model_consumer_view.warnings),
            )
        )
    if ai_read_model_governance_context is not None:
        blocks.append(
            AIResearchInputBlock(
                name="ai_read_model_governance",
                available=True,
                summary=(
                    ai_read_model_governance_interpretation.summary
                    if ai_read_model_governance_interpretation is not None
                    else ai_read_model_governance_context.summary
                ),
                reference=ai_read_model_governance_context.source_trace_reference,
                warnings=list(ai_read_model_governance_context.warnings),
            )
        )
    if ai_read_model_consumer_guidance is not None:
        blocks.append(
            AIResearchInputBlock(
                name="ai_read_model_guidance",
                available=True,
                summary=ai_read_model_consumer_guidance.summary,
                reference=ai_read_model_consumer_guidance.source_trace_reference,
                warnings=[],
            )
        )
    return blocks


def _reference_from_research_context(
    research_context_consumer_view: ResearchContextConsumerView,
) -> str:
    if research_context_consumer_view.governance_context is not None:
        return research_context_consumer_view.governance_context.source_trace_reference
    if research_context_consumer_view.contract_meta is not None:
        return (
            f"{research_context_consumer_view.contract_meta.version} / "
            f"{research_context_consumer_view.contract_meta.surface}"
        )
    return "not available"


def _reference_from_ai_read_model(
    ai_read_model_consumer_view: AIReadModelConsumerView,
) -> str:
    if ai_read_model_consumer_view.governance_context is not None:
        return ai_read_model_consumer_view.governance_context.source_trace_reference
    if ai_read_model_consumer_view.read_model is not None:
        return (
            f"{ai_read_model_consumer_view.read_model.contract_meta.version} / "
            f"{ai_read_model_consumer_view.read_model.contract_meta.surface}"
        )
    return "not available"


def _warnings(
    *,
    research_context_consumer_view: ResearchContextConsumerView | None,
    research_governance_context: ResearchGovernanceContext | None,
    ai_read_model_consumer_view: AIReadModelConsumerView | None,
    ai_read_model_governance_context: AIReadModelGovernanceContext | None,
    ai_read_model_consumer_guidance: AIReadModelConsumerUsageGuidance | None,
) -> list[str]:
    warning_sets = [
        research_context_consumer_view.warnings if research_context_consumer_view is not None else [],
        research_governance_context.warnings if research_governance_context is not None else [],
        ai_read_model_consumer_view.warnings if ai_read_model_consumer_view is not None else [],
        ai_read_model_governance_context.warnings if ai_read_model_governance_context is not None else [],
        (
            ai_read_model_consumer_guidance.warnings
            if ai_read_model_consumer_guidance is not None
            else []
        ),
    ]
    flattened = [warning for warning_group in warning_sets for warning in warning_group]
    return list(dict.fromkeys(flattened))


def _summary_text(
    *,
    identity: AIReadModelIdentity | None,
    research_context_available: bool,
    ai_read_model_available: bool,
    governance_available: bool,
    warnings: list[str],
    research_governance_interpretation: ResearchGovernanceInterpretation | None,
    ai_read_model_governance_interpretation: AIReadModelGovernanceInterpretation | None,
) -> str:
    stock_code = identity.stock_code if identity is not None else "unavailable"
    research_state = "available" if research_context_available else "unavailable"
    ai_state = "available" if ai_read_model_available else "unavailable"
    governance_state = "linked" if governance_available else "unavailable"
    warning_summary = f"{len(warnings)} warning(s)"
    research_summary = (
        research_governance_interpretation.summary
        if research_governance_interpretation is not None
        else "Research governance context is unavailable."
    )
    ai_summary = (
        ai_read_model_governance_interpretation.summary
        if ai_read_model_governance_interpretation is not None
        else "AI Read Model governance context is unavailable."
    )
    return (
        "AI research context assembly: "
        f"stock_code={stock_code}; "
        f"research_context={research_state}; "
        f"ai_read_model={ai_state}; "
        f"governance={governance_state}; "
        f"warnings={warning_summary}; "
        f"research_governance={research_summary}; "
        f"ai_read_model_governance={ai_summary}"
    )

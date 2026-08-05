from __future__ import annotations

from pydantic import BaseModel, Field

from ccass_core.research_context import ResearchContextPackage, ResearchContextQualityContext
from ccass_core.research_context_consumer import (
    ResearchContextConsumerView,
    build_research_context_consumer_view,
)
from ccass_core.research_workflow import (
    ResearchWorkflowContractMeta,
    ResearchWorkflowSession,
    ResearchWorkflowSessionMetadata,
    ResearchWorkflowState,
)


class ResearchWorkflowConsumerView(BaseModel):
    available: bool = False
    workflow_state: ResearchWorkflowState = ResearchWorkflowState.CREATED
    session_metadata: ResearchWorkflowSessionMetadata | None = None
    research_context_package: ResearchContextPackage | None = None
    research_context_consumer_view: ResearchContextConsumerView | None = None
    context_available: bool = False
    quality_context: ResearchContextQualityContext | None = None
    warnings: list[str] = Field(default_factory=list)
    summary: str | None = None
    contract_meta: ResearchWorkflowContractMeta | None = None


def build_research_workflow_consumer_view(
    workflow: ResearchWorkflowSession | None,
) -> ResearchWorkflowConsumerView:
    if workflow is None:
        return ResearchWorkflowConsumerView(summary="No research workflow session is available.")

    research_context_package = workflow.research_context_package
    research_context_consumer_view = workflow.consumer_view
    if research_context_package is not None and research_context_consumer_view is None:
        research_context_consumer_view = build_research_context_consumer_view(research_context_package)

    quality_context = (
        research_context_consumer_view.quality_context if research_context_consumer_view else None
    )
    warnings = (
        list(research_context_consumer_view.warnings)
        if research_context_consumer_view is not None
        else []
    )
    context_available = (
        research_context_consumer_view.available
        if research_context_consumer_view is not None
        else False
    )
    return ResearchWorkflowConsumerView(
        available=True,
        workflow_state=workflow.state,
        session_metadata=workflow.metadata,
        research_context_package=research_context_package,
        research_context_consumer_view=research_context_consumer_view,
        context_available=context_available,
        quality_context=quality_context,
        warnings=warnings,
        summary=_workflow_summary(
            workflow.state,
            workflow.metadata,
            context_available=context_available,
            quality_context=quality_context,
        ),
        contract_meta=workflow.contract_meta,
    )


def _workflow_summary(
    state: ResearchWorkflowState,
    metadata: ResearchWorkflowSessionMetadata,
    *,
    context_available: bool,
    quality_context: ResearchContextQualityContext | None,
) -> str:
    summary = f"Research workflow {state.value} for {metadata.stock_code}."
    if not context_available:
        return f"{summary} Research context is not yet available."
    freshness = quality_context.freshness_status if quality_context else "unknown"
    return f"{summary} Research context is available with {freshness} quality."

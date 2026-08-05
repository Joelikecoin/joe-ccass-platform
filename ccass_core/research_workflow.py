from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.models import (
    AnnouncementsResponse,
    CapitalInformationResponse,
    CcassResponse,
    OfficersResponse,
    PriceHistoryResponse,
    StockEventsResponse,
)
from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.compute import AnalysisResult
from ccass_core.research_context import (
    RESEARCH_CONTEXT_SURFACE as RESEARCH_CONTEXT_PACKAGE_SURFACE,
    ResearchContextPackage,
    build_research_context_package,
)
from ccass_core.research_context_consumer import (
    ResearchContextConsumerView,
    build_research_context_consumer_view,
)

RESEARCH_WORKFLOW_VERSION = "v0.1"
RESEARCH_WORKFLOW_SURFACE = "research_workflow"


class ResearchWorkflowState(StrEnum):
    CREATED = "created"
    LOADED = "loaded"
    READY = "ready"


class ResearchWorkflowContractMeta(BaseModel):
    version: str = RESEARCH_WORKFLOW_VERSION
    surface: str = RESEARCH_WORKFLOW_SURFACE


class ResearchWorkflowSessionMetadata(BaseModel):
    session_id: str
    stock_code: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    loaded_at: datetime | None = None
    ready_at: datetime | None = None
    research_context_package_version: str | None = None
    research_context_package_surface: str | None = None


class ResearchWorkflowSession(BaseModel):
    state: ResearchWorkflowState = ResearchWorkflowState.CREATED
    metadata: ResearchWorkflowSessionMetadata
    research_context_package: ResearchContextPackage | None = None
    consumer_view: ResearchContextConsumerView | None = None
    contract_meta: ResearchWorkflowContractMeta = Field(
        default_factory=ResearchWorkflowContractMeta
    )


def create_research_workflow_session(
    *,
    stock_code: str,
    session_id: str | None = None,
    surface: str = RESEARCH_WORKFLOW_SURFACE,
) -> ResearchWorkflowSession:
    metadata = ResearchWorkflowSessionMetadata(
        session_id=session_id or _default_session_id(stock_code),
        stock_code=stock_code,
    )
    return ResearchWorkflowSession(
        state=ResearchWorkflowState.CREATED,
        metadata=metadata,
        contract_meta=ResearchWorkflowContractMeta(surface=surface),
    )


def load_research_context_into_workflow(
    workflow: ResearchWorkflowSession,
    research_context_package: ResearchContextPackage | None,
) -> ResearchWorkflowSession:
    if research_context_package is None:
        return workflow.model_copy(
            deep=True,
            update={
                "state": ResearchWorkflowState.CREATED,
                "research_context_package": None,
                "consumer_view": None,
                "metadata": workflow.metadata.model_copy(
                    deep=True,
                    update={
                        "loaded_at": None,
                        "ready_at": None,
                        "research_context_package_version": None,
                        "research_context_package_surface": None,
                    },
                ),
            },
        )

    loaded_at = datetime.now(UTC)
    consumer_view = build_research_context_consumer_view(research_context_package)
    return workflow.model_copy(
        deep=True,
        update={
            "state": ResearchWorkflowState.LOADED,
            "research_context_package": research_context_package,
            "consumer_view": consumer_view,
            "metadata": workflow.metadata.model_copy(
                deep=True,
                update={
                    "loaded_at": loaded_at,
                    "ready_at": None,
                    "research_context_package_version": research_context_package.contract_meta.version,
                    "research_context_package_surface": research_context_package.contract_meta.surface,
                },
            ),
        },
    )


def mark_research_workflow_ready(workflow: ResearchWorkflowSession) -> ResearchWorkflowSession:
    if workflow.research_context_package is None:
        return workflow

    ready_at = datetime.now(UTC)
    loaded_at = workflow.metadata.loaded_at or ready_at
    return workflow.model_copy(
        deep=True,
        update={
            "state": ResearchWorkflowState.READY,
            "metadata": workflow.metadata.model_copy(
                deep=True,
                update={
                    "loaded_at": loaded_at,
                    "ready_at": ready_at,
                },
            ),
        },
    )


def build_research_workflow_session_from_result(
    *,
    code: str,
    response: CcassResponse | None,
    analysis: AnalysisResult | None = None,
    previous_response: CcassResponse | None = None,
    snapshot_id: int | None = None,
    previous_snapshot_id: int | None = None,
    announcements: AnnouncementsResponse | None = None,
    stock_events: StockEventsResponse | None = None,
    capital_information: CapitalInformationResponse | None = None,
    officers: OfficersResponse | None = None,
    price_history: PriceHistoryResponse | None = None,
    session_id: str | None = None,
    surface: str = RESEARCH_WORKFLOW_SURFACE,
    research_context_surface: str = RESEARCH_CONTEXT_PACKAGE_SURFACE,
) -> ResearchWorkflowSession:
    workflow = create_research_workflow_session(
        stock_code=code,
        session_id=session_id,
        surface=surface,
    )
    if response is None:
        return workflow

    ai_read_model = build_ai_read_model_v0_1(
        code=code,
        response=response,
        surface=research_context_surface,
        analysis=analysis,
        previous_response=previous_response,
        snapshot_id=snapshot_id,
        previous_snapshot_id=previous_snapshot_id,
        announcements=announcements,
        price_history=price_history,
    )
    research_context_package = build_research_context_package(
        ai_read_model=ai_read_model,
        stock_events=stock_events,
        officers=officers,
        capital_information=capital_information,
    )
    loaded = load_research_context_into_workflow(workflow, research_context_package)
    return mark_research_workflow_ready(loaded)


def _default_session_id(stock_code: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"research-{stock_code}-{timestamp}"

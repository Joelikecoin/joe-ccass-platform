from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models import (
    AnnouncementsResponse,
    CapitalInformationResponse,
    CcassResponse,
    HoldingRow,
    HoldingsSummary,
    OfficersResponse,
    PriceHistoryResponse,
    StockEventsResponse,
)
from ccass_core.ai_read_model import (
    AIReadModelComparisonContext,
    AIReadModelContractMeta,
    AIReadModelErrorState,
    AIReadModelIdentity,
    AIReadModelProvenance,
    AIReadModelSnapshotReference,
    AIReadModelSurfaceReference,
    AIReadModelV0_1,
)

RESEARCH_CONTEXT_VERSION = "v0.1"
RESEARCH_CONTEXT_SURFACE = "research_context_package"


class ResearchContextOwnershipContext(BaseModel):
    surface: AIReadModelSurfaceReference | None = None
    current_snapshot: AIReadModelSnapshotReference | None = None
    holdings_summary: HoldingsSummary | None = None
    holdings: list[HoldingRow] = Field(default_factory=list)


class ResearchContextMarketContext(BaseModel):
    surface: AIReadModelSurfaceReference | None = None
    price_history: PriceHistoryResponse | None = None


class ResearchContextCompanyContext(BaseModel):
    announcements_surface: AIReadModelSurfaceReference | None = None
    announcements: AnnouncementsResponse | None = None
    stock_events_surface: AIReadModelSurfaceReference | None = None
    stock_events: StockEventsResponse | None = None
    officers_surface: AIReadModelSurfaceReference | None = None
    officers: OfficersResponse | None = None
    capital_information_surface: AIReadModelSurfaceReference | None = None
    capital_information: CapitalInformationResponse | None = None


class ResearchContextHistoricalContext(BaseModel):
    snapshot_id: int | None = None
    current_snapshot: AIReadModelSnapshotReference | None = None
    previous_snapshot: AIReadModelSnapshotReference | None = None
    comparison_context: AIReadModelComparisonContext | None = None
    history_snapshots: list[AIReadModelSnapshotReference] = Field(default_factory=list)


class ResearchContextQualityContext(BaseModel):
    provenance: AIReadModelProvenance
    freshness_status: str
    warnings: list[str] = Field(default_factory=list)
    error_state: AIReadModelErrorState | None = None


class ResearchContextContractMeta(BaseModel):
    version: str = RESEARCH_CONTEXT_VERSION
    surface: str = RESEARCH_CONTEXT_SURFACE


class ResearchContextPackage(BaseModel):
    identity: AIReadModelIdentity
    ownership_context: ResearchContextOwnershipContext
    market_context: ResearchContextMarketContext
    company_context: ResearchContextCompanyContext
    historical_context: ResearchContextHistoricalContext
    quality_context: ResearchContextQualityContext
    contract_meta: ResearchContextContractMeta


def build_research_context_package(
    *,
    ai_read_model: AIReadModelV0_1,
    stock_events: StockEventsResponse | None = None,
    officers: OfficersResponse | None = None,
    capital_information: CapitalInformationResponse | None = None,
    history_snapshots: Sequence[AIReadModelSnapshotReference] = (),
    surface: str = RESEARCH_CONTEXT_SURFACE,
) -> ResearchContextPackage:
    ccass_response = ai_read_model.payload.ccass
    ownership_surface = _ccass_surface_reference(ai_read_model)
    market_surface = _market_surface_reference(ai_read_model)
    company_surfaces = _company_surface_references(
        ai_read_model,
        stock_events=stock_events,
        officers=officers,
        capital_information=capital_information,
    )
    warnings = _collect_warnings(
        ai_read_model,
        stock_events=stock_events,
        officers=officers,
        capital_information=capital_information,
    )
    current_snapshot = _current_snapshot_reference(ai_read_model)
    historical_context = ResearchContextHistoricalContext(
        snapshot_id=ai_read_model.history.snapshot_id,
        current_snapshot=current_snapshot,
        previous_snapshot=ai_read_model.history.previous_snapshot,
        comparison_context=ai_read_model.history.comparison_context,
        history_snapshots=list(history_snapshots),
    )
    return ResearchContextPackage(
        identity=ai_read_model.identity,
        ownership_context=ResearchContextOwnershipContext(
            surface=ownership_surface,
            current_snapshot=current_snapshot,
            holdings_summary=ccass_response.holdings_summary if ccass_response else None,
            holdings=list(ccass_response.holdings) if ccass_response else [],
        ),
        market_context=ResearchContextMarketContext(
            surface=market_surface,
            price_history=ai_read_model.payload.price_history,
        ),
        company_context=ResearchContextCompanyContext(
            announcements_surface=company_surfaces["announcements"],
            announcements=ai_read_model.payload.announcements,
            stock_events_surface=company_surfaces["stock_events"],
            stock_events=stock_events,
            officers_surface=company_surfaces["officers"],
            officers=officers,
            capital_information_surface=company_surfaces["capital_information"],
            capital_information=capital_information,
        ),
        historical_context=historical_context,
        quality_context=ResearchContextQualityContext(
            provenance=ai_read_model.provenance,
            freshness_status=ai_read_model.quality.freshness_status,
            warnings=warnings,
            error_state=ai_read_model.quality.error_state,
        ),
        contract_meta=ResearchContextContractMeta(surface=surface),
    )


def _current_snapshot_reference(ai_read_model: AIReadModelV0_1) -> AIReadModelSnapshotReference | None:
    if ai_read_model.payload.ccass is None:
        return None
    return AIReadModelSnapshotReference(
        snapshot_id=ai_read_model.history.snapshot_id,
        snapshot_date=ai_read_model.timing.data_as_of,
        data_as_of=ai_read_model.timing.data_as_of,
        fetched_at=ai_read_model.timing.fetched_at,
        source=ai_read_model.provenance.source,
    )


def _ccass_surface_reference(ai_read_model: AIReadModelV0_1) -> AIReadModelSurfaceReference | None:
    ccass_response = ai_read_model.payload.ccass
    if ccass_response is None:
        return None
    return AIReadModelSurfaceReference(
        surface="ccass",
        available=True,
        source=ai_read_model.provenance.source,
        source_type=ai_read_model.provenance.source_type,
        data_as_of=ai_read_model.timing.data_as_of,
        fetched_at=ai_read_model.timing.fetched_at,
        row_count=len(ccass_response.holdings),
    )


def _market_surface_reference(ai_read_model: AIReadModelV0_1) -> AIReadModelSurfaceReference | None:
    price_history = ai_read_model.payload.price_history
    if price_history is None:
        return None
    return AIReadModelSurfaceReference(
        surface="price_history",
        available=True,
        source=price_history.metadata.source_name,
        source_type="market_price",
        data_as_of=price_history.metadata.data_as_of,
        fetched_at=price_history.metadata.fetched_at,
        row_count=len(price_history.prices),
    )


def _company_surface_references(
    ai_read_model: AIReadModelV0_1,
    *,
    stock_events: StockEventsResponse | None,
    officers: OfficersResponse | None,
    capital_information: CapitalInformationResponse | None,
) -> dict[str, AIReadModelSurfaceReference | None]:
    announcements = ai_read_model.payload.announcements
    return {
        "announcements": _surface_reference(
            surface="announcements",
            available=announcements is not None,
            source=announcements.metadata.source_name if announcements else None,
            source_type="company_announcements",
            data_as_of=announcements.metadata.data_as_of if announcements else None,
            fetched_at=announcements.metadata.fetched_at if announcements else None,
            row_count=len(announcements.announcements) if announcements else None,
        ),
        "stock_events": _surface_reference(
            surface="stock_events",
            available=stock_events is not None,
            source=stock_events.metadata.source_name if stock_events else None,
            source_type="stock_events",
            data_as_of=stock_events.metadata.data_as_of if stock_events else None,
            fetched_at=stock_events.metadata.fetched_at if stock_events else None,
            row_count=len(stock_events.stock_events) if stock_events else None,
        ),
        "officers": _surface_reference(
            surface="officers",
            available=officers is not None,
            source=officers.metadata.source_name if officers else None,
            source_type="officers",
            data_as_of=officers.metadata.data_as_of if officers else None,
            fetched_at=officers.metadata.fetched_at if officers else None,
            row_count=len(officers.officers) if officers else None,
        ),
        "capital_information": _surface_reference(
            surface="capital_information",
            available=capital_information is not None,
            source=capital_information.metadata.source_name if capital_information else None,
            source_type="capital_information",
            data_as_of=capital_information.metadata.data_as_of if capital_information else None,
            fetched_at=capital_information.metadata.fetched_at if capital_information else None,
            row_count=len(capital_information.capital_information) if capital_information else None,
        ),
    }


def _surface_reference(
    *,
    surface: str,
    available: bool,
    source: str | None,
    source_type: str | None,
    data_as_of: date | None,
    fetched_at: datetime | None,
    row_count: int | None,
) -> AIReadModelSurfaceReference:
    return AIReadModelSurfaceReference(
        surface=surface,
        available=available,
        source=source,
        source_type=source_type,
        data_as_of=data_as_of,
        fetched_at=fetched_at,
        row_count=row_count,
    )


def _collect_warnings(
    ai_read_model: AIReadModelV0_1,
    *,
    stock_events: StockEventsResponse | None,
    officers: OfficersResponse | None,
    capital_information: CapitalInformationResponse | None,
) -> list[str]:
    warnings = list(ai_read_model.quality.warnings)
    for response in (ai_read_model.payload.ccass, ai_read_model.payload.announcements, ai_read_model.payload.price_history, stock_events, officers, capital_information):
        if response is not None:
            warnings.extend(response.data_quality_warnings)
    return list(dict.fromkeys(warnings))

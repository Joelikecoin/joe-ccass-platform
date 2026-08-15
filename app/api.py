from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app import __version__
from app.data_quality import structured_warning
from app.config import Settings, get_settings
from app.errors import ErrorCode, PlatformError
from app.models import (
    AnnouncementsResponse,
    BigChangesResponse,
    CapitalInformationResponse,
    CcassResponse,
    ChangesResponse,
    ConcentrationResponse,
    OfficersResponse,
    PriceHistoryResponse,
    StockEventsResponse,
)
from app.services.ai_read_model import AIReadModelService, get_ai_read_model_service
from app.services.announcements import AnnouncementsService, get_announcements_service
from app.services.big_changes import BigChangesService, get_big_changes_service
from app.services.ccass import CcassService, get_ccass_service
from app.services.changes import ChangesService, get_changes_service
from app.services.concentration import ConcentrationService, get_concentration_service
from app.services.capital_information import CapitalInformationService, get_capital_information_service
from app.services.officers import OfficersService, get_officers_service
from app.services.price_history import PriceHistoryService, get_price_history_service
from app.services.stock_events import StockEventsService, get_stock_events_service
from ccass_core.big_changes_report import build_big_changes_markdown_report
from ccass_core.ai_read_model import AIReadModelV0_1
from ccass_core.changes_report import build_changes_markdown_report
from ccass_core.compute import compute_analysis
from ccass_core.concentration_report import build_concentration_markdown_report
from ccass_core.normalize import normalize_stock_code
from ccass_core.report import build_markdown_report

app = FastAPI(
    title="Joe CCASS Platform API",
    version=__version__,
    description="AI-ready Hong Kong CCASS research data. Not investment advice.",
)


def verify_api_key(
    settings: Annotated[Settings, Depends(get_settings)],
    key: str | None = Query(default=None),
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    if not settings.api_key:
        return
    bearer = authorization.removeprefix("Bearer ") if authorization else None
    if settings.api_key not in {key, x_api_key, bearer}:
        raise PlatformError(
            ErrorCode.AUTH_FAILED,
            "A valid API key is required.",
            status_code=401,
        )


@app.exception_handler(PlatformError)
async def platform_error_handler(_: Request, exc: PlatformError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.as_dict())


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get(
    "/api/v1/stocks/{stock_code}/holdings",
    response_model=CcassResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["holdings"],
)
async def get_latest_holdings(
    stock_code: str,
    holdings_limit: int = Query(default=15, ge=1, le=100),
    service: CcassService = Depends(get_ccass_service),
) -> CcassResponse:
    return await service.get_stock_data(stock_code, holdings_limit=holdings_limit)


@app.get(
    "/api/v1/stocks/{stock_code}/changes",
    response_model=ChangesResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["changes"],
)
async def get_stock_changes(
    stock_code: str,
    snapshot_date: date,
    compare_date: date,
    service: ChangesService = Depends(get_changes_service),
) -> ChangesResponse:
    return service.get_changes(
        stock_code,
        snapshot_date=snapshot_date,
        compare_date=compare_date,
    )


@app.get(
    "/api/v1/stocks/{stock_code}/changes/report",
    response_class=PlainTextResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["changes"],
)
async def get_stock_changes_report(
    stock_code: str,
    snapshot_date: date,
    compare_date: date,
    service: ChangesService = Depends(get_changes_service),
) -> PlainTextResponse:
    response = service.get_changes(
        stock_code,
        snapshot_date=snapshot_date,
        compare_date=compare_date,
    )
    return PlainTextResponse(
        build_changes_markdown_report(response),
        media_type="text/markdown; charset=utf-8",
    )


@app.get(
    "/api/v1/stocks/{stock_code}/big-changes",
    response_model=BigChangesResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["big-changes"],
)
async def get_stock_big_changes(
    stock_code: str,
    snapshot_date: date,
    compare_date: date,
    threshold_shares: int | None = Query(default=None, ge=1),
    service: BigChangesService = Depends(get_big_changes_service),
) -> BigChangesResponse:
    return service.get_big_changes(
        stock_code,
        snapshot_date=snapshot_date,
        compare_date=compare_date,
        threshold_shares=threshold_shares,
    )


@app.get(
    "/api/v1/stocks/{stock_code}/big-changes/report",
    response_class=PlainTextResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["big-changes"],
)
async def get_stock_big_changes_report(
    stock_code: str,
    snapshot_date: date,
    compare_date: date,
    threshold_shares: int | None = Query(default=None, ge=1),
    service: BigChangesService = Depends(get_big_changes_service),
) -> PlainTextResponse:
    response = service.get_big_changes(
        stock_code,
        snapshot_date=snapshot_date,
        compare_date=compare_date,
        threshold_shares=threshold_shares,
    )
    return PlainTextResponse(
        build_big_changes_markdown_report(response),
        media_type="text/markdown; charset=utf-8",
    )


@app.get(
    "/api/v1/stocks/{stock_code}/concentration",
    response_model=ConcentrationResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["concentration"],
)
async def get_stock_concentration(
    stock_code: str,
    snapshot_date: date,
    top_holders_limit: int = Query(default=10, ge=1, le=100),
    service: ConcentrationService = Depends(get_concentration_service),
) -> ConcentrationResponse:
    return service.get_concentration(
        stock_code,
        snapshot_date=snapshot_date,
        top_holders_limit=top_holders_limit,
    )


@app.get(
    "/api/v1/stocks/{stock_code}/concentration/report",
    response_class=PlainTextResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["concentration"],
)
async def get_stock_concentration_report(
    stock_code: str,
    snapshot_date: date,
    top_holders_limit: int = Query(default=10, ge=1, le=100),
    service: ConcentrationService = Depends(get_concentration_service),
) -> PlainTextResponse:
    response = service.get_concentration(
        stock_code,
        snapshot_date=snapshot_date,
        top_holders_limit=top_holders_limit,
    )
    return PlainTextResponse(
        build_concentration_markdown_report(response),
        media_type="text/markdown; charset=utf-8",
    )


@app.get(
    "/api/v1/stocks/{stock_code}/prices",
    response_model=PriceHistoryResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["prices"],
)
async def get_stock_prices(
    stock_code: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    service: PriceHistoryService = Depends(get_price_history_service),
) -> PriceHistoryResponse:
    return await service.get_price_history(
        stock_code,
        start_date=start_date,
        end_date=end_date,
    )


@app.get(
    "/api/v1/stocks/{stock_code}/announcements",
    response_model=AnnouncementsResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["announcements"],
)
async def get_stock_announcements(
    stock_code: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    service: AnnouncementsService = Depends(get_announcements_service),
) -> AnnouncementsResponse:
    return await service.get_announcements(
        stock_code,
        start_date=start_date,
        end_date=end_date,
    )


@app.get(
    "/api/v1/stocks/{stock_code}/officers",
    response_model=OfficersResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["officers"],
)
async def get_stock_officers(
    stock_code: str,
    service: OfficersService = Depends(get_officers_service),
) -> OfficersResponse:
    return await service.get_officers(stock_code)


@app.get(
    "/api/v1/stocks/{stock_code}/stock-events",
    response_model=StockEventsResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["stock-events"],
)
async def get_stock_events(
    stock_code: str,
    service: StockEventsService = Depends(get_stock_events_service),
) -> StockEventsResponse:
    return await service.get_stock_events(stock_code)


@app.get(
    "/api/v1/stocks/{stock_code}/capital-information",
    response_model=CapitalInformationResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["capital-information"],
)
async def get_capital_information(
    stock_code: str,
    service: CapitalInformationService = Depends(get_capital_information_service),
) -> CapitalInformationResponse:
    return await service.get_capital_information(stock_code)


@app.get(
    "/api/v1/ccass/{code}",
    response_model=CcassResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["ccass"],
)
async def get_ccass_stock_data(
    code: str,
    holdings_limit: int = Query(default=15, ge=1, le=100),
    service: CcassService = Depends(get_ccass_service),
) -> CcassResponse:
    return await service.get_stock_data(code, holdings_limit=holdings_limit)


@app.get(
    "/api/v1/ccass/{code}/ai-read-model",
    response_model=AIReadModelV0_1,
    dependencies=[Depends(verify_api_key)],
    tags=["ccass"],
)
async def get_ccass_ai_read_model(
    code: str,
    service: AIReadModelService = Depends(get_ai_read_model_service),
) -> AIReadModelV0_1:
    return await service.get_read_model(code)


@app.get(
    "/api/v1/ccass/{code}/report",
    response_class=PlainTextResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["ccass"],
)
async def get_ccass_stock_report(
    code: str,
    holdings_limit: int = Query(default=20, ge=1, le=100),
    big_change_threshold: int = Query(default=1_000_000, ge=0),
    announcements_service: AnnouncementsService = Depends(get_announcements_service),
    stock_events_service: StockEventsService = Depends(get_stock_events_service),
    capital_information_service: CapitalInformationService = Depends(get_capital_information_service),
    officers_service: OfficersService = Depends(get_officers_service),
    service: CcassService = Depends(get_ccass_service),
) -> PlainTextResponse:
    normalized = normalize_stock_code(code)
    response = await service.get_stock_data(normalized, holdings_limit=holdings_limit)
    previous = None
    lkg_repository = getattr(service, "lkg_repository", None)
    if lkg_repository is not None and response.metadata.data_as_of is not None:
        previous_snapshot = lkg_repository.previous(
            normalized,
            before_date=response.metadata.data_as_of,
            include_partial=False,
        )
        previous = previous_snapshot.to_response() if previous_snapshot is not None else None
    analysis = compute_analysis(
        response,
        previous=previous,
        big_change_threshold=big_change_threshold,
    )
    announcements = response.announcements
    if announcements is None:
        try:
            announcements = await announcements_service.get_announcements(normalized)
            response = response.model_copy(update={"announcements": announcements})
            response.data_quality_warnings.extend(announcements.data_quality_warnings)
        except PlatformError:
            announcements = None

    stock_events = response.stock_events
    if stock_events is None:
        try:
            stock_events = await stock_events_service.get_stock_events(normalized)
            response = response.model_copy(update={"stock_events": stock_events})
        except PlatformError as exc:
            stock_events = None
            response.data_quality_warnings.append(
                structured_warning(
                    "DATA_LIMITATION",
                    "STOCK_EVENTS_UNAVAILABLE",
                    f"Stock events are unavailable ({exc.code}: {exc.message}).",
                )
            )
        except Exception as exc:
            stock_events = None
            response.data_quality_warnings.append(
                structured_warning(
                    "DATA_LIMITATION",
                    "STOCK_EVENTS_UNAVAILABLE",
                    f"Stock events are unavailable ({type(exc).__name__}).",
                )
            )
        else:
            response.data_quality_warnings.extend(stock_events.data_quality_warnings)
    capital_information = response.capital_information
    if capital_information is None:
        try:
            capital_information = await capital_information_service.get_capital_information(normalized)
            response = response.model_copy(update={"capital_information": capital_information})
        except PlatformError as exc:
            capital_information = None
            response.data_quality_warnings.append(
                structured_warning(
                    "DATA_LIMITATION",
                    "CAPITAL_INFORMATION_UNAVAILABLE",
                    f"Capital information is unavailable ({exc.code}: {exc.message}).",
                )
            )
        except Exception as exc:
            capital_information = None
            response.data_quality_warnings.append(
                structured_warning(
                    "DATA_LIMITATION",
                    "CAPITAL_INFORMATION_UNAVAILABLE",
                    f"Capital information is unavailable ({type(exc).__name__}).",
                )
            )
        else:
            response.data_quality_warnings.extend(capital_information.data_quality_warnings)
    officers = response.officers
    if officers is None:
        try:
            officers = await officers_service.get_officers(normalized)
            response = response.model_copy(update={"officers": officers})
        except PlatformError:
            officers = None
        else:
            response.data_quality_warnings.extend(officers.data_quality_warnings)
    report = build_markdown_report(
        response,
        code=normalized,
        analysis=analysis,
        announcements=announcements,
        stock_events=stock_events,
        capital_information=capital_information,
        officers=officers,
    )
    return PlainTextResponse(report, media_type="text/markdown; charset=utf-8")

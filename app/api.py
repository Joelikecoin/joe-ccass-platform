from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app import __version__
from app.config import Settings, get_settings
from app.errors import ErrorCode, PlatformError
from app.models import (
    BigChangesResponse,
    CcassResponse,
    ChangesResponse,
    ConcentrationResponse,
)
from app.services.big_changes import BigChangesService, get_big_changes_service
from app.services.ccass import CcassService, get_ccass_service
from app.services.changes import ChangesService, get_changes_service
from app.services.concentration import ConcentrationService, get_concentration_service
from ccass_core.big_changes_report import build_big_changes_markdown_report
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
    "/api/v1/ccass/{code}/report",
    response_class=PlainTextResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["ccass"],
)
async def get_ccass_stock_report(
    code: str,
    holdings_limit: int = Query(default=20, ge=1, le=100),
    big_change_threshold: int = Query(default=1_000_000, ge=0),
    service: CcassService = Depends(get_ccass_service),
) -> PlainTextResponse:
    normalized = normalize_stock_code(code)
    response = await service.get_stock_data(normalized, holdings_limit=holdings_limit)
    analysis = compute_analysis(
        response,
        previous=None,
        big_change_threshold=big_change_threshold,
    )
    report = build_markdown_report(response, code=normalized, analysis=analysis)
    return PlainTextResponse(report, media_type="text/markdown; charset=utf-8")

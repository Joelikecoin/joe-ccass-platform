from typing import Annotated

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app import __version__
from app.config import Settings, get_settings
from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse
from app.services.ccass import CcassService, get_ccass_service
from ccass_core.compute import compute_analysis
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

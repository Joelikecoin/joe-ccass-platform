from functools import lru_cache
from typing import Protocol

from app.config import Settings, get_settings
from app.data_quality import structured_warning
from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse
from app.services.data_gateway import CcassDataGateway, GatewayRequest
from app.services.holdings_lkg import PersistentLatestHoldingsSource
from app.services.latest_holdings import finalize_latest_holdings
from ccass_core.source_trace import (
    SourceTraceView,
    build_source_trace_view,
    validate_ccass_date_convention,
)
from app.sources.google_drive_csv import GoogleDriveCsvSource
from app.sources.registry import (
    GOOGLE_DRIVE_CSV_SOURCE_ID,
    WEBBSITE_SOURCE_ID,
    SourceRegistry,
    build_source_registry,
)
from app.sources.webbsite import WebbsiteClient
from app.storage.history import NormalizedSnapshotRepository


class HoldingsSource(Protocol):
    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse: ...


class MirrorWithCsvFallback:
    def __init__(
        self,
        settings: Settings,
        registry: SourceRegistry | None = None,
        *,
        allow_process_lkg_on_error: bool = True,
    ) -> None:
        selection = (registry or build_source_registry(settings)).select_holdings_sources("auto")
        self.selection = selection
        self.primary_source = selection.primary
        self.fallback_sources = selection.fallback
        self.unavailable_sources = selection.unavailable
        source_ids = {source.source_id for source in selection.available}
        self.mirror = WebbsiteClient(settings) if WEBBSITE_SOURCE_ID in source_ids else None
        self.csv = None
        if GOOGLE_DRIVE_CSV_SOURCE_ID in source_ids:
            self.csv = GoogleDriveCsvSource(settings)
            if not allow_process_lkg_on_error:
                self.csv.allow_process_lkg_on_error = False

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        if self.mirror is None:
            if self.csv is None:
                raise RuntimeError("source registry selected no holdings source")
            return await self.csv.get_holdings(code, limit=limit)
        try:
            return await self.mirror.get_holdings(code, limit=limit)
        except PlatformError as mirror_error:
            if self.csv is None:
                raise
            error_code = getattr(mirror_error, "code", type(mirror_error).__name__)
            try:
                response = await self.csv.get_holdings(code, limit=limit)
            except PlatformError as csv_error:
                raise PlatformError(
                    csv_error.code,
                    f"Primary mirror failed ({error_code}); configured CSV fallback also failed "
                    f"({csv_error.code}).",
                    retry_recommended=(
                        mirror_error.retry_recommended or csv_error.retry_recommended
                    ),
                    retry_after_seconds=(
                        csv_error.retry_after_seconds or mirror_error.retry_after_seconds
                    ),
                    status_code=csv_error.status_code,
                ) from csv_error
            response.data_quality_warnings.append(
                structured_warning(
                    "SOURCE_STATUS",
                    "CSV_FALLBACK_USED",
                    f"Primary mirror failed ({error_code}); using the configured CSV snapshot fallback.",
                )
            )
            return response


class CcassService:
    def __init__(
        self,
        client: HoldingsSource | None = None,
        settings: Settings | None = None,
        lkg_repository: NormalizedSnapshotRepository | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        registry = build_source_registry(self.settings)
        selection = registry.select_holdings_sources(self.settings.data_source)
        selected = selection.available
        if client is not None:
            self.source = client
        else:
            if len(selected) > 1:
                self.source = MirrorWithCsvFallback(
                    self.settings,
                    registry,
                    allow_process_lkg_on_error=lkg_repository is None,
                )
            elif selected[0].source_id == GOOGLE_DRIVE_CSV_SOURCE_ID:
                self.source = GoogleDriveCsvSource(self.settings)
                if lkg_repository is not None:
                    self.source.allow_process_lkg_on_error = False
            else:
                self.source = WebbsiteClient(self.settings)
        if lkg_repository is not None:
            self.source = PersistentLatestHoldingsSource(
                self.source,
                repository=lkg_repository,
                definitions=selected,
            )
        self.client = self.source
        self.gateway = CcassDataGateway(source_backend=self.source)

    async def get_stock_data(self, code: str | int, holdings_limit: int = 15) -> CcassResponse:
        gateway_response = await self.get_stock_gateway_response(code, holdings_limit=holdings_limit)
        return gateway_response.normalized_response

    async def get_stock_gateway_response(
        self,
        code: str | int,
        holdings_limit: int = 15,
    ) -> "GatewayResponse":
        if holdings_limit < 1:
            raise PlatformError(
                ErrorCode.INVALID_SCHEMA,
                "holdings_limit must be at least 1.",
                status_code=400,
            )
        request = GatewayRequest(
            stock_code=code,
            holdings_limit=holdings_limit,
            request_surface="service",
        )
        gateway_response = await self.gateway.get_holdings(request)
        normalized = gateway_response.request.normalized_stock_code
        normalized_response = finalize_latest_holdings(
            gateway_response.normalized_response,
            requested_code=normalized,
            holdings_limit=holdings_limit,
        )
        gateway_response = gateway_response.model_copy(update={"normalized_response": normalized_response})
        source_trace_view = build_source_trace_view(gateway_response)
        validation = validate_ccass_date_convention(
            source_trace_view,
            data_as_of=normalized_response.metadata.data_as_of,
        )
        if validation.warnings:
            normalized_response = normalized_response.model_copy(
                update={
                    "data_quality_warnings": list(
                        dict.fromkeys(
                            [
                                *normalized_response.data_quality_warnings,
                                *validation.warnings,
                            ]
                        )
                    )
                }
            )
        if validation.notes:
            updated_notes = tuple(
                dict.fromkeys(
                    [
                        *gateway_response.source_trace.notes,
                        *validation.notes,
                    ]
                )
            )
            gateway_response = gateway_response.model_copy(
                update={
                    "source_trace": gateway_response.source_trace.model_copy(
                        update={"notes": updated_notes}
                    )
                }
            )
        return gateway_response.model_copy(update={"normalized_response": normalized_response})

    async def get_stock_source_trace(
        self,
        code: str | int,
        holdings_limit: int = 15,
    ) -> SourceTraceView:
        gateway_response = await self.get_stock_gateway_response(code, holdings_limit=holdings_limit)
        return build_source_trace_view(gateway_response)


@lru_cache
def get_ccass_service() -> CcassService:
    settings = get_settings()
    return CcassService(
        settings=settings,
        lkg_repository=NormalizedSnapshotRepository(settings.ccass_sqlite_path),
    )

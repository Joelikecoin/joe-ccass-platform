from functools import lru_cache
from typing import Protocol

from app.config import Settings, get_settings
from app.errors import PlatformError
from app.models import CcassResponse
from app.services.holdings_lkg import PersistentLatestHoldingsSource
from app.sources.google_drive_csv import GoogleDriveCsvSource
from app.sources.registry import (
    GOOGLE_DRIVE_CSV_SOURCE_ID,
    WEBBSITE_SOURCE_ID,
    SourceRegistry,
    build_source_registry,
)
from app.sources.webbsite import WebbsiteClient
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.normalize import normalize_stock_code


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
        selected = (registry or build_source_registry(settings)).select_holdings("auto")
        source_ids = {source.source_id for source in selected}
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
                f"Primary mirror failed ({error_code}); using the configured CSV snapshot fallback."
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
        selected = registry.select_holdings(self.settings.data_source)
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

    async def get_stock_data(self, code: str | int, holdings_limit: int = 15) -> CcassResponse:
        normalized = normalize_stock_code(code)
        return await self.source.get_holdings(normalized, limit=holdings_limit)


@lru_cache
def get_ccass_service() -> CcassService:
    settings = get_settings()
    return CcassService(
        settings=settings,
        lkg_repository=NormalizedSnapshotRepository(settings.ccass_sqlite_path),
    )

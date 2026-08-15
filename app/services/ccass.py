from datetime import UTC, datetime
from functools import lru_cache
from typing import Protocol

from app.config import Settings, get_settings
from app.data_quality import structured_warning
from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse
from app.services.data_gateway import (
    CcassDataGateway,
    GatewayRequest,
    GatewayRequestContext,
    GatewaySourceCandidate,
)
from app.services.latest_holdings import finalize_latest_holdings
from app.domain.history import HistoricalSnapshot
from app.services.holdings_lkg import (
    FreshnessStatus,
    LKG_AGE_SECONDS_PREFIX,
    SOURCE_ERROR_CODE_PREFIX,
    SOURCE_ERROR_MESSAGE_PREFIX,
    SOURCE_ERROR_RETRY_AFTER_SECONDS_PREFIX,
    SOURCE_ERROR_RETRY_RECOMMENDED_PREFIX,
)
from ccass_core.source_trace import (
    SourceTraceView,
    build_source_trace_view,
    validate_ccass_date_convention,
)
from app.sources.google_drive_csv import GoogleDriveCsvSource
from app.sources.registry import (
    HKEX_SDW_SOURCE_ID,
    GOOGLE_DRIVE_CSV_SOURCE_ID,
    WEBBSITE_SOURCE_ID,
    SourceDefinition,
    SourceRegistry,
    build_source_registry,
)
from app.sources.hkex_sdw import HKEXSdwClient
from app.sources.webbsite import WebbsiteClient
from app.storage.history import NormalizedSnapshotRepository


class HoldingsSource(Protocol):
    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse: ...


class _DeferredHoldingsSource:
    def __init__(self, factory) -> None:
        self._factory = factory
        self._backend: HoldingsSource | None = None

    def _resolve(self) -> HoldingsSource:
        if self._backend is None:
            self._backend = self._factory()
        return self._backend

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        return await self._resolve().get_holdings(code, limit=limit)


class RepositorySnapshotBackend:
    def __init__(
        self,
        repository: NormalizedSnapshotRepository,
        *,
        max_age_seconds: int,
        source_ids: tuple[str, ...] | None = None,
    ) -> None:
        self.repository = repository
        self.max_age_seconds = max_age_seconds
        self.source_ids = source_ids

    async def get(self, request: GatewayRequestContext) -> CcassResponse | None:
        snapshot = self._latest_snapshot(request.normalized_stock_code)
        if snapshot is None or not self._is_valid_snapshot(snapshot, request.requested_at):
            return None
        response = snapshot.to_response()
        response.metadata.cached = True
        return response

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        snapshot = self._latest_snapshot(code)
        if snapshot is None or not self._is_valid_snapshot(snapshot):
            raise PlatformError(
                ErrorCode.SOURCE_UNAVAILABLE,
                "Persistent normalized snapshot recovery is unavailable.",
                retry_recommended=True,
                retry_after_seconds=30,
                status_code=503,
            )
        response = snapshot.to_response()
        response.metadata.cached = True
        return response

    def _latest_snapshot(self, code: str) -> HistoricalSnapshot | None:
        if self.source_ids:
            candidates = [
                snapshot
                for source_id in self.source_ids
                if (snapshot := self.repository.latest(code, source_id=source_id, include_partial=False))
                is not None
            ]
            if not candidates:
                return None
            return max(candidates, key=lambda snapshot: snapshot.fetched_at)
        return self.repository.latest(code, include_partial=False)

    def _is_valid_snapshot(
        self,
        snapshot: HistoricalSnapshot,
        requested_at=None,
    ) -> bool:
        if snapshot.partial or snapshot.stale:
            return False
        fetched_at = snapshot.fetched_at
        if fetched_at.tzinfo is None or fetched_at.utcoffset() is None:
            return False
        if requested_at is None:
            from datetime import UTC, datetime

            requested_at = datetime.now(UTC)
        if requested_at.tzinfo is None or requested_at.utcoffset() is None:
            return False
        age_seconds = int((requested_at - fetched_at).total_seconds())
        return 0 <= age_seconds <= self.max_age_seconds


class _RecordingGatewayBackend:
    def __init__(self, backend: HoldingsSource) -> None:
        self.backend = backend
        self.last_error: PlatformError | None = None

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        try:
            return await self.backend.get_holdings(code, limit=limit)
        except PlatformError as error:
            self.last_error = error
            raise


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

    def _build_gateway_sources(
        self,
    ) -> tuple[
        tuple[GatewaySourceCandidate, ...],
        _RecordingGatewayBackend | None,
        _RecordingGatewayBackend | None,
    ]:
        candidates: list[GatewaySourceCandidate] = []
        mirror_backend: _RecordingGatewayBackend | None = None
        csv_backend: _RecordingGatewayBackend | None = None
        if self.mirror is not None:
            mirror_backend = _RecordingGatewayBackend(self.mirror)
            candidates.append(
                GatewaySourceCandidate(
                    source_id=WEBBSITE_SOURCE_ID,
                    source_name=self.primary_source.display_name if self.primary_source else None,
                    priority=0,
                    status="active",
                    backend=mirror_backend,
                    fallback_eligible=True,
                )
            )
        if self.csv is not None:
            csv_backend = _RecordingGatewayBackend(self.csv)
            candidates.append(
                GatewaySourceCandidate(
                    source_id=GOOGLE_DRIVE_CSV_SOURCE_ID,
                    source_name="Google Drive CSV",
                    priority=1,
                    status="fallback",
                    backend=csv_backend,
                    fallback_eligible=True,
                )
            )
        return tuple(candidates), mirror_backend, csv_backend

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        source_candidates, mirror_backend, csv_backend = self._build_gateway_sources()
        if not source_candidates:
            raise RuntimeError("source registry selected no holdings source")
        gateway = CcassDataGateway(source_candidates=source_candidates)
        request = GatewayRequest(
            stock_code=code,
            holdings_limit=limit,
            request_surface="service",
        )
        try:
            gateway_response = await gateway.get_holdings(request)
        except PlatformError as error:
            if mirror_backend is not None and csv_backend is not None:
                mirror_error = mirror_backend.last_error
                csv_error = csv_backend.last_error
                if mirror_error is not None and csv_error is not None:
                    raise PlatformError(
                        csv_error.code,
                        f"Primary mirror failed ({mirror_error.code}); configured CSV fallback also "
                        f"failed ({csv_error.code}).",
                        retry_recommended=(
                            mirror_error.retry_recommended or csv_error.retry_recommended
                        ),
                        retry_after_seconds=(
                            csv_error.retry_after_seconds or mirror_error.retry_after_seconds
                        ),
                        status_code=csv_error.status_code,
                    ) from csv_error
            raise
        response = gateway_response.normalized_response
        if (
            gateway_response.routing.selected_source_id == GOOGLE_DRIVE_CSV_SOURCE_ID
            and mirror_backend is not None
        ):
            mirror_error = mirror_backend.last_error
            mirror_error_code = (
                mirror_error.code if mirror_error is not None else ErrorCode.SOURCE_UNAVAILABLE
            )
            response = response.model_copy(
                update={
                    "data_quality_warnings": [
                        *response.data_quality_warnings,
                        structured_warning(
                            "SOURCE_STATUS",
                            "CSV_FALLBACK_USED",
                            f"Primary mirror failed ({mirror_error_code}); using the configured CSV "
                            "snapshot fallback.",
                        ),
                    ]
                }
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
        self.registry = build_source_registry(self.settings)
        self.selection = self.registry.select_holdings_sources(self.settings.data_source)
        self.available_sources = self.selection.available
        self.source_definitions_by_id = {
            definition.source_id: definition for definition in self.available_sources
        }
        self.lkg_repository = lkg_repository
        if client is not None:
            self.source = client
            self.client = self.source
            self.gateway = CcassDataGateway(source_backend=self.source)
            return

        live_definition = self.selection.primary
        if live_definition is None:
            raise PlatformError(
                ErrorCode.SOURCE_DISABLED,
                "No enabled CCASS source is available for routing.",
                status_code=503,
            )
        self.source = self._build_live_source(live_definition)
        cache_backend = self._build_cache_backend()
        source_candidates = self._build_source_candidates(live_definition)
        if cache_backend is None and len(source_candidates) == 1:
            self.gateway = CcassDataGateway(source_backend=self.source)
        else:
            self.gateway = CcassDataGateway(
                source_candidates=source_candidates,
                cache_backend=cache_backend,
            )
        self.client = self.source

    def _build_live_source(self, definition: SourceDefinition) -> HoldingsSource:
        if definition.source_id == GOOGLE_DRIVE_CSV_SOURCE_ID:
            return GoogleDriveCsvSource(self.settings)
        if definition.source_id == HKEX_SDW_SOURCE_ID:
            return HKEXSdwClient(self.settings)
        return WebbsiteClient(self.settings)

    def _build_cache_backend(self) -> RepositorySnapshotBackend | None:
        if self.lkg_repository is None:
            return None
        return RepositorySnapshotBackend(
            self.lkg_repository,
            max_age_seconds=self.settings.cache_ttl_seconds,
            source_ids=tuple(source.source_id for source in self.available_sources),
        )

    def _build_recovery_backend(
        self,
        source_id: str,
    ) -> RepositorySnapshotBackend | None:
        if self.lkg_repository is None:
            return None
        return RepositorySnapshotBackend(
            self.lkg_repository,
            max_age_seconds=self.settings.holdings_lkg_max_age_seconds,
            source_ids=(source_id,),
        )

    def _build_source_candidates(
        self,
        live_definition: SourceDefinition,
    ) -> tuple[GatewaySourceCandidate, ...]:
        candidates: list[GatewaySourceCandidate] = [
            GatewaySourceCandidate(
                source_id=live_definition.source_id,
                source_name=live_definition.display_name,
                priority=0,
                status="active",
                backend=self.source,
                fallback_eligible=True,
            )
        ]
        if (
            self.settings.data_source == "auto"
            and live_definition.source_id == WEBBSITE_SOURCE_ID
            and any(source.source_id == HKEX_SDW_SOURCE_ID for source in self.available_sources)
        ):
            candidates.append(
                GatewaySourceCandidate(
                    source_id=HKEX_SDW_SOURCE_ID,
                    source_name="HKEX SDW",
                    priority=1,
                    status="active",
                    backend=_DeferredHoldingsSource(lambda: HKEXSdwClient(self.settings)),
                    fallback_eligible=False,
                )
            )
        recovery_backend = self._build_recovery_backend(live_definition.source_id)
        if recovery_backend is not None:
            candidates.append(
                GatewaySourceCandidate(
                    source_id="persistent_lkg",
                    source_name="Persistent LKG",
                    priority=2,
                    status="fallback",
                    backend=recovery_backend,
                    fallback_eligible=True,
                )
            )
        if live_definition.source_id != GOOGLE_DRIVE_CSV_SOURCE_ID and any(
            source.source_id == GOOGLE_DRIVE_CSV_SOURCE_ID for source in self.available_sources
        ):
            candidates.append(
                GatewaySourceCandidate(
                    source_id=GOOGLE_DRIVE_CSV_SOURCE_ID,
                    source_name="Google Drive CSV",
                    priority=3,
                    status="fallback",
                    backend=GoogleDriveCsvSource(self.settings),
                    fallback_eligible=True,
                )
            )
        return tuple(candidates)

    async def get_stock_data(
        self,
        code: str | int,
        holdings_limit: int = 15,
        *,
        cache_first: bool = True,
    ) -> CcassResponse:
        gateway_response = await self.get_stock_gateway_response(
            code,
            holdings_limit=holdings_limit,
            cache_first=cache_first,
        )
        return gateway_response.normalized_response

    async def get_stock_gateway_response(
        self,
        code: str | int,
        holdings_limit: int = 15,
        *,
        cache_first: bool = True,
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
            cache_first=cache_first,
        )
        gateway_response = await self.gateway.get_holdings(request)
        persistence_warning = self._persist_gateway_response(gateway_response)
        if persistence_warning is not None:
            gateway_response = gateway_response.model_copy(
                update={
                    "normalized_response": gateway_response.normalized_response.model_copy(
                        update={
                            "data_quality_warnings": [
                                *gateway_response.normalized_response.data_quality_warnings,
                                persistence_warning,
                            ]
                        }
                    )
                }
            )
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
        gateway_response = gateway_response.model_copy(update={"normalized_response": normalized_response})
        normalized_response = self._apply_recovery_metadata(gateway_response)
        return gateway_response.model_copy(update={"normalized_response": normalized_response})

    def _persist_gateway_response(self, gateway_response: "GatewayResponse") -> str | None:
        if self.lkg_repository is None:
            return None
        source_id = gateway_response.routing.selected_source_id
        if source_id in {None, "cache", "persistent_lkg"}:
            return None
        definition = self.source_definitions_by_id.get(source_id)
        if definition is None:
            return None
        try:
            snapshot = HistoricalSnapshot.from_response(
                gateway_response.normalized_response,
                source_id=definition.source_id,
                parser_version=definition.parser_version,
            )
            self.lkg_repository.save(snapshot)
        except Exception as error:
            return structured_warning(
                "LKG_PERSISTENCE_ERROR",
                type(error).__name__,
                "Verified live data was served, but the transactional LKG write failed.",
            )
        return None

    def _apply_recovery_metadata(self, gateway_response: "GatewayResponse") -> CcassResponse:
        response = gateway_response.normalized_response
        routing = gateway_response.routing
        if routing.selected_source_id != "persistent_lkg":
            return response
        fetched_at = response.metadata.fetched_at
        age_seconds = 0
        if fetched_at.tzinfo is not None and fetched_at.utcoffset() is not None:
            age_seconds = max(0, int((datetime.now(UTC) - fetched_at).total_seconds()))
        warnings = list(response.data_quality_warnings)
        warnings.extend(
            (
                structured_warning(
                    "FRESHNESS_STATUS",
                    FreshnessStatus.STALE_LKG.value,
                    "The current result came from a cached or snapshot data source.",
                ),
                structured_warning(
                    SOURCE_ERROR_CODE_PREFIX[:-1],
                    routing.last_error_code or ErrorCode.SOURCE_UNAVAILABLE.value,
                    f"Source error code: {routing.last_error_code or ErrorCode.SOURCE_UNAVAILABLE.value}",
                ),
                structured_warning(
                    SOURCE_ERROR_MESSAGE_PREFIX[:-1],
                    routing.last_error_message or "Persistent LKG recovery was used.",
                    "Source error message: "
                    f"{routing.last_error_message or 'Persistent LKG recovery was used.'}",
                ),
                structured_warning(
                    SOURCE_ERROR_RETRY_RECOMMENDED_PREFIX[:-1],
                    str(
                        routing.last_error_retry_recommended
                        if routing.last_error_retry_recommended is not None
                        else True
                    ).lower(),
                    "Source retry recommended: "
                    f"{str(routing.last_error_retry_recommended if routing.last_error_retry_recommended is not None else True).lower()}",
                ),
                structured_warning(
                    SOURCE_ERROR_RETRY_AFTER_SECONDS_PREFIX[:-1],
                    (
                        routing.last_error_retry_after_seconds
                        if routing.last_error_retry_after_seconds is not None
                        else "none"
                    ),
                    "Source retry-after seconds: "
                    f"{routing.last_error_retry_after_seconds if routing.last_error_retry_after_seconds is not None else 'none'}",
                ),
                structured_warning(
                    LKG_AGE_SECONDS_PREFIX[:-1],
                    str(age_seconds),
                    f"Last-known-good age seconds: {age_seconds}",
                ),
            )
        )
        return response.model_copy(update={"data_quality_warnings": list(dict.fromkeys(warnings))})

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

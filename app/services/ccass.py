import asyncio
from datetime import UTC, date, datetime
from functools import lru_cache
from typing import Any, Protocol

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
from app.services.announcements import get_announcements_service
from app.services.capital_information import get_capital_information_service
from app.services.officers import get_officers_service
from app.services.price_history import get_price_history_service
from app.services.stock_events import get_stock_events_service
from app.services.concentration import get_concentration_service
from app.services.changes import get_changes_service
from app.services.big_changes import get_big_changes_service
from app.services.holdings_lkg import (
    FreshnessStatus,
    FRESHNESS_PREFIX,
    LKG_AGE_SECONDS_PREFIX,
    LKG_RETRIEVED_AT_PREFIX,
    SOURCE_ERROR_CODE_PREFIX,
    SOURCE_ERROR_MESSAGE_PREFIX,
    SOURCE_ERROR_RETRY_AFTER_SECONDS_PREFIX,
    SOURCE_ERROR_RETRY_RECOMMENDED_PREFIX,
    SERVED_AT_PREFIX,
    build_stale_lkg_warnings,
)
from app.services.request_context import REQUESTED_CCASS_SNAPSHOT_DATE
from ccass_core.source_trace import (
    SourceTraceView,
    build_source_trace_view,
    build_source_trace_markdown,
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
        snapshot = self._latest_snapshot(request.normalized_stock_code, requested_date=request.requested_date)
        if snapshot is None or not self._is_valid_snapshot(snapshot, request.requested_at):
            return None
        response = snapshot.to_response()
        response.metadata.cached = True
        return response

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        snapshot = self._latest_snapshot(
            code,
            requested_date=REQUESTED_CCASS_SNAPSHOT_DATE.get(),
        )
        if snapshot is None or not self._is_recoverable_snapshot(snapshot):
            raise PlatformError(
                ErrorCode.SOURCE_UNAVAILABLE,
                "Persistent normalized snapshot recovery is unavailable.",
                retry_recommended=True,
                retry_after_seconds=30,
                status_code=503,
            )
        response = snapshot.to_response()
        response.metadata.cached = True
        response = response.model_copy(
            update={
                "data_quality_warnings": [
                    *_without_freshness(response.data_quality_warnings),
                    *build_stale_lkg_warnings(
                        retrieved_at=snapshot.fetched_at,
                        served_at=datetime.now(UTC),
                    ),
                ]
            }
        )
        return response

    def _latest_snapshot(
        self,
        code: str,
        *,
        requested_date: date | None = None,
    ) -> HistoricalSnapshot | None:
        if requested_date is not None:
            if self.source_ids:
                candidates = [
                    snapshot
                    for source_id in self.source_ids
                    if (snapshot := self.repository.snapshot_on(
                        code,
                        requested_date,
                        source_id=source_id,
                    ))
                    is not None
                ]
                if not candidates:
                    return None
                return max(candidates, key=lambda snapshot: snapshot.fetched_at)
            snapshots = self.repository.date_range(
                code,
                date_from=requested_date,
                date_to=requested_date,
                include_partial=True,
            )
            if not snapshots:
                return None
            return max(snapshots, key=lambda snapshot: snapshot.fetched_at)
        if self.source_ids:
            candidates = [
                snapshot
                for source_id in self.source_ids
                if (snapshot := self.repository.latest(code, source_id=source_id, include_partial=True))
                is not None
            ]
            if not candidates:
                return None
            return max(candidates, key=lambda snapshot: snapshot.fetched_at)
        return self.repository.latest(code, include_partial=True)

    def _is_valid_snapshot(
        self,
        snapshot: HistoricalSnapshot,
        requested_at=None,
    ) -> bool:
        if snapshot.stale:
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

    def _is_recoverable_snapshot(self, snapshot: HistoricalSnapshot) -> bool:
        if snapshot.stale:
            return False
        fetched_at = snapshot.fetched_at
        if fetched_at.tzinfo is None or fetched_at.utcoffset() is None:
            return False
        now = datetime.now(UTC)
        if now.tzinfo is None or now.utcoffset() is None:
            return False
        return int((now - fetched_at).total_seconds()) >= 0


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


def _without_freshness(warnings) -> list[str]:
    prefixes = (
        FRESHNESS_PREFIX,
        SOURCE_ERROR_CODE_PREFIX,
        SOURCE_ERROR_MESSAGE_PREFIX,
        SOURCE_ERROR_RETRY_RECOMMENDED_PREFIX,
        SOURCE_ERROR_RETRY_AFTER_SECONDS_PREFIX,
        LKG_AGE_SECONDS_PREFIX,
        LKG_RETRIEVED_AT_PREFIX,
        SERVED_AT_PREFIX,
    )
    return [warning for warning in warnings if not warning.startswith(prefixes)]


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

        live_definition = (
            self.source_definitions_by_id.get(WEBBSITE_SOURCE_ID)
            if self.settings.data_source == "auto"
            else self.selection.primary
        )
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
        source_ids: tuple[str, ...] | None = None,
    ) -> RepositorySnapshotBackend | None:
        if self.lkg_repository is None:
            return None
        if source_ids is not None and not source_ids:
            return None
        return RepositorySnapshotBackend(
            self.lkg_repository,
            max_age_seconds=self.settings.holdings_lkg_max_age_seconds,
            source_ids=source_ids,
        )

    def _build_source_candidates(
        self,
        live_definition: SourceDefinition,
    ) -> tuple[GatewaySourceCandidate, ...]:
        if self.settings.data_source == "auto":
            candidates: list[GatewaySourceCandidate] = []
            if any(source.source_id == WEBBSITE_SOURCE_ID for source in self.available_sources):
                candidates.append(
                    GatewaySourceCandidate(
                        source_id=WEBBSITE_SOURCE_ID,
                        source_name=self.source_definitions_by_id[WEBBSITE_SOURCE_ID].display_name,
                        priority=0,
                        status="active",
                        backend=_DeferredHoldingsSource(lambda: WebbsiteClient(self.settings)),
                        fallback_eligible=True,
                    )
                )
            recovery_source_ids = tuple(
                source.source_id
                for source in self.available_sources
                if source.source_id != GOOGLE_DRIVE_CSV_SOURCE_ID
            )
            recovery_backend = self._build_recovery_backend(recovery_source_ids)
            if recovery_backend is not None:
                candidates.append(
                    GatewaySourceCandidate(
                        source_id="persistent_lkg",
                        source_name="Persistent LKG",
                        priority=1,
                        status="fallback",
                        backend=recovery_backend,
                        fallback_eligible=True,
                    )
                )
            return tuple(candidates)
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
                    fallback_eligible=True,
                )
            )
        recovery_source_ids = tuple(
            source.source_id
            for source in self.available_sources
            if source.source_id != GOOGLE_DRIVE_CSV_SOURCE_ID
        )
        recovery_backend = self._build_recovery_backend(recovery_source_ids)
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
        requested_date: date | None = None,
    ) -> CcassResponse:
        gateway_response = await self.get_stock_gateway_response(
            code,
            holdings_limit=holdings_limit,
            cache_first=cache_first,
            requested_date=requested_date,
        )
        return gateway_response.normalized_response

    async def get_stock_gateway_response(
        self,
        code: str | int,
        holdings_limit: int = 15,
        *,
        cache_first: bool = True,
        requested_date: date | None = None,
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
            requested_date=requested_date,
        )
        token = REQUESTED_CCASS_SNAPSHOT_DATE.set(requested_date)
        try:
            gateway_response = await self.gateway.get_holdings(request)
        finally:
            REQUESTED_CCASS_SNAPSHOT_DATE.reset(token)
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
        normalized_response = await self._attach_related_surfaces(
            normalized_response,
            normalized_stock_code=normalized,
            holdings_limit=holdings_limit,
            source_trace_view=source_trace_view,
        )
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

    async def _attach_related_surfaces(
        self,
        response: CcassResponse,
        *,
        normalized_stock_code: str,
        holdings_limit: int,
        source_trace_view: SourceTraceView | None,
    ) -> CcassResponse:
        warnings = list(response.data_quality_warnings)
        errors = list(response.errors)
        previous_response = self._previous_response(response)

        changes = response.changes
        big_changes = response.big_changes
        if previous_response is not None and response.metadata.data_as_of is not None:
            compare_date = (
                previous_response.metadata.data_as_of
                or previous_response.metadata.holdings_date
            )
            if compare_date is None:
                previous_response = None
            else:
                try:
                    changes = get_changes_service().get_changes(
                        normalized_stock_code,
                        snapshot_date=response.metadata.data_as_of,
                        compare_date=compare_date,
                    )
                    if changes.data_quality_warnings:
                        warnings.extend(changes.data_quality_warnings)
                except Exception as exc:
                    errors.append(f"changes: {type(exc).__name__}")
                    warnings.append(
                        structured_warning(
                            "DATA_LIMITATION",
                            "CHANGES_UNAVAILABLE",
                            f"Changes are unavailable ({type(exc).__name__}).",
                        )
                    )
                try:
                    big_changes = get_big_changes_service().get_big_changes(
                        normalized_stock_code,
                        snapshot_date=response.metadata.data_as_of,
                        compare_date=compare_date,
                        threshold_shares=self.settings.big_changes_threshold_shares,
                    )
                    if big_changes.data_quality_warnings:
                        warnings.extend(big_changes.data_quality_warnings)
                except Exception as exc:
                    errors.append(f"big_changes: {type(exc).__name__}")
                    warnings.append(
                        structured_warning(
                            "DATA_LIMITATION",
                            "BIG_CHANGES_UNAVAILABLE",
                            f"Big changes are unavailable ({type(exc).__name__}).",
                        )
                    )
        concentration = response.concentration
        if response.metadata.data_as_of is not None:
            try:
                concentration = get_concentration_service().get_concentration(
                    normalized_stock_code,
                    snapshot_date=response.metadata.data_as_of,
                    top_holders_limit=max(1, min(holdings_limit, 100)),
                )
                if concentration.data_quality_warnings:
                    warnings.extend(concentration.data_quality_warnings)
            except Exception as exc:
                errors.append(f"concentration: {type(exc).__name__}")
                warnings.append(
                    structured_warning(
                        "DATA_LIMITATION",
                        "CONCENTRATION_UNAVAILABLE",
                        f"Concentration is unavailable ({type(exc).__name__}).",
                    )
                )
        fetch_jobs: list[tuple[str, Any]] = []
        if response.announcements is None:
            fetch_jobs.append(("announcements", get_announcements_service().get_announcements(normalized_stock_code)))
        if response.stock_events is None:
            fetch_jobs.append(("stock_events", get_stock_events_service().get_stock_events(normalized_stock_code)))
        if response.capital_information is None:
            fetch_jobs.append((
                "capital_information",
                get_capital_information_service().get_capital_information(normalized_stock_code),
            ))
        if response.officers is None:
            fetch_jobs.append(("officers", get_officers_service().get_officers(normalized_stock_code)))
        if response.price_history is None:
            fetch_jobs.append(("price_history", get_price_history_service().get_price_history(normalized_stock_code)))

        fetched: dict[str, Any] = {}
        if fetch_jobs:
            results = await asyncio.gather(*(job for _, job in fetch_jobs), return_exceptions=True)
            fetched = {label: result for (label, _), result in zip(fetch_jobs, results)}

        def _surface_or_current(label: str) -> Any | None:
            current_value = getattr(response, label)
            incoming = fetched.get(label, current_value)
            if isinstance(incoming, Exception):
                errors.append(f"{label}: {type(incoming).__name__}")
                warnings.append(
                    structured_warning(
                        "DATA_LIMITATION",
                        f"{label.upper()}_UNAVAILABLE",
                        f"{label.replace('_', ' ').title()} are unavailable ({type(incoming).__name__}).",
                    )
                )
                return current_value
            if incoming is current_value:
                return current_value
            if incoming is None:
                return current_value
            candidate_rows = getattr(incoming, "prices", None)
            if candidate_rows is None:
                candidate_rows = getattr(incoming, label, ())
            if candidate_rows:
                warnings.extend(getattr(incoming, "data_quality_warnings", ()))
                return incoming
            warnings.extend(getattr(incoming, "data_quality_warnings", ()))
            return current_value

        announcements = _surface_or_current("announcements")
        stock_events = _surface_or_current("stock_events")
        capital_information = _surface_or_current("capital_information")
        officers = _surface_or_current("officers")
        price_history = _surface_or_current("price_history")

        fetch_summary = response.fetch_summary
        if source_trace_view is not None:
            fetch_summary = build_source_trace_markdown(source_trace_view)

        current = response.model_copy(
            update={
                "data_quality_warnings": list(dict.fromkeys(warnings)),
                "errors": list(dict.fromkeys(errors)),
                "fetch_summary": fetch_summary,
                "changes": changes,
                "big_changes": big_changes,
                "concentration": concentration,
                "price_history": price_history,
                "announcements": announcements,
                "stock_events": stock_events,
                "capital_information": capital_information,
                "officers": officers,
            }
        )
        return current

    def _previous_response(self, response: CcassResponse) -> CcassResponse | None:
        if self.lkg_repository is None:
            return None
        data_as_of = response.metadata.data_as_of
        if data_as_of is None:
            return None
        previous_snapshot = self.lkg_repository.previous(
            response.metadata.code,
            before_date=data_as_of,
            include_partial=False,
        )
        return previous_snapshot.to_response() if previous_snapshot is not None else None

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

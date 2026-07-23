"""Persistent last-known-good handling for latest Holdings responses."""

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from enum import StrEnum

from app.domain.history import HistoricalSnapshot
from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse
from app.services.latest_holdings import (
    finalize_latest_holdings,
    latest_holdings_is_complete,
)
from app.sources.registry import SourceDefinition
from app.storage.history import NormalizedSnapshotRepository

FRESHNESS_PREFIX = "FRESHNESS_STATUS:"
SOURCE_ERROR_CODE_PREFIX = "SOURCE_ERROR_CODE:"
SOURCE_ERROR_MESSAGE_PREFIX = "SOURCE_ERROR_MESSAGE:"
SOURCE_ERROR_RETRY_RECOMMENDED_PREFIX = "SOURCE_ERROR_RETRY_RECOMMENDED:"
SOURCE_ERROR_RETRY_AFTER_SECONDS_PREFIX = "SOURCE_ERROR_RETRY_AFTER_SECONDS:"
LKG_RETRIEVED_AT_PREFIX = "LKG_RETRIEVED_AT:"
LKG_AGE_SECONDS_PREFIX = "LKG_AGE_SECONDS:"
SERVED_AT_PREFIX = "SERVED_AT:"

_TRANSIENT_LKG_ERRORS = frozenset(
    {
        ErrorCode.SOURCE_FORBIDDEN,
        ErrorCode.SOURCE_RATE_LIMITED,
        ErrorCode.SOURCE_TIMEOUT,
        ErrorCode.SOURCE_UNAVAILABLE,
    }
)


class FreshnessStatus(StrEnum):
    FRESH = "FRESH"
    STALE_LKG = "STALE_LKG"
    UNAVAILABLE = "UNAVAILABLE"


class PersistentLatestHoldingsSource:
    """Wrap a latest-only source with normalized persistent LKG semantics."""

    def __init__(
        self,
        source,
        *,
        repository: NormalizedSnapshotRepository,
        definitions: Sequence[SourceDefinition],
        clock: Callable[[], datetime] | None = None,
        collection_limit: int = 10_000,
    ) -> None:
        self.source = source
        self.repository = repository
        self.definitions = tuple(definitions)
        self.clock = clock or (lambda: datetime.now(UTC))
        self.collection_limit = collection_limit

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        served_at = _aware_utc(self.clock(), field="served_at")
        try:
            response = await self.source.get_holdings(code, limit=self.collection_limit)
            response = finalize_latest_holdings(response, requested_code=code)
            definition = self._definition_for_response(response)
            snapshot = self._validated_live_snapshot(
                response,
                requested_code=code,
                definition=definition,
            )
        except PlatformError as error:
            return self._fallback(code, limit=limit, served_at=served_at, error=error)
        except ValueError as error:
            raise PlatformError(
                ErrorCode.SOURCE_CHANGED,
                f"{FreshnessStatus.UNAVAILABLE.value}: latest Holdings validation failed.",
                status_code=502,
            ) from error

        persistence_warning = None
        if not snapshot.partial:
            try:
                self.repository.save(snapshot)
            except Exception as error:
                persistence_warning = (
                    "LKG_PERSISTENCE_ERROR: verified live data was served, but the "
                    f"transactional LKG write failed ({type(error).__name__})."
                )

        result = response.model_copy(deep=True)
        result.holdings = result.holdings[: max(1, limit)]
        result.data_quality_warnings = _without_freshness(result.data_quality_warnings)
        result.data_quality_warnings.extend(
            (
                f"{FRESHNESS_PREFIX} {FreshnessStatus.FRESH.value}",
                f"{SERVED_AT_PREFIX} {served_at.isoformat()}",
            )
        )
        if persistence_warning:
            result.data_quality_warnings.append(persistence_warning)
        return result

    def _validated_live_snapshot(
        self,
        response: CcassResponse,
        *,
        requested_code: str,
        definition: SourceDefinition,
    ) -> HistoricalSnapshot:
        if response.metadata.code != requested_code:
            raise PlatformError(
                ErrorCode.SOURCE_CHANGED,
                f"{FreshnessStatus.UNAVAILABLE.value}: source returned another stock identity.",
                status_code=502,
            )
        _aware_utc(response.metadata.fetched_at, field="fetched_at")
        try:
            return HistoricalSnapshot.from_response(
                response,
                source_id=definition.source_id,
                parser_version=definition.parser_version,
                partial=not latest_holdings_is_complete(response),
            )
        except ValueError as error:
            raise PlatformError(
                ErrorCode.SOURCE_CHANGED,
                f"{FreshnessStatus.UNAVAILABLE.value}: source data failed schema or identity "
                "validation.",
                status_code=502,
            ) from error

    def _definition_for_response(self, response: CcassResponse) -> SourceDefinition:
        matches = tuple(
            definition
            for definition in self.definitions
            if definition.display_name == response.metadata.source_name
        )
        if len(matches) != 1:
            raise PlatformError(
                ErrorCode.SOURCE_CHANGED,
                f"{FreshnessStatus.UNAVAILABLE.value}: response source identity is not registered.",
                status_code=502,
            )
        return matches[0]

    def _fallback(
        self,
        code: str,
        *,
        limit: int,
        served_at: datetime,
        error: PlatformError,
    ) -> CcassResponse:
        if error.code not in _TRANSIENT_LKG_ERRORS:
            raise _unavailable(error)

        candidates: list[tuple[HistoricalSnapshot, SourceDefinition]] = []
        for definition in self.definitions:
            snapshot = self.repository.latest(
                code,
                source_id=definition.source_id,
                include_partial=False,
            )
            if snapshot is not None:
                candidates.append((snapshot, definition))
        if not candidates:
            raise _unavailable(error)

        aware_candidates: list[tuple[HistoricalSnapshot, SourceDefinition, datetime]] = []
        for candidate, candidate_definition in candidates:
            try:
                candidate_retrieved_at = _aware_utc(
                    candidate.fetched_at,
                    field="LKG fetched_at",
                )
            except ValueError as validation_error:
                raise _integrity_unavailable(
                    "stored LKG has an invalid retrieval timestamp"
                ) from validation_error
            aware_candidates.append(
                (candidate, candidate_definition, candidate_retrieved_at)
            )
        snapshot, definition, retrieved_at = max(
            aware_candidates,
            key=lambda item: item[2],
        )
        age_seconds = int((served_at - retrieved_at).total_seconds())
        if age_seconds < 0:
            raise _integrity_unavailable("stored LKG retrieval timestamp is in the future")
        if (
            snapshot.stock.code != code
            or snapshot.partial
            or snapshot.stale
            or snapshot.schema_version != 1
            or snapshot.parser_version != definition.parser_version
            or snapshot.source.source_id != definition.source_id
        ):
            raise _integrity_unavailable("stored LKG failed identity or schema validation")
        if age_seconds > definition.policy.lkg_max_age_seconds:
            raise PlatformError(
                ErrorCode.DATA_STALE,
                f"{FreshnessStatus.UNAVAILABLE.value}: stored LKG exceeds the configured "
                "freshness limit.",
                retry_recommended=error.retry_recommended,
                retry_after_seconds=error.retry_after_seconds,
                status_code=503,
            ) from error

        result = snapshot.to_response()
        result.metadata.cached = True
        result.holdings = result.holdings[: max(1, limit)]
        result.data_quality_warnings = _without_freshness(result.data_quality_warnings)
        result.data_quality_warnings.extend(
            (
                f"{FRESHNESS_PREFIX} {FreshnessStatus.STALE_LKG.value}",
                f"{SOURCE_ERROR_CODE_PREFIX} {error.code.value}",
                f"{SOURCE_ERROR_MESSAGE_PREFIX} {error.message}",
                f"{SOURCE_ERROR_RETRY_RECOMMENDED_PREFIX} "
                f"{str(error.retry_recommended).lower()}",
                f"{SOURCE_ERROR_RETRY_AFTER_SECONDS_PREFIX} "
                f"{error.retry_after_seconds if error.retry_after_seconds is not None else 'none'}",
                f"{LKG_RETRIEVED_AT_PREFIX} {retrieved_at.isoformat()}",
                f"{LKG_AGE_SECONDS_PREFIX} {age_seconds}",
                f"{SERVED_AT_PREFIX} {served_at.isoformat()}",
            )
        )
        return result


def freshness_status(response: CcassResponse) -> FreshnessStatus:
    for warning in response.data_quality_warnings:
        if warning.startswith(FRESHNESS_PREFIX):
            value = warning.removeprefix(FRESHNESS_PREFIX).strip()
            try:
                return FreshnessStatus(value)
            except ValueError:
                break
    return FreshnessStatus.FRESH


def freshness_detail(response: CcassResponse, prefix: str) -> str | None:
    for warning in response.data_quality_warnings:
        if warning.startswith(prefix):
            return warning.removeprefix(prefix).strip()
    return None


def _unavailable(error: PlatformError) -> PlatformError:
    return PlatformError(
        error.code,
        f"{FreshnessStatus.UNAVAILABLE.value}: {error.message}",
        retry_recommended=error.retry_recommended,
        retry_after_seconds=error.retry_after_seconds,
        status_code=error.status_code,
    )


def _integrity_unavailable(reason: str) -> PlatformError:
    return PlatformError(
        ErrorCode.SOURCE_CHANGED,
        f"{FreshnessStatus.UNAVAILABLE.value}: {reason}.",
        status_code=502,
    )


def _aware_utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _without_freshness(warnings: Sequence[str]) -> list[str]:
    prefixes = (
        FRESHNESS_PREFIX,
        SOURCE_ERROR_CODE_PREFIX,
        SOURCE_ERROR_MESSAGE_PREFIX,
        SOURCE_ERROR_RETRY_RECOMMENDED_PREFIX,
        SOURCE_ERROR_RETRY_AFTER_SECONDS_PREFIX,
        LKG_RETRIEVED_AT_PREFIX,
        LKG_AGE_SECONDS_PREFIX,
        SERVED_AT_PREFIX,
    )
    return [warning for warning in warnings if not warning.startswith(prefixes)]

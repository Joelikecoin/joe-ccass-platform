from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, Literal, Protocol, cast
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse
from ccass_core.normalize import normalize_stock_code
from ccass_core.source_trace import CCASS_DATE_CONVENTION_REFERENCE, CCASS_SOURCE_DATE_TYPE

GatewayRoute = Literal["cache", "existing_service"]
GatewaySourceStatus = Literal[
    "active",
    "fallback",
    "disabled",
    "unverified",
    "unavailable",
    "cached",
    "unknown",
]
GatewaySelectionRule = Literal["priority_then_availability", "availability_then_priority"]
SOURCE_FETCH_LIMIT = 10_000


class GatewayRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    stock_code: str | int
    holdings_limit: int = Field(default=15, ge=1, le=100)
    request_surface: str = "api"
    cache_first: bool = True
    selection_rule: GatewaySelectionRule = "priority_then_availability"
    request_id: str = Field(default_factory=lambda: uuid4().hex)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @computed_field
    @property
    def normalized_stock_code(self) -> str:
        return normalize_stock_code(self.stock_code)


class GatewayRequestContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str
    request_surface: str
    requested_at: datetime
    raw_stock_code: str | int
    normalized_stock_code: str
    holdings_limit: int
    source_limit: int = SOURCE_FETCH_LIMIT
    cache_first: bool
    selection_rule: GatewaySelectionRule = "priority_then_availability"
    source_hint: str | None = None

    @computed_field
    @property
    def cache_key(self) -> str:
        return f"{self.request_surface}:{self.normalized_stock_code}:{self.holdings_limit}"


class GatewaySourceCandidate(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    source_id: str
    source_name: str | None = None
    priority: int = 0
    status: GatewaySourceStatus = "unknown"
    backend: Any = None
    fallback_eligible: bool = True
    disabled_reason: str | None = None

    @computed_field
    @property
    def is_available(self) -> bool:
        return self.backend is not None and self.status not in {"disabled", "unavailable"}


class GatewaySourceAttempt(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str
    source_name: str | None = None
    priority: int = 0
    status: GatewaySourceStatus = "unknown"
    outcome: Literal["selected", "skipped", "failed", "cached"] = "skipped"
    reason: str | None = None


class GatewayRoutingSelection(BaseModel):
    model_config = ConfigDict(frozen=True)

    selection_rule: GatewaySelectionRule
    selected_source_id: str | None = None
    selected_source_name: str | None = None
    selected_source_status: GatewaySourceStatus = "unknown"
    selected_priority: int | None = None
    attempted_sources: tuple[str, ...] = ()
    attempted_statuses: tuple[GatewaySourceStatus, ...] = ()
    fallback_reason: str | None = None
    source_candidates: tuple[str, ...] = ()
    source_status: GatewaySourceStatus = "unknown"


class GatewaySourceTrace(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str
    request_surface: str
    requested_at: datetime
    requested_stock_code: str | int
    normalized_stock_code: str
    route: GatewayRoute
    cache_first: bool
    cache_hit: bool
    cache_key: str
    selection_rule: GatewaySelectionRule
    selected_source_id: str | None = None
    selected_source_name: str | None = None
    selected_source_status: GatewaySourceStatus = "unknown"
    attempted_sources: tuple[str, ...] = ()
    attempted_statuses: tuple[GatewaySourceStatus, ...] = ()
    fallback_reason: str | None = None
    source_candidates: tuple[str, ...] = ()
    source_status: GatewaySourceStatus = "unknown"
    source_name: str | None = None
    source_url: str | None = None
    source_date_type: Literal["holdings_date", "unknown"] = CCASS_SOURCE_DATE_TYPE
    date_convention_reference: str = CCASS_DATE_CONVENTION_REFERENCE
    data_as_of: date | None = None
    fetched_at: datetime | None = None
    response_cached: bool = False
    authoritative: bool = False
    notes: tuple[str, ...] = ()


class GatewayResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    request: GatewayRequestContext
    routing: GatewayRoutingSelection
    source_trace: GatewaySourceTrace
    normalized_response: CcassResponse


class GatewayCacheBackend(Protocol):
    async def get(self, request: GatewayRequestContext) -> CcassResponse | None: ...


class GatewaySourceBackend(Protocol):
    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse: ...


class CacheFirstSourceRouter:
    def __init__(
        self,
        *,
        source_backend: GatewaySourceBackend | None = None,
        source_candidates: tuple[GatewaySourceCandidate, ...] | None = None,
        cache_backend: GatewayCacheBackend | None = None,
        selection_rule: GatewaySelectionRule = "priority_then_availability",
    ) -> None:
        if source_candidates is None:
            if source_backend is None:
                raise ValueError("a source backend or source candidates must be provided")
            source_candidates = (
                GatewaySourceCandidate(
                    source_id="existing_service",
                    source_name=type(source_backend).__name__,
                    priority=0,
                    status="active",
                    backend=source_backend,
                    fallback_eligible=True,
                ),
            )
        self.source_candidates = tuple(source_candidates)
        self.cache_backend = cache_backend
        self.selection_rule = selection_rule

    def select_source(self, request: GatewayRequest) -> GatewayRoutingSelection:
        ordered = self._ordered_candidates(request)
        attempted_sources: list[str] = []
        attempted_statuses: list[GatewaySourceStatus] = []
        fallback_reason: str | None = None
        for candidate in ordered:
            attempted_sources.append(candidate.source_id)
            attempted_statuses.append(candidate.status)
            if candidate.is_available:
                return GatewayRoutingSelection(
                    selection_rule=request.selection_rule,
                    selected_source_id=candidate.source_id,
                    selected_source_name=candidate.source_name,
                    selected_source_status=candidate.status,
                    selected_priority=candidate.priority,
                    attempted_sources=tuple(attempted_sources),
                    attempted_statuses=tuple(attempted_statuses),
                    fallback_reason=fallback_reason,
                    source_candidates=tuple(item.source_id for item in ordered),
                    source_status=candidate.status,
                )
            fallback_reason = candidate.disabled_reason or (
                f"Source {candidate.source_id} is {candidate.status}."
            )
        return GatewayRoutingSelection(
            selection_rule=request.selection_rule,
            selected_source_id=None,
            selected_source_name=None,
            selected_source_status="unavailable",
            selected_priority=None,
            attempted_sources=tuple(attempted_sources),
            attempted_statuses=tuple(attempted_statuses),
            fallback_reason=fallback_reason or "No selectable source candidates were available.",
            source_candidates=tuple(item.source_id for item in ordered),
            source_status="unavailable",
        )

    async def route(self, request: GatewayRequest) -> GatewayResponse:
        context = GatewayRequestContext(
            request_id=request.request_id,
            request_surface=request.request_surface,
            requested_at=request.requested_at,
            raw_stock_code=request.stock_code,
            normalized_stock_code=request.normalized_stock_code,
            holdings_limit=request.holdings_limit,
            source_limit=SOURCE_FETCH_LIMIT,
            cache_first=request.cache_first,
            selection_rule=request.selection_rule,
        )

        if request.cache_first and self.cache_backend is not None:
            cached_response = await self.cache_backend.get(context)
            if cached_response is not None:
                routing = GatewayRoutingSelection(
                    selection_rule=request.selection_rule,
                    selected_source_id="cache",
                    selected_source_name="cache",
                    selected_source_status="cached",
                    selected_priority=-1,
                    attempted_sources=("cache",),
                    attempted_statuses=("cached",),
                    fallback_reason=None,
                    source_candidates=("cache",),
                    source_status="cached",
                )
                return GatewayResponse(
                    request=context,
                routing=routing,
                source_trace=self._build_trace(
                    context,
                    cached_response,
                    routing,
                        route="cache",
                        cache_hit=True,
                        notes=("cache_hit",),
                    ),
                    normalized_response=cached_response,
                )

        ordered = self._ordered_candidates(request)
        attempted_sources: list[str] = []
        attempted_statuses: list[GatewaySourceStatus] = []
        fallback_reason: str | None = None
        last_error: PlatformError | None = None
        for candidate in ordered:
            attempted_sources.append(candidate.source_id)
            attempted_statuses.append(candidate.status)
            if not candidate.is_available:
                if fallback_reason is None:
                    fallback_reason = candidate.disabled_reason or (
                        f"Source {candidate.source_id} is {candidate.status}."
                    )
                continue
            backend = cast(GatewaySourceBackend | None, candidate.backend)
            if backend is None:
                if fallback_reason is None:
                    fallback_reason = f"Source {candidate.source_id} has no backend."
                continue
            try:
                response = await backend.get_holdings(
                    context.normalized_stock_code,
                    limit=context.source_limit,
                )
            except PlatformError as exc:
                last_error = exc
                fallback_reason = self._fallback_reason_for_error(candidate, exc)
                if not candidate.fallback_eligible:
                    raise
                continue
            routing = GatewayRoutingSelection(
                selection_rule=request.selection_rule,
                selected_source_id=candidate.source_id,
                selected_source_name=candidate.source_name,
                selected_source_status=candidate.status,
                selected_priority=candidate.priority,
                attempted_sources=tuple(attempted_sources),
                attempted_statuses=tuple(attempted_statuses),
                fallback_reason=fallback_reason,
                source_candidates=tuple(item.source_id for item in ordered),
                source_status=candidate.status,
            )
            return GatewayResponse(
                request=context,
                routing=routing,
                source_trace=self._build_trace(
                    context,
                    response,
                    routing,
                    route="existing_service",
                    cache_hit=False,
                    notes=self._route_notes(candidate, routing, last_error),
                ),
                normalized_response=response,
            )

        if last_error is not None:
            raise last_error
        raise PlatformError(
            ErrorCode.SOURCE_UNAVAILABLE,
            "No selectable CCASS source candidates were available.",
            retry_recommended=True,
            status_code=503,
        )

    def _ordered_candidates(self, request: GatewayRequest) -> tuple[GatewaySourceCandidate, ...]:
        candidates = self.source_candidates
        if request.selection_rule == "availability_then_priority":
            return tuple(
                sorted(
                    candidates,
                    key=lambda candidate: (
                        0 if candidate.is_available else 1,
                        candidate.priority,
                        candidate.source_id,
                    ),
                )
            )
        return tuple(
            sorted(
                candidates,
                key=lambda candidate: (
                    candidate.priority,
                    0 if candidate.is_available else 1,
                    candidate.source_id,
                ),
            )
        )

    @staticmethod
    def _fallback_reason_for_error(candidate: GatewaySourceCandidate, exc: PlatformError) -> str:
        return f"{candidate.source_id} failed with {exc.code}: {exc.message}"

    @staticmethod
    def _route_notes(
        candidate: GatewaySourceCandidate,
        routing: GatewayRoutingSelection,
        last_error: PlatformError | None,
    ) -> tuple[str, ...]:
        notes: list[str] = []
        if routing.attempted_sources and routing.attempted_sources[0] != candidate.source_id:
            notes.append("source_selection_reordered")
        if routing.fallback_reason:
            notes.append(f"fallback_reason={routing.fallback_reason}")
        if last_error is not None:
            notes.append(f"last_error={last_error.code}")
        return tuple(notes)

    @staticmethod
    def _build_trace(
        context: GatewayRequestContext,
        response: CcassResponse,
        routing: GatewayRoutingSelection,
        *,
        route: GatewayRoute,
        cache_hit: bool,
        notes: tuple[str, ...],
    ) -> GatewaySourceTrace:
        metadata = response.metadata
        return GatewaySourceTrace(
            request_id=context.request_id,
            request_surface=context.request_surface,
            requested_at=context.requested_at,
            requested_stock_code=context.raw_stock_code,
            normalized_stock_code=context.normalized_stock_code,
            route=route,
            cache_first=context.cache_first,
            cache_hit=cache_hit,
            cache_key=context.cache_key,
            selection_rule=context.selection_rule,
            selected_source_id=routing.selected_source_id,
            selected_source_name=routing.selected_source_name,
            selected_source_status=routing.selected_source_status,
            attempted_sources=routing.attempted_sources,
            attempted_statuses=routing.attempted_statuses,
            fallback_reason=routing.fallback_reason,
            source_candidates=routing.source_candidates,
            source_status=routing.source_status,
            source_name=metadata.source_name,
            source_url=metadata.source_url,
            source_date_type=CCASS_SOURCE_DATE_TYPE,
            date_convention_reference=CCASS_DATE_CONVENTION_REFERENCE,
            data_as_of=metadata.data_as_of,
            fetched_at=metadata.fetched_at,
            response_cached=metadata.cached,
            authoritative=False,
            notes=notes,
        )


class CcassDataGateway:
    def __init__(
        self,
        *,
        source_backend: GatewaySourceBackend | None = None,
        source_candidates: tuple[GatewaySourceCandidate, ...] | None = None,
        cache_backend: GatewayCacheBackend | None = None,
        selection_rule: GatewaySelectionRule = "priority_then_availability",
    ) -> None:
        self.router = CacheFirstSourceRouter(
            source_backend=source_backend,
            source_candidates=source_candidates,
            cache_backend=cache_backend,
            selection_rule=selection_rule,
        )

    async def get_holdings(self, request: GatewayRequest) -> GatewayResponse:
        return await self.router.route(request)

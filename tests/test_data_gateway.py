from datetime import UTC, datetime, timedelta

from app.errors import ErrorCode, PlatformError
from app.services.ccass import CcassService
from app.services.data_gateway import (
    CcassDataGateway,
    CacheFirstSourceRouter,
    GatewayRequest,
    GatewaySourceCandidate,
)
from app.domain.history import HistoricalSnapshot
from app.sources.registry import GOOGLE_DRIVE_CSV_SOURCE_ID, WEBBSITE_SOURCE_ID
from app.storage.history import NormalizedSnapshotRepository


class FixtureSource:
    def __init__(self, response, *, error: PlatformError | None = None):
        self.response = response
        self.error = error
        self.calls = []

    async def get_holdings(self, code, limit=15):
        self.calls.append((code, limit))
        if self.error is not None:
            raise self.error
        return self.response.model_copy(deep=True)


class FixtureCache:
    def __init__(self, response=None):
        self.response = response
        self.calls = []

    async def get(self, request):
        self.calls.append(request)
        if self.response is None:
            return None
        return self.response.model_copy(deep=True)


def _request(stock_code="1592", *, selection_rule="priority_then_availability"):
    return GatewayRequest(
        stock_code=stock_code,
        holdings_limit=3,
        request_surface="api",
        selection_rule=selection_rule,
    )


def _persist_snapshot(repository, response, *, source_id, parser_version="fixture-parser"):
    repository.save(
        HistoricalSnapshot.from_response(
            response,
            source_id=source_id,
            parser_version=parser_version,
        )
    )


async def test_gateway_creation_builds_request_context_and_returns_wrapper(current_response):
    source = FixtureSource(current_response)
    gateway = CcassDataGateway(source_backend=source)

    result = await gateway.get_holdings(_request())

    assert result.request.normalized_stock_code == "01592"
    assert result.request.cache_key == "api:01592:3"
    assert result.normalized_response.metadata.code == "01592"
    assert result.routing.selected_source_id == "existing_service"
    assert source.calls == [("01592", 10_000)]


def test_stock_code_normalization_is_applied_before_routing():
    request = GatewayRequest(stock_code=1592, holdings_limit=15, request_surface="mcp")

    assert request.normalized_stock_code == "01592"


async def test_source_priority_prefers_lower_priority_candidate(current_response):
    primary = FixtureSource(current_response.model_copy(deep=True))
    fallback = FixtureSource(current_response.model_copy(deep=True))
    router = CacheFirstSourceRouter(
        source_candidates=(
            GatewaySourceCandidate(
                source_id="fallback",
                source_name="Fallback Source",
                priority=10,
                status="fallback",
                backend=fallback,
            ),
            GatewaySourceCandidate(
                source_id="primary",
                source_name="Primary Source",
                priority=0,
                status="active",
                backend=primary,
            ),
        )
    )

    result = await router.route(_request())

    assert result.routing.selected_source_id == "primary"
    assert result.routing.attempted_sources == ("primary",)
    assert result.routing.fallback_reason is None
    assert primary.calls == [("01592", 10000)]
    assert fallback.calls == []


async def test_fallback_selection_uses_next_available_candidate(current_response):
    failing = FixtureSource(
        current_response.model_copy(deep=True),
        error=PlatformError(
            ErrorCode.SOURCE_UNAVAILABLE,
            "Primary source unavailable.",
            retry_recommended=True,
            status_code=503,
        ),
    )
    fallback = FixtureSource(current_response.model_copy(deep=True))
    router = CacheFirstSourceRouter(
        source_candidates=(
            GatewaySourceCandidate(
                source_id="primary",
                source_name="Primary Source",
                priority=0,
                status="active",
                backend=failing,
            ),
            GatewaySourceCandidate(
                source_id="fallback",
                source_name="Fallback Source",
                priority=1,
                status="fallback",
                backend=fallback,
            ),
        )
    )

    result = await router.route(_request())

    assert result.routing.selected_source_id == "fallback"
    assert result.routing.attempted_sources == ("primary", "fallback")
    assert result.routing.fallback_reason and "primary failed" in result.routing.fallback_reason.lower()
    assert failing.calls == [("01592", 10000)]
    assert fallback.calls == [("01592", 10000)]


async def test_unavailable_source_handling_skips_disabled_candidate(current_response):
    unavailable = FixtureSource(current_response.model_copy(deep=True))
    selected = FixtureSource(current_response.model_copy(deep=True))
    router = CacheFirstSourceRouter(
        source_candidates=(
            GatewaySourceCandidate(
                source_id="unavailable",
                source_name="Disabled Candidate",
                priority=0,
                status="disabled",
                backend=None,
                disabled_reason="source pending approval",
            ),
            GatewaySourceCandidate(
                source_id="selected",
                source_name="Selected Candidate",
                priority=1,
                status="active",
                backend=selected,
            ),
        )
    )

    result = await router.route(_request())

    assert result.routing.selected_source_id == "selected"
    assert result.routing.attempted_sources == ("unavailable", "selected")
    assert result.routing.fallback_reason == "source pending approval"
    assert unavailable.calls == []
    assert selected.calls == [("01592", 10000)]


async def test_trace_metadata_preserves_selected_source_and_attempts(current_response):
    source = FixtureSource(current_response)
    cache = FixtureCache()
    gateway = CcassDataGateway(source_backend=source, cache_backend=cache)

    result = await gateway.get_holdings(_request())

    assert result.source_trace.route == "existing_service"
    assert result.source_trace.cache_hit is False
    assert result.source_trace.selected_source_id == "existing_service"
    assert result.source_trace.selected_source_status == "active"
    assert result.source_trace.attempted_sources == ("existing_service",)
    assert result.source_trace.source_status == "active"
    assert result.source_trace.source_name == current_response.metadata.source_name
    assert result.source_trace.source_url == current_response.metadata.source_url
    assert result.source_trace.data_as_of == current_response.metadata.data_as_of
    assert result.source_trace.fetched_at == current_response.metadata.fetched_at
    assert result.source_trace.response_cached == current_response.metadata.cached


async def test_gateway_cache_first_uses_cache_before_existing_service(current_response):
    cached_response = current_response.model_copy(deep=True)
    source = FixtureSource(current_response)
    cache = FixtureCache(cached_response)
    gateway = CcassDataGateway(source_backend=source, cache_backend=cache)

    result = await gateway.get_holdings(_request())

    assert source.calls == []
    assert len(cache.calls) == 1
    assert result.source_trace.route == "cache"
    assert result.source_trace.cache_hit is True
    assert result.source_trace.selected_source_id == "cache"
    assert result.source_trace.selected_source_status == "cached"
    assert result.source_trace.notes == ("cache_hit",)
    assert result.normalized_response.metadata.code == "01592"


async def test_stale_cache_does_not_bypass_live_source_when_current_data_required(
    tmp_path,
    current_response,
):
    repository = NormalizedSnapshotRepository(tmp_path / "cache.db")
    cached = current_response.model_copy(deep=True)
    cached.metadata.fetched_at = datetime.now(UTC) - timedelta(days=3)
    _persist_snapshot(repository, cached, source_id=WEBBSITE_SOURCE_ID)
    source = FixtureSource(current_response)
    from app.services.ccass import RepositorySnapshotBackend

    gateway = CcassDataGateway(
        source_backend=source,
        cache_backend=RepositorySnapshotBackend(
            repository,
            max_age_seconds=60 * 60,
        ),
    )

    result = await gateway.get_holdings(_request())

    assert source.calls == [("01592", 10000)]
    assert result.routing.selected_source_id == "existing_service"
    assert result.source_trace.route == "existing_service"
    assert result.source_trace.cache_hit is False
    assert result.normalized_response.metadata.cached is False
    assert result.normalized_response.metadata.data_as_of == current_response.metadata.data_as_of


async def test_live_failure_uses_lkg_recovery_before_csv_fallback(
    tmp_path,
    current_response,
):
    repository = NormalizedSnapshotRepository(tmp_path / "lkg.db")
    recovered = current_response.model_copy(deep=True)
    recovered.metadata.fetched_at = datetime.now(UTC) - timedelta(hours=2)
    _persist_snapshot(repository, recovered, source_id=WEBBSITE_SOURCE_ID)

    failing = FixtureSource(
        current_response.model_copy(deep=True),
        error=PlatformError(
            ErrorCode.SOURCE_TIMEOUT,
            "Live source unavailable.",
            retry_recommended=True,
            retry_after_seconds=30,
            status_code=504,
        ),
    )
    csv = FixtureSource(current_response.model_copy(deep=True))

    from app.services.ccass import RepositorySnapshotBackend

    gateway = CcassDataGateway(
        source_candidates=(
            GatewaySourceCandidate(
                source_id=WEBBSITE_SOURCE_ID,
                source_name="Webb-site mirror",
                priority=0,
                status="active",
                backend=failing,
            ),
            GatewaySourceCandidate(
                source_id="persistent_lkg",
                source_name="Persistent LKG",
                priority=1,
                status="fallback",
                backend=RepositorySnapshotBackend(
                    repository,
                    max_age_seconds=7 * 24 * 60 * 60,
                    source_ids=(WEBBSITE_SOURCE_ID,),
                ),
            ),
            GatewaySourceCandidate(
                source_id=GOOGLE_DRIVE_CSV_SOURCE_ID,
                source_name="Google Drive CSV",
                priority=2,
                status="fallback",
                backend=csv,
            ),
        )
    )

    result = await gateway.get_holdings(_request())

    assert failing.calls == [("01592", 10000)]
    assert csv.calls == []
    assert result.routing.selected_source_id == "persistent_lkg"
    assert result.routing.selected_source_status == "fallback"
    assert result.source_trace.route == "existing_service"
    assert result.source_trace.selected_source_id == "persistent_lkg"
    assert result.source_trace.selected_source_status == "fallback"
    assert result.normalized_response.metadata.cached is True
    assert result.normalized_response.metadata.data_as_of == current_response.metadata.data_as_of


async def test_lkg_unavailable_falls_back_to_csv_last_resort(
    tmp_path,
    current_response,
):
    repository = NormalizedSnapshotRepository(tmp_path / "empty_lkg.db")
    failing = FixtureSource(
        current_response.model_copy(deep=True),
        error=PlatformError(
            ErrorCode.SOURCE_TIMEOUT,
            "Live source unavailable.",
            retry_recommended=True,
            retry_after_seconds=30,
            status_code=504,
        ),
    )
    csv = FixtureSource(current_response.model_copy(deep=True))

    from app.services.ccass import RepositorySnapshotBackend

    gateway = CcassDataGateway(
        source_candidates=(
            GatewaySourceCandidate(
                source_id=WEBBSITE_SOURCE_ID,
                source_name="Webb-site mirror",
                priority=0,
                status="active",
                backend=failing,
            ),
            GatewaySourceCandidate(
                source_id="persistent_lkg",
                source_name="Persistent LKG",
                priority=1,
                status="fallback",
                backend=RepositorySnapshotBackend(
                    repository,
                    max_age_seconds=7 * 24 * 60 * 60,
                    source_ids=(WEBBSITE_SOURCE_ID,),
                ),
            ),
            GatewaySourceCandidate(
                source_id=GOOGLE_DRIVE_CSV_SOURCE_ID,
                source_name="Google Drive CSV",
                priority=2,
                status="fallback",
                backend=csv,
            ),
        )
    )

    result = await gateway.get_holdings(_request())

    assert failing.calls == [("01592", 10000)]
    assert csv.calls == [("01592", 10000)]
    assert result.routing.selected_source_id == GOOGLE_DRIVE_CSV_SOURCE_ID
    assert result.source_trace.selected_source_id == GOOGLE_DRIVE_CSV_SOURCE_ID
    assert result.normalized_response.metadata.cached is False
    assert result.normalized_response.metadata.data_as_of == current_response.metadata.data_as_of


async def test_ccass_service_persists_live_success_into_local_snapshot_cache(
    tmp_path,
    current_response,
    monkeypatch,
):
    repository = NormalizedSnapshotRepository(tmp_path / "persist.db")
    source = FixtureSource(current_response)
    monkeypatch.setattr("app.services.ccass.WebbsiteClient", lambda settings: source)
    service = CcassService(lkg_repository=repository)

    gateway_response = await service.get_stock_gateway_response("1592", holdings_limit=2)

    assert source.calls == [("01592", 10000)]
    assert gateway_response.routing.selected_source_id == WEBBSITE_SOURCE_ID
    stored = repository.latest("01592", source_id=WEBBSITE_SOURCE_ID)
    assert stored is not None
    assert stored.snapshot_date == current_response.metadata.holdings_date
    assert stored.fetched_at == current_response.metadata.fetched_at


async def test_ccass_service_regression_preserves_latest_holdings_contract(current_response):
    source = FixtureSource(current_response)
    service = CcassService(client=source)

    response = await service.get_stock_data("1592", holdings_limit=2)

    assert source.calls == [("01592", 10_000)]
    assert response.metadata.code == "01592"
    assert len(response.holdings) == 2
    assert response.holdings_summary.participant_count == 3

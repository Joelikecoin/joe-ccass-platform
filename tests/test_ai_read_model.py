from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from app.api import app
from app.data_quality import structured_warning
from app.errors import ErrorCode, PlatformError
from app.models import (
    AnnouncementRow,
    AnnouncementsMetadata,
    AnnouncementsResponse,
    PriceHistoryMetadata,
    PriceHistoryResponse,
    PriceHistoryRow,
)
from app.services.ai_read_model import AIReadModelService, get_ai_read_model_service
from app.services.announcements import AnnouncementsService
from app.services.ccass import CcassService
from app.services.price_history import PriceHistoryService
from app.storage.history import NormalizedSnapshotRepository
from app import mcp_server
from app.models import CcassResponse, HoldingRow, HoldingsSummary, SourceMetadata
from app.domain.history import HistoricalSnapshot
from ccass_core.ai_read_model import (
    AIReadModelContractMeta,
    AIReadModelContext,
    AIReadModelErrorState,
    AIReadModelHistory,
    AIReadModelIdentity,
    AIReadModelPayload,
    AIReadModelProvenance,
    AIReadModelQuality,
    AIReadModelSnapshotReference,
    AIReadModelSurfaceReference,
    AIReadModelTiming,
    AIReadModelV0_1,
)


def _announcements_response() -> AnnouncementsResponse:
    return AnnouncementsResponse(
        metadata=AnnouncementsMetadata(
            code="01592",
            name="TEST FIXTURE ??GOLDEN STOCK",
            source_name="HKEXnews",
            source_url="https://www1.hkexnews.hk/search/titlesearch.xhtml?category=0&lang=EN&market=SEHK&stockId=189695",
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            earliest_announcement_date=date(2026, 7, 19),
            latest_announcement_date=date(2026, 7, 20),
            announcement_count=1,
        ),
        announcements=[
            AnnouncementRow(
                announcement_date=date(2026, 7, 20),
                title="Sample HKEX announcement",
                source="HKEXnews",
                link="https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0720/2026072000123.pdf",
            )
        ],
    )


def _price_history_response() -> PriceHistoryResponse:
    return PriceHistoryResponse(
        metadata=PriceHistoryMetadata(
            code="01592",
            name="TEST FIXTURE ??GOLDEN STOCK",
            ticker="01592.HK",
            price_date_from=date(2026, 7, 19),
            price_date_to=date(2026, 7, 20),
            source_name="Yahoo Finance",
            source_url="https://query1.finance.yahoo.com/v8/finance/chart/01592.HK",
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            adjustment_state="adjusted",
            currency="HKD",
            adjustment_note="Adjusted close values are available from Yahoo Finance.",
        ),
        prices=[
            PriceHistoryRow(
                price_date=date(2026, 7, 19),
                open=1.0,
                high=1.1,
                low=0.9,
                close=1.05,
                adjusted_close=1.01,
                volume=1000,
                turnover=1050.0,
            )
        ],
    )


class FixtureCcassService(CcassService):
    def __init__(self, response: CcassResponse | None = None, error: PlatformError | None = None):
        self._response = response
        self._error = error

    async def get_stock_data(self, code, holdings_limit: int = 15):  # type: ignore[override]
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return self._response


class FixtureAnnouncementsService(AnnouncementsService):
    def __init__(self, response: AnnouncementsResponse | None = None, error: PlatformError | None = None):
        self._response = response
        self._error = error

    async def get_announcements(self, code, start_date=None, end_date=None):  # type: ignore[override]
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return self._response


class FixturePriceHistoryService(PriceHistoryService):
    def __init__(self, response: PriceHistoryResponse | None = None, error: PlatformError | None = None):
        self._response = response
        self._error = error

    async def get_price_history(self, code, start_date=None, end_date=None):  # type: ignore[override]
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return self._response


class FixtureSnapshotRepository:
    def __init__(
        self,
        *,
        current_id: int = 101,
        previous_id: int = 100,
        current_response: CcassResponse,
        previous_response: CcassResponse,
    ) -> None:
        self.current_id = current_id
        self.previous_id = previous_id
        self.current_date = current_response.metadata.data_as_of
        self.previous_date = previous_response.metadata.data_as_of
        self.previous_response = previous_response

    def snapshot_id_on(self, code: str, snapshot_date: date, *, source_id: str) -> int | None:
        if snapshot_date == self.current_date:
            return self.current_id
        if snapshot_date == self.previous_date:
            return self.previous_id
        return None

    def previous(self, code: str, *, before_date: date, source_id: str) -> HistoricalSnapshot | None:
        if before_date <= self.previous_date:
            return None
        return HistoricalSnapshot.from_response(self.previous_response, source_id=source_id)


class FixtureAIReadModelService:
    def __init__(self, model: AIReadModelV0_1):
        self.model = model
        self.calls: list[tuple[str, str]] = []

    async def get_read_model(self, code: str | int, *, surface: str = "ccass_ai_read_model") -> AIReadModelV0_1:
        self.calls.append((str(code), surface))
        return self.model


def _build_service(
    current_response: CcassResponse,
    previous_response: CcassResponse,
    *,
    ccass_service: CcassService | None = None,
    announcements_service: AnnouncementsService | None = None,
    price_history_service: PriceHistoryService | None = None,
) -> AIReadModelService:
    return AIReadModelService(
        ccass_service=ccass_service or FixtureCcassService(current_response),
        announcements_service=announcements_service or FixtureAnnouncementsService(_announcements_response()),
        price_history_service=price_history_service or FixturePriceHistoryService(_price_history_response()),
        snapshot_repository=FixtureSnapshotRepository(
            current_response=current_response,
            previous_response=previous_response,
        ),
    )


def test_ai_read_model_service_builds_normal_contract(current_response, previous_response):
    service = _build_service(current_response, previous_response)

    model = __import__("asyncio").run(service.get_read_model("1592"))

    assert model.identity == AIReadModelIdentity(
        stock_code="01592",
        market="HK",
        company_name=current_response.metadata.name,
    )
    assert model.timing.data_as_of == current_response.metadata.data_as_of
    assert model.provenance.source == current_response.metadata.source_name
    assert model.provenance.primary_or_fallback == "primary"
    assert model.quality.freshness_status == "fresh"
    assert model.history.snapshot_id == 101
    assert model.history.previous_snapshot == AIReadModelSnapshotReference(
        snapshot_id=100,
        snapshot_date=previous_response.metadata.data_as_of,
        data_as_of=previous_response.metadata.data_as_of,
        fetched_at=previous_response.metadata.fetched_at,
        source=previous_response.metadata.source_name,
    )
    assert model.history.comparison_context is not None
    assert model.history.comparison_context.previous_available is True
    assert model.context.announcements is not None
    assert model.context.price_reference is not None
    assert len(model.context.company_information_references) == 3
    assert model.payload.ccass is not None
    assert model.payload.announcements is not None
    assert model.payload.price_history is not None
    assert model.contract_meta == AIReadModelContractMeta(surface="ccass_ai_read_model")


def test_ai_read_model_service_marks_fallback_data_as_cached(current_response, previous_response):
    fallback_response = current_response.model_copy(
        deep=True,
        update={
            "metadata": current_response.metadata.model_copy(update={"cached": True}),
            "data_quality_warnings": [
                structured_warning(
                    "SOURCE_STATUS",
                    "CSV_FALLBACK_USED",
                    "Primary mirror failed (DATA_SOURCE_ERROR); using the configured CSV snapshot fallback.",
                )
            ],
        },
    )
    service = _build_service(
        fallback_response,
        previous_response,
        ccass_service=FixtureCcassService(fallback_response),
    )

    model = __import__("asyncio").run(service.get_read_model("1592"))

    assert model.provenance.primary_or_fallback == "fallback"
    assert model.quality.freshness_status == "cached"


def test_ai_read_model_service_marks_stale_warning_data(current_response, previous_response):
    stale_response = current_response.model_copy(
        deep=True,
        update={
            "data_quality_warnings": [
                structured_warning(
                    "FRESHNESS_STATUS",
                    "STALE_DATA",
                    "The current result is stale.",
                )
            ]
        },
    )
    service = _build_service(
        stale_response,
        previous_response,
        ccass_service=FixtureCcassService(stale_response),
    )

    model = __import__("asyncio").run(service.get_read_model("1592"))

    assert model.quality.freshness_status == "stale"
    assert any("STALE_DATA" in warning for warning in model.quality.warnings)


def test_ai_read_model_service_handles_unavailable_data():
    error = PlatformError(
        ErrorCode.SOURCE_TIMEOUT,
        "Primary source timed out.",
        retry_recommended=True,
    )
    service = AIReadModelService(
        ccass_service=FixtureCcassService(error=error),
        announcements_service=FixtureAnnouncementsService(_announcements_response()),
        price_history_service=FixturePriceHistoryService(_price_history_response()),
        snapshot_repository=FixtureSnapshotRepository(
            current_id=101,
            previous_id=100,
            current_response=_placeholder_response(),
            previous_response=_placeholder_response(),
        ),
    )

    model = __import__("asyncio").run(service.get_read_model("1592"))

    assert model.quality.freshness_status == "unavailable"
    assert model.quality.error_state == AIReadModelErrorState(
        code="SOURCE_TIMEOUT",
        message="Primary source timed out.",
        retry_recommended=True,
        retry_after_seconds=None,
    )
    assert model.payload.ccass is None


def test_api_and_mcp_return_the_same_ai_read_model(current_response, previous_response):
    service = _build_service(current_response, previous_response)
    expected_model = __import__("asyncio").run(service.get_read_model("1592"))
    fixture_service = FixtureAIReadModelService(expected_model)

    app.dependency_overrides[get_ai_read_model_service] = lambda: fixture_service
    original_getter = mcp_server.get_ai_read_model_service
    mcp_server.get_ai_read_model_service = lambda: fixture_service
    client = TestClient(app)
    try:
        api_response = client.get("/api/v1/ccass/1592/ai-read-model")
        mcp_response = __import__("asyncio").run(mcp_server.get_ai_read_model.fn("1592"))
    finally:
        app.dependency_overrides.clear()
        mcp_server.get_ai_read_model_service = original_getter

    assert api_response.status_code == 200
    assert api_response.json() == mcp_response
    assert fixture_service.calls == [("1592", "ccass_ai_read_model"), ("1592", "ccass_ai_read_model")]


def _placeholder_response() -> CcassResponse:
    return CcassResponse(
        metadata=SourceMetadata(
            code="01592",
            name="Placeholder",
            issue_id=15_920,
            holdings_date=date(2026, 7, 20),
            fetched_at=datetime(2026, 7, 21, 1, tzinfo=UTC),
            source_url="https://placeholder.invalid/",
            source_name="Placeholder source",
            cached=False,
            attribution="Placeholder",
        ),
        holdings_summary=HoldingsSummary(
            total_in_ccass_shares=1000,
            total_in_ccass_pct_of_issued=10.0,
            issued_shares=10_000,
            issued_shares_as_of=date(2026, 7, 20),
            non_ccass_shares=9_000,
            non_ccass_pct_of_issued=90.0,
            participant_count=1,
            top5_pct_of_issued=10.0,
            top10_pct_of_issued=10.0,
            top5_pct_of_ccass=100.0,
            top10_pct_of_ccass=100.0,
        ),
        holdings=[
            HoldingRow(
                rank=1,
                participant_id="B00001",
                participant="Placeholder",
                shares=1000,
                last_change=date(2026, 7, 20),
                pct_of_issued=10.0,
                pct_of_ccass=100.0,
                cumulative_pct_of_issued=10.0,
                participant_category="broker",
            )
        ],
        data_quality_warnings=[],
    )

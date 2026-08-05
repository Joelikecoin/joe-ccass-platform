from datetime import UTC, date, datetime

from app.data_quality import structured_warning
from app.models import (
    AnnouncementRow,
    AnnouncementsMetadata,
    AnnouncementsResponse,
    CapitalInformationMetadata,
    CapitalInformationResponse,
    CapitalInformationRow,
    OfficerRow,
    OfficersMetadata,
    OfficersResponse,
    PriceHistoryMetadata,
    PriceHistoryResponse,
    PriceHistoryRow,
    StockEventRow,
    StockEventsMetadata,
    StockEventsResponse,
)
from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.compute import compute_analysis
from ccass_core.research_context import build_research_context_package
from ccass_core.research_context_consumer import build_research_context_consumer_view


_UNSET = object()


def _announcements_response(*, warnings: list[str] | None = None) -> AnnouncementsResponse:
    return AnnouncementsResponse(
        metadata=AnnouncementsMetadata(
            code="01592",
            name="TEST FIXTURE — GOLDEN STOCK",
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
        data_quality_warnings=warnings or [],
    )


def _price_history_response(*, warnings: list[str] | None = None) -> PriceHistoryResponse:
    return PriceHistoryResponse(
        metadata=PriceHistoryMetadata(
            code="01592",
            name="TEST FIXTURE — GOLDEN STOCK",
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
        data_quality_warnings=warnings or [],
    )


def _stock_events_response(*, warnings: list[str] | None = None) -> StockEventsResponse:
    return StockEventsResponse(
        metadata=StockEventsMetadata(
            code="01592",
            name="TEST FIXTURE — GOLDEN STOCK",
            source_name="Pending stock events source",
            source_url=None,
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            data_as_of=date(2026, 7, 20),
            stock_events_count=1,
            source_status="ready",
        ),
        stock_events=[
            StockEventRow(
                event_date=date(2026, 7, 20),
                title="Sample stock event",
                event_type="corporate_action",
                source="Pending stock events source",
                link=None,
                details="Sample event details.",
            )
        ],
        data_quality_warnings=warnings or [],
    )


def _officers_response(*, warnings: list[str] | None = None) -> OfficersResponse:
    return OfficersResponse(
        metadata=OfficersMetadata(
            code="01592",
            name="TEST FIXTURE — GOLDEN STOCK",
            source_name="同花順 F10 managers",
            source_url="https://stockpage.10jqka.com.cn/basicweb/176/HK1351/manager.html",
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            data_as_of=date(2026, 7, 20),
            officers_count=1,
            source_status="ready",
        ),
        officers=[
            OfficerRow(
                name="Sample Officer",
                positions=["Director"],
                tenure_from=date(2024, 1, 1),
                tenure_to=None,
                is_current=True,
                sex=None,
                age=None,
                education=None,
                salary=None,
                biography=None,
            )
        ],
        data_quality_warnings=warnings or [],
    )


def _capital_information_response(*, warnings: list[str] | None = None) -> CapitalInformationResponse:
    return CapitalInformationResponse(
        metadata=CapitalInformationMetadata(
            code="01592",
            name="TEST FIXTURE — GOLDEN STOCK",
            source_name="Capital information source",
            source_url=None,
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            data_as_of=date(2026, 7, 20),
            capital_information_count=1,
            source_status="pending",
        ),
        capital_information=[
            CapitalInformationRow(
                label="Issued share capital",
                value="1000000",
                unit="shares",
                as_of=date(2026, 7, 20),
                source="Capital information source",
                note="Sample metric.",
                link=None,
            )
        ],
        data_quality_warnings=warnings or [],
    )


def _build_read_model(
    current_response,
    previous_response,
    *,
    announcements=_UNSET,
    price_history=_UNSET,
    extra_warnings=(),
):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    return build_ai_read_model_v0_1(
        code=current_response.metadata.code,
        response=current_response,
        surface="ccass_ai_read_model",
        analysis=analysis,
        previous_response=previous_response,
        snapshot_id=101,
        previous_snapshot_id=100,
        announcements=_announcements_response() if announcements is _UNSET else announcements,
        price_history=_price_history_response() if price_history is _UNSET else price_history,
        extra_warnings=extra_warnings,
    )


def test_research_context_consumer_helper_handles_normal_context(current_response, previous_response):
    ai_read_model = _build_read_model(current_response, previous_response)
    package = build_research_context_package(
        ai_read_model=ai_read_model,
        stock_events=_stock_events_response(),
        officers=_officers_response(),
        capital_information=_capital_information_response(),
    )

    consumer_view = build_research_context_consumer_view(package)

    assert consumer_view.available is True
    assert consumer_view.identity == package.identity
    assert consumer_view.ownership_context.current_snapshot == package.ownership_context.current_snapshot
    assert consumer_view.market_context.price_history == package.market_context.price_history
    assert consumer_view.company_context.announcements == package.company_context.announcements
    assert consumer_view.historical_context.previous_snapshot == package.historical_context.previous_snapshot
    assert consumer_view.quality_context == package.quality_context
    assert consumer_view.contract_meta == package.contract_meta


def test_research_context_consumer_helper_handles_missing_context():
    consumer_view = build_research_context_consumer_view(None)

    assert consumer_view.available is False
    assert consumer_view.identity is None
    assert consumer_view.ownership_context is None
    assert consumer_view.market_context is None
    assert consumer_view.company_context is None
    assert consumer_view.historical_context is None
    assert consumer_view.quality_context is None
    assert consumer_view.contract_meta is None
    assert consumer_view.warnings == []


def test_research_context_consumer_helper_handles_empty_data():
    ai_read_model = build_ai_read_model_v0_1(
        code="01592",
        response=None,
        surface="ccass_ai_read_model",
    )
    package = build_research_context_package(ai_read_model=ai_read_model)
    consumer_view = build_research_context_consumer_view(package)

    assert consumer_view.available is True
    assert consumer_view.identity.stock_code == "01592"
    assert consumer_view.ownership_context.current_snapshot is None
    assert consumer_view.ownership_context.holdings == []
    assert consumer_view.market_context.price_history is None
    assert consumer_view.company_context.announcements is None
    assert consumer_view.historical_context.current_snapshot is None
    assert consumer_view.quality_context.freshness_status == "unavailable"


def test_research_context_consumer_helper_propagates_warnings(current_response, previous_response):
    current_with_warning = current_response.model_copy(
        deep=True,
        update={
            "data_quality_warnings": [
                structured_warning("SOURCE_STATUS", "CSV_FALLBACK_USED", "Primary mirror failed; CSV fallback used."),
            ]
        },
    )
    stock_events = _stock_events_response(
        warnings=[
            structured_warning(
                "DATA_LIMITATION",
                "STOCK_EVENTS_UNAVAILABLE",
                "Stock events are unavailable (SOURCE_TIMEOUT: Fixture timeout).",
            )
        ]
    )
    ai_read_model = _build_read_model(
        current_with_warning,
        previous_response,
        extra_warnings=[
            structured_warning(
                "DATA_LIMITATION",
                "ANNOUNCEMENTS_UNAVAILABLE",
                "Announcements are unavailable (SOURCE_TIMEOUT: Fixture timeout).",
            )
        ],
    )
    package = build_research_context_package(
        ai_read_model=ai_read_model,
        stock_events=stock_events,
        officers=_officers_response(),
        capital_information=_capital_information_response(),
    )
    consumer_view = build_research_context_consumer_view(package)

    assert any("CSV_FALLBACK_USED" in warning for warning in consumer_view.warnings)
    assert any("ANNOUNCEMENTS_UNAVAILABLE" in warning for warning in consumer_view.warnings)
    assert any("STOCK_EVENTS_UNAVAILABLE" in warning for warning in consumer_view.warnings)


def test_research_context_consumer_helper_preserves_quality_context(current_response, previous_response):
    ai_read_model = _build_read_model(current_response, previous_response)
    package = build_research_context_package(
        ai_read_model=ai_read_model,
        stock_events=_stock_events_response(),
        officers=_officers_response(),
        capital_information=_capital_information_response(),
    )
    consumer_view = build_research_context_consumer_view(package)

    assert consumer_view.quality_context.provenance == package.quality_context.provenance
    assert consumer_view.quality_context.freshness_status == package.quality_context.freshness_status
    assert consumer_view.quality_context.warnings == package.quality_context.warnings
    assert consumer_view.quality_context.error_state == package.quality_context.error_state

import asyncio
from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from app import mcp_server
from app.api import app
from app.models import (
    AnnouncementRow,
    AnnouncementsMetadata,
    AnnouncementsResponse,
    OfficerRow,
    OfficersMetadata,
    OfficersResponse,
    PriceHistoryMetadata,
    PriceHistoryResponse,
    PriceHistoryRow,
)
from app.services.announcements import get_announcements_service
from app.services.ccass import get_ccass_service
from ccass_core.report import DEFAULT_LOCALE, SECTION_HEADINGS, translate_text


class FixtureService:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def get_stock_data(self, code, holdings_limit=15):
        self.calls.append((code, holdings_limit))
        return self.response


class FixtureAnnouncementsService:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def get_announcements(self, code, start_date=None, end_date=None):
        self.calls.append((code, start_date, end_date))
        return self.response


def _announcements_response() -> AnnouncementsResponse:
    return AnnouncementsResponse(
        metadata=AnnouncementsMetadata(
            code="01592",
            name="TEST FIXTURE ??GOLDEN STOCK",
            source_name="HKEXnews",
            source_url="https://www1.hkexnews.hk/search/titlesearch.xhtml?category=0&lang=EN&market=SEHK&stockId=189695",
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
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


def _officers_response() -> OfficersResponse:
    return OfficersResponse(
        metadata=OfficersMetadata(
            code="01592",
            name="TEST FIXTURE ??GOLDEN STOCK",
            source_name="同花順 F10 managers",
            source_url="https://stockpage.10jqka.com.cn/basicweb/176/HK1351/manager.html",
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            data_as_of=None,
            officers_count=1,
            source_status="ready",
        ),
        officers=[
            OfficerRow(
                name="董晖",
                positions=["主席", "执行董事", "行政总裁"],
                is_current=True,
                biography="董晖先生，于2018年11月8日获委任。",
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
                price_date=date(2026, 7, 20),
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


def _enriched_response(base_response):
    return base_response.model_copy(
        update={
            "announcements": _announcements_response(),
            "officers": _officers_response(),
            "price_history": _price_history_response(),
            "fetch_summary": "Source trace summary",
            "errors": ["NONE"],
        }
    )


def test_markdown_report_endpoint_reuses_core_without_breaking_json_api(current_response):
    service = FixtureService(current_response)
    announcements_service = FixtureAnnouncementsService(_announcements_response())
    app.dependency_overrides[get_ccass_service] = lambda: service
    app.dependency_overrides[get_announcements_service] = lambda: announcements_service
    client = TestClient(app)
    try:
        report_response = client.get(
            "/api/v1/ccass/1592/report",
            params={"holdings_limit": 25, "big_change_threshold": 500},
        )
        json_response = client.get("/api/v1/ccass/1592", params={"holdings_limit": 25})
    finally:
        app.dependency_overrides.clear()

    assert report_response.status_code == 200
    assert report_response.headers["content-type"].startswith("text/markdown")
    assert report_response.text.startswith(f"# {translate_text(DEFAULT_LOCALE, 'report.title')}")
    assert [line for line in report_response.text.splitlines() if line.startswith("## ")] == list(
        SECTION_HEADINGS
    )
    assert translate_text(DEFAULT_LOCALE, "report.section.announcements") in report_response.text
    assert "Sample HKEX announcement" in report_response.text
    assert json_response.status_code == 200
    assert json_response.json()["metadata"]["code"] == "01592"
    assert (
        json_response.json()["metadata"]["data_as_of"]
        == current_response.metadata.holdings_date.isoformat()
    )
    assert service.calls == [("01592", 25), ("1592", 25)]
    assert announcements_service.calls == [("01592", None, None)]


def test_json_api_passes_through_hkex_sdw_metadata(current_response):
    hkex_response = current_response.model_copy(
        update={
            "metadata": current_response.metadata.model_copy(
                update={
                    "source_name": "HKEX SDW",
                    "source_url": "https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx",
                }
            )
        }
    )
    service = FixtureService(hkex_response)
    app.dependency_overrides[get_ccass_service] = lambda: service
    client = TestClient(app)
    try:
        json_response = client.get("/api/v1/ccass/1592", params={"holdings_limit": 25})
    finally:
        app.dependency_overrides.clear()

    assert json_response.status_code == 200
    assert json_response.json()["metadata"]["source_name"] == "HKEX SDW"
    assert json_response.json()["metadata"]["source_url"].startswith("https://www3.hkexnews.hk/")
    assert service.calls == [("1592", 25)]


def test_api_and_mcp_return_the_same_enriched_stock_payload(current_response):
    enriched_response = _enriched_response(current_response)
    service = FixtureService(enriched_response)
    app.dependency_overrides[get_ccass_service] = lambda: service
    original_getter = mcp_server.get_ccass_service
    mcp_server.get_ccass_service = lambda: service
    client = TestClient(app)
    try:
        api_response = client.get("/api/v1/ccass/1592", params={"holdings_limit": 25})
        mcp_response = asyncio.run(mcp_server.get_ccass_stock_data.fn("1592", holdings_limit=25))
    finally:
        app.dependency_overrides.clear()
        mcp_server.get_ccass_service = original_getter

    assert api_response.status_code == 200
    assert api_response.json() == mcp_response
    assert api_response.json()["announcements"]["metadata"]["source_name"] == "HKEXnews"
    assert api_response.json()["officers"]["metadata"]["source_name"] == "同花順 F10 managers"
    assert api_response.json()["price_history"]["metadata"]["source_name"] == "Yahoo Finance"

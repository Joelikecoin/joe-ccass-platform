from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from app.api import app
from app.models import AnnouncementRow, AnnouncementsMetadata, AnnouncementsResponse
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

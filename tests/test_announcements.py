import asyncio
from datetime import UTC, date, datetime
import json
import re

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.api import app
from app.models import AnnouncementRow, AnnouncementsMetadata, AnnouncementsResponse
from app.services.announcements import get_announcements_service
from app.sources.announcements import (
    HKEXNEWS_PREFIX_URL,
    HKEXNEWS_TITLE_SEARCH_SERVLET_URL,
    HKEXNewsAnnouncementsSource,
)


def _announcements_response() -> AnnouncementsResponse:
    return AnnouncementsResponse(
        metadata=AnnouncementsMetadata(
            code="01592",
            name="ANCHORSTONE",
            source_name="HKEXnews",
            source_url="https://www1.hkexnews.hk/search/titlesearch.xhtml?category=0&lang=EN&market=SEHK&stockId=189695",
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            earliest_announcement_date=date(2026, 7, 19),
            latest_announcement_date=date(2026, 7, 20),
            announcement_count=2,
        ),
        announcements=[
            AnnouncementRow(
                announcement_date=date(2026, 7, 20),
                title="Sample HKEX announcement",
                source="HKEXnews",
                link="https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0720/2026072000123.pdf",
            ),
            AnnouncementRow(
                announcement_date=date(2026, 7, 19),
                title="Earlier HKEX announcement",
                source="HKEXnews",
                link="https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0719/2026071900456.pdf",
            ),
        ],
    )


@respx.mock
def test_hkexnews_announcements_source_parses_stock_lookup_and_rows():
    source = HKEXNewsAnnouncementsSource()

    prefix_route = respx.get(re.compile(r".*/search/prefix\.do.*")).mock(
        return_value=httpx.Response(
            200,
            text='callback({"more":"1","stockInfo":[{"stockId":189695,"code":"01592","name":"ANCHORSTONE"}]});',
        )
    )
    servlet_route = respx.get(re.compile(r".*/search/titleSearchServlet\.do.*")).mock(
        return_value=httpx.Response(
            200,
            json={
                "result": json.dumps(
                    [
                        {
                            "FILE_INFO": "88KB",
                            "NEWS_ID": "1",
                            "SHORT_TEXT": "Official announcement",
                            "TOTAL_COUNT": "2",
                            "DOD_WEB_PATH": "",
                            "STOCK_NAME": "ANCHORSTONE<br/>",
                            "TITLE": "Sample HKEX announcement",
                            "FILE_TYPE": "PDF",
                            "DATE_TIME": "20/07/2026 17:50",
                            "LONG_TEXT": "Official announcement",
                            "STOCK_CODE": "01592",
                            "FILE_LINK": "/listedco/listconews/sehk/2026/0720/2026072000123.pdf",
                        },
                        {
                            "FILE_INFO": "91KB",
                            "NEWS_ID": "2",
                            "SHORT_TEXT": "Official announcement",
                            "TOTAL_COUNT": "2",
                            "DOD_WEB_PATH": "",
                            "STOCK_NAME": "ANCHORSTONE<br/>",
                            "TITLE": "Earlier HKEX announcement",
                            "FILE_TYPE": "PDF",
                            "DATE_TIME": "19/07/2026 17:50",
                            "LONG_TEXT": "Official announcement",
                            "STOCK_CODE": "01592",
                            "FILE_LINK": "/listedco/listconews/sehk/2026/0719/2026071900456.pdf",
                        },
                    ]
                ),
                "hasNextRow": False,
                "sortList": "[[0,0]]",
                "rowRange": 10000,
                "lang": "E",
                "loadedRecord": 2,
                "recordCnt": 2,
            },
        )
    )

    response = asyncio.run(source.get_announcements("1592"))

    assert prefix_route.called
    assert servlet_route.called
    assert response.metadata.code == "01592"
    assert response.metadata.source_name == "HKEXnews"
    assert response.metadata.announcement_count == 2
    assert response.metadata.data_as_of == date(2026, 7, 20)
    assert len(response.announcements) == 2
    assert response.announcements[0].title == "Sample HKEX announcement"
    assert response.announcements[0].link.endswith("2026072000123.pdf")
    assert response.announcements[1].announcement_date == date(2026, 7, 19)


def test_api_announcements_endpoint_returns_json_payload():
    service = _announcements_response()

    class FixtureAnnouncementsService:
        def __init__(self, response: AnnouncementsResponse):
            self.response = response
            self.calls = []

        async def get_announcements(self, code, start_date=None, end_date=None):
            self.calls.append((code, start_date, end_date))
            return self.response

    fixture_service = FixtureAnnouncementsService(service)
    app.dependency_overrides[get_announcements_service] = lambda: fixture_service
    client = TestClient(app)
    try:
        response = client.get(
            "/api/v1/stocks/1592/announcements",
            params={"start_date": "2026-07-19", "end_date": "2026-07-20"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["code"] == "01592"
    assert body["metadata"]["source_name"] == "HKEXnews"
    assert body["announcements"][0]["title"] == "Sample HKEX announcement"
    assert fixture_service.calls == [("1592", date(2026, 7, 19), date(2026, 7, 20))]

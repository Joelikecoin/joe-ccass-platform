import asyncio
from datetime import UTC, datetime
from datetime import date

from fastapi.testclient import TestClient

from app.api import app
from app.errors import ErrorCode, PlatformError
from app.mcp_server import get_stock_events
from app.models import StockEventRow, StockEventsMetadata, StockEventsResponse
from app.services.stock_events import StockEventsService
from app.services.stock_events import get_stock_events_service
from app.sources.stock_events import STOCK_EVENTS_SOURCE_NAME, WebbsiteStockEventsSource
from app.sources.webbsite import FetchedPage
from ccass_core.compute import AnalysisResult
from ccass_core.report import DEFAULT_LOCALE, build_markdown_report, translate_text


STOCK_EVENTS_SAMPLE_HTML = """
<html>
  <head><title>Events: FURNIWEB HOLDINGS LIMITED: O HKD</title></head>
  <body>
    <h2>FURNIWEB HOLDINGS LIMITED</h2>
    <table>
      <tr>
        <th>Announced</th>
        <th>Year-end</th>
        <th>Type</th>
        <th>Amount</th>
        <th>Value in quote curr.</th>
        <th>New: Old</th>
        <th>ex-Date</th>
        <th>Distribution</th>
        <th>Notes</th>
      </tr>
      <tr>
        <td>2024-03-22</td>
        <td>2023-12-31</td>
        <td><a href="/dbpub/eventdets.asp?e=12345">Final dividend</a></td>
        <td>HKD 0.1000</td>
        <td></td>
        <td></td>
        <td>2024-05-28</td>
        <td>2024-06-14</td>
        <td>Board recommendation</td>
      </tr>
      <tr>
        <td>2023-08-25</td>
        <td>2023-12-31</td>
        <td>Int (Semi-annual) dividend</td>
        <td>HKD 0.1500</td>
        <td></td>
        <td></td>
        <td>2023-09-15</td>
        <td>2023-10-06</td>
        <td>Interim payout</td>
      </tr>
    </table>
  </body>
</html>
"""


def _stock_events_response() -> StockEventsResponse:
    return StockEventsResponse(
        metadata=StockEventsMetadata(
            code="01592",
            name="ANCHORSTONE",
            source_name="Stock events source pending",
            source_url=None,
            fetched_at=datetime(2026, 7, 21, 9, 15, tzinfo=UTC),
            data_as_of=None,
            stock_events_count=0,
            source_status="pending",
        ),
        stock_events=[],
        data_quality_warnings=[
            "SOURCE_STATUS:STOCK_EVENTS_SOURCE_PENDING: Stock events source is pending approval; placeholder read path only.",
        ],
    )


def _ready_stock_events_response() -> StockEventsResponse:
    return StockEventsResponse(
        metadata=StockEventsMetadata(
            code="01592",
            name="TEST FIXTURE ??GOLDEN STOCK",
            source_name=STOCK_EVENTS_SOURCE_NAME,
            source_url="https://webbsite.0xmd.com/dbpub/events.asp?i=25297",
            fetched_at=datetime(2026, 7, 21, 9, 15, tzinfo=UTC),
            data_as_of=date(2024, 3, 22),
            stock_events_count=2,
            source_status="ready",
        ),
        stock_events=[],
        data_quality_warnings=[],
    )


def test_stock_events_placeholder_response_renders_in_markdown(current_response):
    report = build_markdown_report(
        current_response,
        code="01592",
        analysis=AnalysisResult(previous_available=True),
        stock_events=_stock_events_response(),
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "report.section.stock_events") in report
    assert translate_text(DEFAULT_LOCALE, "ui.stock_events_source_pending") in report
    assert translate_text(DEFAULT_LOCALE, "ui.stock_events_empty") in report


def test_stock_events_ready_response_renders_in_markdown(current_response):
    report = build_markdown_report(
        current_response,
        code="01592",
        analysis=AnalysisResult(previous_available=True),
        stock_events=_ready_stock_events_response(),
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "report.section.stock_events") in report
    assert translate_text(DEFAULT_LOCALE, "ui.stock_events_source_ready") in report
    assert translate_text(DEFAULT_LOCALE, "ui.stock_events_empty") in report


def test_webbsite_stock_events_source_parses_ready_page(monkeypatch):
    source = WebbsiteStockEventsSource()

    async def fake_resolve_issue_id(code):
        assert code == "01592"
        return 25297, "FURNIWEB HOLDINGS LIMITED"

    async def fake_get_stock_events_page(issue_id: int):
        assert issue_id == 25297
        return FetchedPage(
            html=STOCK_EVENTS_SAMPLE_HTML,
            source_url="https://webbsite.0xmd.com/dbpub/events.asp?i=25297",
            cached=False,
        )

    monkeypatch.setattr(source.client, "resolve_issue_id", fake_resolve_issue_id)
    monkeypatch.setattr(source.client, "get_stock_events_page", fake_get_stock_events_page)

    response = asyncio.run(source.get_stock_events("1592"))

    assert response.metadata.code == "01592"
    assert response.metadata.name == "FURNIWEB HOLDINGS LIMITED"
    assert response.metadata.source_name == STOCK_EVENTS_SOURCE_NAME
    assert response.metadata.source_status == "ready"
    assert response.metadata.data_as_of == date(2024, 3, 22)
    assert response.metadata.stock_events_count == 2
    assert response.data_quality_warnings == []
    assert [row.title for row in response.stock_events] == [
        "Final dividend",
        "Int (Semi-annual) dividend",
    ]
    assert response.stock_events[0].event_type == "Dividend"
    assert response.stock_events[0].link == "https://webbsite.0xmd.com/dbpub/eventdets.asp?e=12345"
    assert "Year-end 2023-12-31" in (response.stock_events[0].details or "")


def test_webbsite_stock_events_source_returns_unavailable_payload(monkeypatch):
    source = WebbsiteStockEventsSource()

    async def fake_resolve_issue_id(code):
        assert code == "01592"
        return 25297, "FURNIWEB HOLDINGS LIMITED"

    async def fake_get_stock_events_page(_: int):
        raise PlatformError(
            ErrorCode.SOURCE_UNAVAILABLE,
            "network unavailable",
            retry_recommended=True,
            status_code=503,
        )

    monkeypatch.setattr(source.client, "resolve_issue_id", fake_resolve_issue_id)
    monkeypatch.setattr(source.client, "get_stock_events_page", fake_get_stock_events_page)

    response = asyncio.run(source.get_stock_events("1592"))

    assert response.metadata.source_name == STOCK_EVENTS_SOURCE_NAME
    assert response.metadata.source_status == "unavailable"
    assert response.metadata.source_url == "https://webbsite.0xmd.com/dbpub/events.asp?i=25297"
    assert response.stock_events == []
    assert any("STOCK_EVENTS_SOURCE_UNAVAILABLE" in warning for warning in response.data_quality_warnings)


def test_stock_events_service_adds_validation_warnings_without_blocking():
    class FixtureStockEventsSource:
        async def get_stock_events(self, code):
            return StockEventsResponse(
                metadata=StockEventsMetadata(
                    code="01592",
                    name="ANCHORSTONE",
                    source_name=STOCK_EVENTS_SOURCE_NAME,
                    source_url="https://example.invalid/stock-events",
                    fetched_at=datetime(2026, 7, 21, 9, 15, tzinfo=UTC),
                    data_as_of=date(2024, 3, 22),
                    stock_events_count=2,
                    source_status="ready",
                ),
                stock_events=[
                    StockEventRow.model_construct(
                        event_date="2026-13-01",
                        title="",
                        event_type=None,
                        source=STOCK_EVENTS_SOURCE_NAME,
                        link=None,
                        details=None,
                    ),
                    StockEventRow(
                        event_date=date(2024, 3, 22),
                        title="Final dividend",
                        event_type="Dividend",
                        source=STOCK_EVENTS_SOURCE_NAME,
                        link=None,
                        details=None,
                    ),
                ],
                data_quality_warnings=[],
            )

    service = StockEventsService(source=FixtureStockEventsSource())
    response = asyncio.run(service.get_stock_events("1592"))

    assert response.metadata.source_status == "ready"
    assert len(response.stock_events) == 2
    assert any("STOCK_EVENTS_EVENT_DATE_INVALID" in warning for warning in response.data_quality_warnings)
    assert any("STOCK_EVENTS_TITLE_MISSING" in warning for warning in response.data_quality_warnings)
    assert any("STOCK_EVENTS_INVALID_ROW" in warning for warning in response.data_quality_warnings)


def test_webbsite_stock_events_source_skips_broken_row_and_returns_partial_rows(monkeypatch):
    source = WebbsiteStockEventsSource()
    calls = {"count": 0}

    async def fake_resolve_issue_id(code):
        assert code == "01592"
        return 25297, "FURNIWEB HOLDINGS LIMITED"

    async def fake_get_stock_events_page(issue_id: int):
        assert issue_id == 25297
        return FetchedPage(
            html=STOCK_EVENTS_SAMPLE_HTML,
            source_url="https://webbsite.0xmd.com/dbpub/events.asp?i=25297",
            cached=False,
        )

    original_parse_event_row = source._parse_event_row

    def flaky_parse_event_row(row, header_map, *, source_url: str):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError("broken row")
        return original_parse_event_row(row, header_map, source_url=source_url)

    monkeypatch.setattr(source.client, "resolve_issue_id", fake_resolve_issue_id)
    monkeypatch.setattr(source.client, "get_stock_events_page", fake_get_stock_events_page)
    monkeypatch.setattr(source, "_parse_event_row", flaky_parse_event_row)

    response = asyncio.run(source.get_stock_events("1592"))

    assert response.metadata.source_status == "ready"
    assert response.metadata.stock_events_count == 1
    assert [row.title for row in response.stock_events] == ["Int (Semi-annual) dividend"]
    assert any("STOCK_EVENTS_ROW_PARSE_FAILED" in warning for warning in response.data_quality_warnings)


def test_api_stock_events_endpoint_returns_placeholder_payload():
    class FixtureStockEventsService:
        def __init__(self, response: StockEventsResponse):
            self.response = response
            self.calls = []

        async def get_stock_events(self, code):
            self.calls.append(code)
            return self.response

    fixture_service = FixtureStockEventsService(_stock_events_response())
    app.dependency_overrides[get_stock_events_service] = lambda: fixture_service
    client = TestClient(app)
    try:
        response = client.get("/api/v1/stocks/1592/stock-events")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["code"] == "01592"
    assert body["metadata"]["source_status"] == "pending"
    assert body["stock_events"] == []
    assert fixture_service.calls == ["1592"]


def test_mcp_stock_events_tool_returns_placeholder_payload(monkeypatch):
    class FixtureStockEventsService:
        def __init__(self, response: StockEventsResponse):
            self.response = response
            self.calls = []

        async def get_stock_events(self, code):
            self.calls.append(code)
            return self.response

    fixture_service = FixtureStockEventsService(_stock_events_response())
    import app.mcp_server as mcp_server

    monkeypatch.setattr(mcp_server, "get_stock_events_service", lambda: fixture_service)

    result = asyncio.run(get_stock_events("1592"))

    assert result["metadata"]["code"] == "01592"
    assert result["metadata"]["source_status"] == "pending"
    assert result["stock_events"] == []
    assert fixture_service.calls == ["1592"]

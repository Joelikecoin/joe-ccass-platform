import asyncio
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api import app
from app.mcp_server import get_stock_events
from app.models import StockEventsMetadata, StockEventsResponse
from app.services.stock_events import get_stock_events_service
from ccass_core.compute import AnalysisResult
from ccass_core.report import DEFAULT_LOCALE, build_markdown_report, translate_text


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

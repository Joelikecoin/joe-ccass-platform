import asyncio
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api import app
from app.mcp_server import get_capital_information
from app.models import CapitalInformationMetadata, CapitalInformationResponse
from app.services.capital_information import get_capital_information_service
from ccass_core.compute import AnalysisResult
from ccass_core.report import DEFAULT_LOCALE, build_markdown_report, translate_text


def _capital_information_response() -> CapitalInformationResponse:
    return CapitalInformationResponse(
        metadata=CapitalInformationMetadata(
            code="01592",
            name="ANCHORSTONE",
            source_name="Capital information source pending",
            source_url=None,
            fetched_at=datetime(2026, 7, 21, 9, 30, tzinfo=UTC),
            data_as_of=None,
            capital_information_count=0,
            source_status="pending",
        ),
        capital_information=[],
        data_quality_warnings=[
            "SOURCE_STATUS:CAPITAL_INFORMATION_SOURCE_PENDING: Capital information source is pending approval; placeholder read path only.",
        ],
    )


def test_capital_information_placeholder_response_renders_in_markdown(current_response):
    report = build_markdown_report(
        current_response,
        code="01592",
        analysis=AnalysisResult(previous_available=True),
        capital_information=_capital_information_response(),
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "report.section.capital_information") in report
    assert translate_text(DEFAULT_LOCALE, "ui.capital_information_source_pending") in report
    assert translate_text(DEFAULT_LOCALE, "ui.capital_information_empty") in report


def test_api_capital_information_endpoint_returns_placeholder_payload():
    class FixtureCapitalInformationService:
        def __init__(self, response: CapitalInformationResponse):
            self.response = response
            self.calls = []

        async def get_capital_information(self, code):
            self.calls.append(code)
            return self.response

    fixture_service = FixtureCapitalInformationService(_capital_information_response())
    app.dependency_overrides[get_capital_information_service] = lambda: fixture_service
    client = TestClient(app)
    try:
        response = client.get("/api/v1/stocks/1592/capital-information")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["code"] == "01592"
    assert body["metadata"]["source_status"] == "pending"
    assert body["capital_information"] == []
    assert fixture_service.calls == ["1592"]


def test_mcp_capital_information_tool_returns_placeholder_payload(monkeypatch):
    class FixtureCapitalInformationService:
        def __init__(self, response: CapitalInformationResponse):
            self.response = response
            self.calls = []

        async def get_capital_information(self, code):
            self.calls.append(code)
            return self.response

    fixture_service = FixtureCapitalInformationService(_capital_information_response())
    import app.mcp_server as mcp_server

    monkeypatch.setattr(mcp_server, "get_capital_information_service", lambda: fixture_service)

    result = asyncio.run(get_capital_information("1592"))

    assert result["metadata"]["code"] == "01592"
    assert result["metadata"]["source_status"] == "pending"
    assert result["capital_information"] == []
    assert fixture_service.calls == ["1592"]

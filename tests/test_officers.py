import asyncio
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api import app
from app.models import OfficersMetadata, OfficersResponse
from app.mcp_server import get_officers
from app.services.officers import get_officers_service
from ccass_core.compute import AnalysisResult
from ccass_core.report import DEFAULT_LOCALE, build_markdown_report, translate_text


def _officers_response() -> OfficersResponse:
    return OfficersResponse(
        metadata=OfficersMetadata(
            code="01592",
            name="ANCHORSTONE",
            source_name="Officers source pending",
            source_url=None,
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            data_as_of=None,
            officers_count=0,
            source_status="pending",
        ),
        officers=[],
        data_quality_warnings=[
            "SOURCE_STATUS:OFFICERS_SOURCE_PENDING: Officers source is pending approval; placeholder read path only.",
        ],
    )


def test_officers_placeholder_response_renders_in_markdown(current_response):
    report = build_markdown_report(
        current_response,
        code="01592",
        analysis=AnalysisResult(previous_available=True),
        officers=_officers_response(),
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "report.section.officers") in report
    assert translate_text(DEFAULT_LOCALE, "ui.officers_source_pending") in report
    assert translate_text(DEFAULT_LOCALE, "ui.officers_empty") in report


def test_api_officers_endpoint_returns_placeholder_payload():
    class FixtureOfficersService:
        def __init__(self, response: OfficersResponse):
            self.response = response
            self.calls = []

        async def get_officers(self, code):
            self.calls.append(code)
            return self.response

    fixture_service = FixtureOfficersService(_officers_response())
    app.dependency_overrides[get_officers_service] = lambda: fixture_service
    client = TestClient(app)
    try:
        response = client.get("/api/v1/stocks/1592/officers")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["code"] == "01592"
    assert body["metadata"]["source_status"] == "pending"
    assert body["officers"] == []
    assert fixture_service.calls == ["1592"]


def test_mcp_officers_tool_returns_placeholder_payload(monkeypatch):
    class FixtureOfficersService:
        def __init__(self, response: OfficersResponse):
            self.response = response
            self.calls = []

        async def get_officers(self, code):
            self.calls.append(code)
            return self.response

    fixture_service = FixtureOfficersService(_officers_response())
    import app.mcp_server as mcp_server

    monkeypatch.setattr(mcp_server, "get_officers_service", lambda: fixture_service)

    result = asyncio.run(get_officers("1592"))

    assert result["metadata"]["code"] == "01592"
    assert result["metadata"]["source_status"] == "pending"
    assert result["officers"] == []
    assert fixture_service.calls == ["1592"]

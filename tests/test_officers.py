import asyncio
from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from app.api import app
from app.models import OfficersMetadata, OfficersResponse
from app.mcp_server import get_officers
from app.services.officers import get_officers_service
from app.sources.officers import OFFICERS_SOURCE_NAME, ParsedOfficerRow, ThsF10OfficersSource
from app.errors import ErrorCode, PlatformError
from ccass_core.compute import AnalysisResult
from ccass_core.report import DEFAULT_LOCALE, build_markdown_report, translate_text
from app.models import OfficerRow
from app.services.officers import OfficersService


OFFICERS_SAMPLE_HTML = """
<html>
  <head>
    <title>輝煌明天(HK1351) 高管介紹_F10_同花順金融服務網</title>
  </head>
  <body>
    <h1>輝煌明天 01351</h1>
    <h2>高管簡介</h2>
    <p>高管 2 人 注：薪酬收入通常包含薪金、袍金、花紅、股票期權、福利津貼等。</p>
    <h3>董晖</h3>
    <p>主席，执行董事，行政总裁 | 本届任期：2019-03-25 至今</p>
    <p>男 39 本科 | 报酬：178.80万 | 截止日期：2026-04-15</p>
    <p>董晖先生，于2018年11月8日获委任为辉煌明天科技控股有限公司董事，并于2019年3月25日调任执行董事、董事会主席兼行政总裁。</p>
    <h3>杨登峰</h3>
    <p>执行董事，技术总监 | 本届任期：2019-03-25 至今</p>
    <p>男 44 本科 | 报酬：92.10万 | 截止日期：2026-04-15</p>
    <p>杨登峰先生，于2018年11月8日获委任为辉煌明天科技控股有限公司董事，并于2019年3月25日调任执行董事兼技术总监。</p>
  </body>
</html>
"""


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


def _ready_officers_response() -> OfficersResponse:
    return OfficersResponse(
        metadata=OfficersMetadata(
            code="01351",
            name="輝煌明天",
            source_name=OFFICERS_SOURCE_NAME,
            source_url="https://stockpage.10jqka.com.cn/basicweb/176/HK1351/manager.html",
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            data_as_of=date(2026, 4, 15),
            officers_count=2,
            source_status="ready",
        ),
        officers=[],
        data_quality_warnings=[],
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


def test_ths_f10_officers_source_parses_ready_page(monkeypatch):
    source = ThsF10OfficersSource()

    async def fake_fetch_html(source_url: str) -> str:
        assert source_url == "https://stockpage.10jqka.com.cn/basicweb/176/HK1351/manager.html"
        return OFFICERS_SAMPLE_HTML

    monkeypatch.setattr(source, "_fetch_html", fake_fetch_html)

    response = asyncio.run(source.get_officers("1351"))

    assert response.metadata.code == "01351"
    assert response.metadata.name == "輝煌明天"
    assert response.metadata.source_name == OFFICERS_SOURCE_NAME
    assert response.metadata.source_status == "ready"
    assert response.metadata.data_as_of == date(2026, 4, 15)
    assert response.metadata.officers_count == 2
    assert response.data_quality_warnings == []
    assert [row.name for row in response.officers] == ["董晖", "杨登峰"]
    assert response.officers[0].positions == ["主席", "执行董事", "行政总裁"]
    assert response.officers[0].tenure_from == date(2019, 3, 25)
    assert response.officers[0].tenure_to is None
    assert response.officers[0].is_current is True
    assert response.officers[0].sex == "男"
    assert response.officers[0].age == 39
    assert response.officers[0].education == "本科"
    assert response.officers[0].salary == "178.80万"
    assert response.officers[0].biography.startswith("董晖先生")


def test_ths_f10_officers_source_returns_unavailable_payload(monkeypatch):
    source = ThsF10OfficersSource()

    async def fake_fetch_html(_: str) -> str:
        raise PlatformError(
            ErrorCode.SOURCE_UNAVAILABLE,
            "network unavailable",
            retry_recommended=True,
            status_code=503,
        )

    monkeypatch.setattr(source, "_fetch_html", fake_fetch_html)

    response = asyncio.run(source.get_officers("1351"))

    assert response.metadata.source_name == OFFICERS_SOURCE_NAME
    assert response.metadata.source_status == "unavailable"
    assert response.officers == []
    assert any("OFFICERS_SOURCE_UNAVAILABLE" in warning for warning in response.data_quality_warnings)


def test_officers_service_adds_validation_warnings_without_blocking():
    class FixtureOfficersSource:
        async def get_officers(self, code):
            return OfficersResponse(
                metadata=OfficersMetadata(
                    code="01592",
                    name="ANCHORSTONE",
                    source_name=OFFICERS_SOURCE_NAME,
                    source_url="https://example.invalid/officers",
                    fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
                    data_as_of=date(2026, 4, 15),
                    officers_count=2,
                    source_status="ready",
                ),
                officers=[
                    OfficerRow(name=" ", positions=[]),
                    OfficerRow(name="Valid Officer", positions=["Director"]),
                ],
                data_quality_warnings=[],
            )

    service = OfficersService(source=FixtureOfficersSource())
    response = asyncio.run(service.get_officers("1592"))

    assert response.metadata.source_status == "ready"
    assert len(response.officers) == 2
    assert any("OFFICERS_NAME_MISSING" in warning for warning in response.data_quality_warnings)
    assert any("OFFICERS_POSITION_MISSING" in warning for warning in response.data_quality_warnings)
    assert any("OFFICERS_INVALID_ROW" in warning for warning in response.data_quality_warnings)


def test_officers_service_normalizes_pending_metadata():
    class FixtureOfficersSource:
        async def get_officers(self, code):
            return OfficersResponse(
                metadata=OfficersMetadata(
                    code="01592",
                    name=None,
                    source_name="Officers source pending",
                    source_url=None,
                    fetched_at=datetime(2026, 7, 21, 9, 0),
                    data_as_of=date(2026, 4, 15),
                    officers_count=0,
                    source_status="pending",
                ),
                officers=[],
                data_quality_warnings=[],
            )

    service = OfficersService(source=FixtureOfficersSource())
    response = asyncio.run(service.get_officers("1592"))

    assert response.metadata.source_name == OFFICERS_SOURCE_NAME
    assert response.metadata.source_url == "https://stockpage.10jqka.com.cn/basicweb/176/HK1592/manager.html"
    assert response.metadata.source_status == "pending"
    assert response.metadata.data_as_of is None
    assert response.metadata.fetched_at.tzinfo is not None


def test_ths_f10_officers_source_skips_broken_block_and_returns_partial_rows(monkeypatch):
    source = ThsF10OfficersSource()
    calls = {"count": 0}

    async def fake_fetch_html(source_url: str) -> str:
        assert source_url == "https://stockpage.10jqka.com.cn/basicweb/176/HK1351/manager.html"
        return OFFICERS_SAMPLE_HTML

    def flaky_parse_officer_block(name, block):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError("broken block")
        return ParsedOfficerRow(
            row=OfficerRow(
                name="備援董事",
                positions=["Director"],
                is_current=True,
            ),
            cutoff_date=date(2026, 4, 15),
        )

    monkeypatch.setattr(source, "_fetch_html", fake_fetch_html)
    monkeypatch.setattr(source, "_parse_officer_block", flaky_parse_officer_block)

    response = asyncio.run(source.get_officers("1351"))

    assert response.metadata.source_status == "ready"
    assert response.metadata.officers_count == 1
    assert [row.name for row in response.officers] == ["備援董事"]
    assert any("OFFICERS_BLOCK_PARSE_FAILED" in warning for warning in response.data_quality_warnings)


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

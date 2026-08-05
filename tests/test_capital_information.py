import asyncio
from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from app.api import app
from app.errors import ErrorCode, PlatformError
from app.mcp_server import get_capital_information
from app.models import CapitalInformationMetadata, CapitalInformationResponse
from app.services.capital_information import get_capital_information_service
from app.sources.capital_information import CAPITAL_INFORMATION_SOURCE_NAME, ThsF10CapitalInformationSource
from ccass_core.compute import AnalysisResult
from ccass_core.report import DEFAULT_LOCALE, build_markdown_report, translate_text


CAPITAL_INFORMATION_SAMPLE_HTML = """
<html>
  <head><title>中国春来(HK1969) 最新动态_F10_同花顺金融服务网</title></head>
  <body>
    <h1>中国春来</h1>
    <div>总股本： 12.00亿股 | 每手股数： 1000 | 净资产收益率(摊薄)： 18.12% | 资产负债率： 40.37%</div>
    <div>注释：公司货币计价单位为人民币元 上述数据来源于2025年年报</div>
  </body>
</html>
"""

CAPITAL_INFORMATION_SPLIT_SAMPLE_HTML = """
<html>
  <head><title>Split Capital (HK1969) _F10_\u540c\u82b1\u987a\u91d1\u878d\u670d\u52a1\u7f51</title></head>
  <body>
    <h1>Split Capital</h1>
    <div>\u603b\u80a1\u672c: 12.00 \u4ebf\u80a1</div>
    <div>\u6bcf\u624b\u80a1\u6570: 1000 \u80a1</div>
    <div>\u51c0\u8d44\u4ea7\u6536\u76ca\u7387(\u644a\u8584): 18.12%</div>
    <div>\u8d44\u4ea7\u8d1f\u503a\u7387: 40.37%</div>
    <div>\u6ce8\u91ca\uff1a\u4e0a\u8ff0\u6570\u636e\u6765\u6e90\u4e8e2025\u5e74\u5e74\u62a5</div>
  </body>
</html>
"""


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


def _ready_capital_information_response() -> CapitalInformationResponse:
    return CapitalInformationResponse(
        metadata=CapitalInformationMetadata(
            code="01592",
            name="中国春来",
            source_name=CAPITAL_INFORMATION_SOURCE_NAME,
            source_url="https://stockpage.10jqka.com.cn/basicweb/176/HK1592/",
            fetched_at=datetime(2026, 7, 21, 9, 30, tzinfo=UTC),
            data_as_of=date(2025, 12, 31),
            capital_information_count=4,
            source_status="ready",
        ),
        capital_information=[],
        data_quality_warnings=[],
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


def test_ths_f10_capital_information_source_parses_ready_page(monkeypatch):
    source = ThsF10CapitalInformationSource()

    async def fake_fetch_html(source_url: str) -> str:
        assert source_url == "https://stockpage.10jqka.com.cn/basicweb/176/HK1592/"
        return CAPITAL_INFORMATION_SAMPLE_HTML

    monkeypatch.setattr(source, "_fetch_html", fake_fetch_html)

    response = asyncio.run(source.get_capital_information("1592"))

    assert response.metadata.code == "01592"
    assert response.metadata.name == "中国春来"
    assert response.metadata.source_name == CAPITAL_INFORMATION_SOURCE_NAME
    assert response.metadata.source_status == "ready"
    assert response.metadata.data_as_of == date(2025, 12, 31)
    assert response.metadata.capital_information_count == 4
    assert response.data_quality_warnings == []
    assert [row.label for row in response.capital_information] == [
        "Total shares",
        "Board lot size",
        "Diluted ROE",
        "Debt ratio",
    ]
    assert response.capital_information[0].value == "12.00"
    assert response.capital_information[0].unit == "亿股"
    assert response.capital_information[0].link == "https://stockpage.10jqka.com.cn/basicweb/176/HK1592/"


def test_ths_f10_capital_information_source_returns_unavailable_payload(monkeypatch):
    source = ThsF10CapitalInformationSource()

    async def fake_fetch_html(_: str) -> str:
        raise PlatformError(
            ErrorCode.SOURCE_UNAVAILABLE,
            "network unavailable",
            retry_recommended=True,
            status_code=503,
        )

    monkeypatch.setattr(source, "_fetch_html", fake_fetch_html)

    response = asyncio.run(source.get_capital_information("1592"))

    assert response.metadata.source_name == CAPITAL_INFORMATION_SOURCE_NAME
    assert response.metadata.source_status == "unavailable"
    assert response.metadata.source_url == "https://stockpage.10jqka.com.cn/basicweb/176/HK1592/"
    assert response.capital_information == []
    assert any("CAPITAL_INFORMATION_SOURCE_UNAVAILABLE" in warning for warning in response.data_quality_warnings)




def test_ths_f10_capital_information_source_parses_split_summary_lines(monkeypatch):
    source = ThsF10CapitalInformationSource()

    async def fake_fetch_html(source_url: str) -> str:
        assert source_url == "https://stockpage.10jqka.com.cn/basicweb/176/HK1592/"
        return CAPITAL_INFORMATION_SPLIT_SAMPLE_HTML

    monkeypatch.setattr(source, "_fetch_html", fake_fetch_html)

    response = asyncio.run(source.get_capital_information("1592"))

    assert response.metadata.source_status == "ready"
    assert response.metadata.capital_information_count == 4
    assert [row.label for row in response.capital_information] == [
        "Total shares",
        "Board lot size",
        "Diluted ROE",
        "Debt ratio",
    ]
    assert response.data_quality_warnings == []


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

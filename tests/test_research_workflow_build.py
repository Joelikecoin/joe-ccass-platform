from datetime import UTC, date, datetime

from streamlit.testing.v1 import AppTest

from app.models import (
    AnnouncementsMetadata,
    AnnouncementsResponse,
    CapitalInformationMetadata,
    CapitalInformationResponse,
    OfficersMetadata,
    OfficersResponse,
    StockEventsMetadata,
    StockEventsResponse,
)
from app.streamlit_ui import DEFAULT_LOCALE, build_research_workflow_overview_markdown, translate_text


class _DemoService:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def get_stock_data(self, code, holdings_limit=15):
        self.calls.append((code, holdings_limit))
        return self.response


class _DemoAnnouncementsService:
    def __init__(self, response: AnnouncementsResponse):
        self.response = response

    async def get_announcements(self, code, start_date=None, end_date=None):
        return self.response


class _DemoStockEventsService:
    def __init__(self, response: StockEventsResponse):
        self.response = response

    async def get_stock_events(self, code):
        return self.response


class _DemoCapitalInformationService:
    def __init__(self, response: CapitalInformationResponse):
        self.response = response

    async def get_capital_information(self, code):
        return self.response


class _DemoOfficersService:
    def __init__(self, response: OfficersResponse):
        self.response = response

    async def get_officers(self, code):
        return self.response


def _demo_announcements_response() -> AnnouncementsResponse:
    return AnnouncementsResponse(
        metadata=AnnouncementsMetadata(
            code="01592",
            name="DEMO STOCK",
            source_name="HKEXnews",
            source_url="https://www1.hkexnews.hk/search/titlesearch.xhtml",
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            announcement_count=0,
        ),
        announcements=[],
        data_quality_warnings=[],
    )


def _demo_stock_events_response() -> StockEventsResponse:
    return StockEventsResponse(
        metadata=StockEventsMetadata(
            code="01592",
            name="DEMO STOCK",
            source_name="Stock events source pending",
            source_url=None,
            fetched_at=datetime(2026, 7, 21, 9, 15, tzinfo=UTC),
            data_as_of=None,
            stock_events_count=0,
            source_status="pending",
        ),
        stock_events=[],
        data_quality_warnings=["SOURCE_STATUS:STOCK_EVENTS_SOURCE_PENDING: Placeholder path only."],
    )


def _demo_capital_information_response() -> CapitalInformationResponse:
    return CapitalInformationResponse(
        metadata=CapitalInformationMetadata(
            code="01592",
            name="DEMO STOCK",
            source_name="Capital information source pending",
            source_url=None,
            fetched_at=datetime(2026, 7, 21, 9, 30, tzinfo=UTC),
            data_as_of=None,
            capital_information_count=0,
            source_status="pending",
        ),
        capital_information=[],
        data_quality_warnings=["SOURCE_STATUS:CAPITAL_INFORMATION_SOURCE_PENDING: Placeholder path only."],
    )


def _demo_officers_response() -> OfficersResponse:
    return OfficersResponse(
        metadata=OfficersMetadata(
            code="01592",
            name="DEMO STOCK",
            source_name="同花順 F10 managers",
            source_url="https://stockpage.10jqka.com.cn/basicweb/176/HK1592/manager.html",
            fetched_at=datetime(2026, 7, 21, 9, 45, tzinfo=UTC),
            data_as_of=date(2026, 4, 15),
            officers_count=0,
            source_status="ready",
        ),
        officers=[],
        data_quality_warnings=[],
    )


def test_build_research_workflow_overview_markdown_describes_usable_path():
    markdown = build_research_workflow_overview_markdown(locale=DEFAULT_LOCALE)

    assert "Research workflow path" in markdown
    assert "01592" in markdown
    assert "Stock Input" in markdown
    assert "Data Retrieval / Existing Snapshot" in markdown
    assert "Research Dashboard" in markdown
    assert "Analysis Display" in markdown
    assert "Report Output" in markdown
    assert "CCASS holdings information" in markdown
    assert "Export and copy controls" in markdown


def test_streamlit_app_renders_demo_overview_and_report_flow(monkeypatch, current_response):
    import app.services.announcements as announcements_service
    import app.services.capital_information as capital_information_service
    import app.services.ccass as ccass_service
    import app.services.officers as officers_service
    import app.services.stock_events as stock_events_service
    import app.streamlit_ui as streamlit_ui

    demo_service = _DemoService(current_response)
    monkeypatch.setattr(ccass_service, "get_ccass_service", lambda: demo_service)
    monkeypatch.setattr(announcements_service, "get_announcements_service", lambda: _DemoAnnouncementsService(_demo_announcements_response()))
    monkeypatch.setattr(stock_events_service, "get_stock_events_service", lambda: _DemoStockEventsService(_demo_stock_events_response()))
    monkeypatch.setattr(capital_information_service, "get_capital_information_service", lambda: _DemoCapitalInformationService(_demo_capital_information_response()))
    monkeypatch.setattr(officers_service, "get_officers_service", lambda: _DemoOfficersService(_demo_officers_response()))
    monkeypatch.setattr(streamlit_ui, "get_announcements_service", lambda: _DemoAnnouncementsService(_demo_announcements_response()))
    monkeypatch.setattr(streamlit_ui, "get_stock_events_service", lambda: _DemoStockEventsService(_demo_stock_events_response()))
    monkeypatch.setattr(streamlit_ui, "get_capital_information_service", lambda: _DemoCapitalInformationService(_demo_capital_information_response()))
    monkeypatch.setattr(streamlit_ui, "get_officers_service", lambda: _DemoOfficersService(_demo_officers_response()))

    app = AppTest.from_file("streamlit_app.py").run(timeout=20)
    app.text_input[0].input("1592")
    app.button[0].click().run(timeout=20)

    assert not app.exception
    assert any("Research workflow path" in block.value for block in app.markdown)
    assert any("Stock Input" in block.value for block in app.markdown)
    assert any("Data Retrieval / Existing Snapshot" in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, "ui.report_flow_heading") in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, "ui.copy_for_chatgpt") in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, "ui.downloads_heading") in block.value for block in app.markdown)
    assert demo_service.calls == [("01592", 20)]

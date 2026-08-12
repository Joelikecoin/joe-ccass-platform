from pathlib import Path
from datetime import UTC, date, datetime

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
from app.streamlit_ui import (
    DEFAULT_LOCALE,
    PreparedReport,
    build_holder_change_investigation_markdown,
    build_research_dashboard_markdown,
    build_ownership_distribution_markdown,
    build_research_intelligence_markdown,
    build_report_flow_markdown,
    build_research_workflow_overview_markdown,
    translate_text,
)
from ccass_core.compute import AnalysisResult, compute_analysis


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
    assert "AI-ready research context handoff in the report output" in markdown
    assert "Export and copy controls" in markdown


def test_build_research_dashboard_markdown_summarizes_research_state(current_response, previous_response):
    prepared = PreparedReport(
        code=current_response.metadata.code,
        markdown="",
        chatgpt_payload="",
        filename="01592_ccass_report.md",
        response=current_response,
        previous_response=previous_response,
        analysis=compute_analysis(current_response, previous_response),
    )

    markdown = build_research_dashboard_markdown(
        prepared,
        history_snapshots=(previous_response,),
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_caption") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_stock_code") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_snapshot_count") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_freshness") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_provenance") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_concentration") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_comparison") in markdown
    assert translate_text(DEFAULT_LOCALE, "report.section.research_context_handoff").removeprefix("## ").strip() in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_report_output") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_link_ownership_distribution") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_link_holder_changes") in markdown
    assert "#holdings" in markdown
    assert "#ownership-distribution" in markdown
    assert "#holder-change-investigation" in markdown
    assert "#concentration" in markdown
    assert "#changes" in markdown
    assert "#big-changes" in markdown
    assert "#research-context-handoff" in markdown
    assert "#copy-for-chatgpt" in markdown
    assert "#raw-markdown" in markdown


def test_build_ownership_distribution_markdown_summarizes_holder_distribution_and_change_focus(
    current_response,
    previous_response,
):
    prepared = PreparedReport(
        code=current_response.metadata.code,
        markdown="",
        chatgpt_payload="",
        filename="01592_ccass_report.md",
        response=current_response,
        previous_response=previous_response,
        analysis=compute_analysis(current_response, previous_response),
    )

    markdown = build_ownership_distribution_markdown(
        prepared,
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_caption") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_top_holders_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_change_focus_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_participant_count") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_total_in_ccass_shares") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_total_in_ccass_pct_of_issued") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_top5_pct_of_issued") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_top10_pct_of_issued") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_top5_pct_of_ccass") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_top10_pct_of_ccass") in markdown
    assert "TEST FIXTURE BROKER ONE" in markdown
    assert "TEST FIXTURE BROKER TWO" in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_intelligence_changes_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_link_big_changes") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_link_holder_changes") in markdown
    assert "<a id='ownership-distribution'></a>" in markdown


def test_build_holder_change_investigation_markdown_summarizes_holder_movement_context(
    current_response,
    previous_response,
):
    prepared = PreparedReport(
        code=current_response.metadata.code,
        markdown="",
        chatgpt_payload="",
        filename="01592_ccass_report.md",
        response=current_response,
        previous_response=previous_response,
        analysis=compute_analysis(current_response, previous_response),
    )

    markdown = build_holder_change_investigation_markdown(
        prepared,
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "ui.holder_change_investigation_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.holder_change_investigation_caption") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.holder_change_investigation_summary_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.holder_change_investigation_top_changes_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.holder_change_investigation_transfer_patterns_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.holder_change_investigation_previous_snapshot") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.holder_change_investigation_change_count") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.holder_change_investigation_big_change_count") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.holder_change_investigation_transfer_pattern_count") in markdown
    assert "TEST FIXTURE BROKER ONE" in markdown
    assert "TEST FIXTURE BROKER TWO" in markdown
    assert "<a id='holder-change-investigation'></a>" in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_link_changes") in markdown
    assert "#changes" in markdown
    assert "#big-changes" in markdown
    assert "#concentration" in markdown


def test_build_research_intelligence_markdown_summarizes_current_state_changes_and_deeper_links(
    current_response,
    previous_response,
):
    prepared = PreparedReport(
        code=current_response.metadata.code,
        markdown="",
        chatgpt_payload="",
        filename="01592_ccass_report.md",
        response=current_response,
        previous_response=previous_response,
        analysis=compute_analysis(current_response, previous_response),
    )

    markdown = build_research_intelligence_markdown(
        prepared,
        history_snapshots=(previous_response,),
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "ui.related_context_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_intelligence_current_state_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_intelligence_changes_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_intelligence_deeper_look_heading") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_intelligence_current_state_body") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_intelligence_changes_body") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_intelligence_deeper_look_body") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_snapshot_date") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_snapshot_count") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_comparison") in markdown
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_report_output") in markdown
    assert "#changes" in markdown
    assert "#big-changes" in markdown
    assert "#concentration" in markdown
    assert "#concentration-history" in markdown


def test_streamlit_app_renders_research_dashboard_and_report_flow(current_response, previous_response):
    prepared = PreparedReport(
        code=current_response.metadata.code,
        markdown="",
        chatgpt_payload="",
        filename="01592_ccass_report.md",
        response=current_response,
        previous_response=previous_response,
        analysis=compute_analysis(current_response, previous_response),
    )

    workflow_overview = build_research_workflow_overview_markdown(locale=DEFAULT_LOCALE)
    dashboard = build_research_dashboard_markdown(
        prepared,
        history_snapshots=(previous_response,),
        locale=DEFAULT_LOCALE,
    )
    intelligence = build_research_intelligence_markdown(
        prepared,
        history_snapshots=(previous_response,),
        locale=DEFAULT_LOCALE,
    )
    report_flow = build_report_flow_markdown(locale=DEFAULT_LOCALE)

    assert "Research workflow path" in workflow_overview
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_heading") in dashboard
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_caption") in dashboard
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_stock_code") in dashboard
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_quick_links") in dashboard
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_link_ownership_distribution") in dashboard
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_link_holder_changes") in dashboard
    assert "#ownership-distribution" in dashboard
    assert "#holder-change-investigation" in dashboard
    ownership_distribution = build_ownership_distribution_markdown(
        prepared,
        locale=DEFAULT_LOCALE,
    )
    assert translate_text(DEFAULT_LOCALE, "ui.ownership_distribution_heading") in ownership_distribution
    holder_changes = build_holder_change_investigation_markdown(
        prepared,
        locale=DEFAULT_LOCALE,
    )
    assert translate_text(DEFAULT_LOCALE, "ui.holder_change_investigation_heading") in holder_changes
    assert translate_text(DEFAULT_LOCALE, "ui.holder_change_investigation_summary_heading") in holder_changes
    assert translate_text(DEFAULT_LOCALE, "ui.research_dashboard_link_ownership_distribution") in holder_changes
    assert translate_text(DEFAULT_LOCALE, "ui.research_intelligence_current_state_heading") in intelligence
    assert translate_text(DEFAULT_LOCALE, "ui.research_intelligence_changes_heading") in intelligence
    assert translate_text(DEFAULT_LOCALE, "ui.research_intelligence_deeper_look_heading") in intelligence
    assert translate_text(DEFAULT_LOCALE, "ui.report_flow_visible_first") in report_flow
    assert translate_text(DEFAULT_LOCALE, "ui.report_flow_collapsed_details") in report_flow
    assert translate_text(DEFAULT_LOCALE, "ui.report_flow_actions") in report_flow
    assert translate_text(DEFAULT_LOCALE, "ui.related_context_heading") in report_flow

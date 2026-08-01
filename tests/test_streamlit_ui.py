import base64
import re
import zipfile
from datetime import date, datetime

import pytest
from io import BytesIO
from xml.etree import ElementTree as ET

from streamlit.testing.v1 import AppTest

from app.errors import ErrorCode, PlatformError
from app.models import CcassResponse, HoldingRow, HoldingsSummary, SourceMetadata
from app.streamlit_ui import (
    DEFAULT_LOCALE,
    STREAMLIT_NAV_SECTIONS,
    STREAMLIT_SIDEBAR_CONTROL_LABELS,
    build_download_artifacts,
    build_full_summary_markdown,
    build_raw_preview_tables,
    PreparedReport,
    copy_button_html,
    prepare_report,
    resolve_streamlit_query_input,
    streamlit_chart_help_sections,
    streamlit_hkex_announcements_columns,
    streamlit_navigation_links,
    streamlit_navigation_sections,
    streamlit_responsive_layout_css,
    streamlit_sidebar_control_labels,
    translate_text,
)
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.compute import AnalysisResult
from ccass_core.report import CHATGPT_COPY_HEADER, localized_report_anchor, report_section_headings


class SuccessfulService:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def get_stock_data(self, code, holdings_limit=15):
        self.calls.append((code, holdings_limit))
        return self.response


class FailingService:
    async def get_stock_data(self, code, holdings_limit=15):
        raise PlatformError(
            ErrorCode.SOURCE_UNAVAILABLE,
            "Offline fixture: source unavailable.",
            retry_recommended=True,
        )


async def test_prepare_report_normalizes_1592_and_applies_holdings_limit(current_response):
    service = SuccessfulService(current_response)
    progress = []

    prepared = await prepare_report(
        "1592",
        holdings_limit=25,
        big_change_threshold=500,
        service=service,
        progress=lambda value, label: progress.append((value, label)),
    )

    assert prepared.code == "01592"
    assert service.calls == [("01592", 25)]
    assert prepared.filename == "01592_ccass_report.md"
    assert progress[-1] == (100, translate_text(DEFAULT_LOCALE, "ui.progress_ready"))

@pytest.mark.parametrize("locale", [DEFAULT_LOCALE, "en"])
async def test_prepare_report_uses_localized_progress_labels(current_response, locale):
    service = SuccessfulService(current_response)
    progress = []

    prepared = await prepare_report(
        "1592",
        holdings_limit=25,
        big_change_threshold=500,
        service=service,
        locale=locale,
        progress=lambda value, label: progress.append((value, label)),
    )

    assert prepared.code == "01592"
    assert progress == [
        (15, translate_text(locale, "ui.progress_validated_stock_code")),
        (30, translate_text(locale, "ui.progress_fetching_source")),
        (65, translate_text(locale, "ui.progress_computing_analysis")),
        (85, translate_text(locale, "ui.progress_rendering_report")),
        (100, translate_text(locale, "ui.progress_ready")),
    ]


async def test_prepare_report_network_failure_keeps_all_sections():
    prepared = await prepare_report(
        "1592",
        holdings_limit=20,
        big_change_threshold=500,
        service=FailingService(),
        locale=DEFAULT_LOCALE,
    )

    assert prepared.fetch_error.startswith("SOURCE_UNAVAILABLE:")
    assert translate_text(DEFAULT_LOCALE, "report.section.fetch_summary") in prepared.markdown
    assert [line for line in prepared.markdown.splitlines() if line.startswith("## ")] == list(
        report_section_headings(DEFAULT_LOCALE)
    )


async def test_optional_previous_snapshot_failure_preserves_report(current_response):
    def broken_previous_loader(response):
        raise OSError("Offline fixture database unavailable")

    prepared = await prepare_report(
        "1592",
        holdings_limit=20,
        big_change_threshold=500,
        service=SuccessfulService(current_response),
        locale=DEFAULT_LOCALE,
        previous_loader=broken_previous_loader,
    )

    assert (
        translate_text(DEFAULT_LOCALE, "report.warning.previous_snapshot_enrichment_unavailable", exception_name="OSError")
        in prepared.markdown
    )
    assert (
        f"{translate_text(DEFAULT_LOCALE, 'report.data_not_available')} ? {translate_text(DEFAULT_LOCALE, 'report.previous_snapshot_unavailable')}"
        in prepared.markdown
    )


def test_copy_button_contains_exact_utf8_payload_and_chatgpt_header():
    payload = CHATGPT_COPY_HEADER + "\n\n# 測試報告\n"
    markup = copy_button_html("Copy for ChatGPT", payload, element_id="copy-chatgpt")
    encoded = re.search(r'atob\("([A-Za-z0-9+/=]+)"\)', markup).group(1)

    assert base64.b64decode(encoded).decode("utf-8") == payload
    assert "Copy for ChatGPT" in markup
    assert "# 測試報告" not in markup

    report_markup = copy_button_html("Copy report", "# Report\n", element_id="copy-report")
    report_encoded = re.search(r'atob\("([A-Za-z0-9+/=]+)"\)', report_markup).group(1)
    assert base64.b64decode(report_encoded).decode("utf-8") == "# Report\n"


def test_streamlit_copy_for_chatgpt_surface_renders_heading_caption_and_actions(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, 'get_ccass_service', lambda: service)

    app = AppTest.from_file('streamlit_app.py').run(timeout=10)
    app.text_input[0].input('1592')
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(
        f"<a id='{localized_report_anchor('copy_for_chatgpt')}'></a>" in block.value
        for block in app.markdown
    )
    assert any(
        translate_text(DEFAULT_LOCALE, 'ui.copy_for_chatgpt') in block.value and block.value.startswith('## ')
        for block in app.markdown
    )
    assert any(
        translate_text(DEFAULT_LOCALE, 'ui.copy_for_chatgpt_caption') in block.value
        for block in app.caption
    )
    assert len(service.calls) == 1


def test_streamlit_abc_shows_validation_error_without_network():
    app = AppTest.from_file("streamlit_app.py").run(timeout=10)
    app.text_input[0].input("abc")
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, "ui.validation_error_prefix") in error.value for error in app.error)

def test_streamlit_query_input_surface_renders_help_caption():
    app = AppTest.from_file("streamlit_app.py").run(timeout=10)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, "ui.sidebar_query_input_caption") in block.value for block in app.caption)
    assert any(translate_text(DEFAULT_LOCALE, "ui.sidebar_stock_code_issue_id") in widget.label for widget in app.text_input)


def test_resolve_streamlit_query_input_supports_issue_id_lookup(tmp_path, current_response):
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    repository.save_response(current_response, source_id="webbsite")

    assert resolve_streamlit_query_input(
        str(current_response.metadata.issue_id),
        "Webb-site Issue ID",
        repository=repository,
    ) == "01592"
    assert resolve_streamlit_query_input("1592", "Stock Code") == "01592"


def test_resolve_streamlit_query_input_rejects_invalid_issue_id(tmp_path):
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")

    with pytest.raises(PlatformError) as excinfo:
        resolve_streamlit_query_input("abc", "Webb-site Issue ID", repository=repository)

    assert excinfo.value.code == ErrorCode.INVALID_SCHEMA
    assert "positive integer" in excinfo.value.message


def test_streamlit_navigation_links_cover_required_sections():
    links = streamlit_navigation_links(DEFAULT_LOCALE)

    assert STREAMLIT_NAV_SECTIONS == streamlit_navigation_sections(DEFAULT_LOCALE)
    assert "#fetch-summary" in links
    assert "#full-summary" in links
    assert "#all-tables" in links
    assert "#dt-rainbow" in links
    assert "#hkex-announcements" in links
    assert "#price-history" in links
    assert "Price & Turnover" in streamlit_navigation_links("en")
    assert "#copy-for-chatgpt" in links
    assert "#downloads" in links


def test_streamlit_issue_id_mode_shows_validation_error_for_invalid_input(tmp_path, monkeypatch, current_response):
    import app.services.ccass as ccass_service

    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    repository.save_response(current_response, source_id="webbsite")
    monkeypatch.setenv("CCASS_SQLITE_PATH", str(tmp_path / "history.db"))

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, "get_ccass_service", lambda: service)

    app = AppTest.from_file("streamlit_app.py").run(timeout=20)
    app.radio[0].set_value("Webb-site Issue ID").run(timeout=20)
    app.text_input[0].input("abc")
    app.button[0].click().run(timeout=20)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, "ui.validation_error_prefix") in error.value for error in app.error)
    assert any("positive integer" in error.value for error in app.error)
    assert len(service.calls) == 0


def test_streamlit_sidebar_controls_cover_required_v1_surface():
    assert STREAMLIT_SIDEBAR_CONTROL_LABELS == streamlit_sidebar_control_labels(DEFAULT_LOCALE)


def test_streamlit_responsive_layout_css_targets_narrow_screens():
    css = streamlit_responsive_layout_css()

    assert '@media (max-width: 768px)' in css
    assert 'section[data-testid="stSidebar"]' in css
    assert 'div[data-testid="stHorizontalBlock"]' in css
    assert 'div[data-testid="column"]' in css
    assert 'overflow-wrap: anywhere' in css


def test_streamlit_chart_help_sections_cover_objective_guidance():
    sections = streamlit_chart_help_sections(DEFAULT_LOCALE)
    sections_en = streamlit_chart_help_sections('en')

    assert len(sections) == 5
    assert sections[0][0] == translate_text(DEFAULT_LOCALE, 'ui.chart_help_rainbow_title')
    assert sections[-1][0] == translate_text(DEFAULT_LOCALE, 'ui.chart_help_cross_check_title')
    assert 'Do not infer buying or selling' in sections_en[0][1]
    assert 'avoid drawing a final conclusion' in sections_en[-1][1]


def test_streamlit_chart_help_surface_renders_help_caption(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, "get_ccass_service", lambda: service)

    app = AppTest.from_file("streamlit_app.py").run(timeout=10)
    app.text_input[0].input("1592")
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, "ui.chart_help_heading") in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, "ui.chart_help_surface_caption") in block.value for block in app.caption)
    assert any(translate_text(DEFAULT_LOCALE, "ui.chart_help_cross_check_title") in block.value for block in app.markdown)


def test_streamlit_hkex_announcements_columns_cover_target_surface():
    assert streamlit_hkex_announcements_columns(DEFAULT_LOCALE) == (
        translate_text(DEFAULT_LOCALE, 'ui.hkex_announcements_table_publish_time'),
        translate_text(DEFAULT_LOCALE, 'ui.hkex_announcements_table_category'),
        translate_text(DEFAULT_LOCALE, 'ui.hkex_announcements_table_title'),
        translate_text(DEFAULT_LOCALE, 'ui.hkex_announcements_table_file_info'),
        translate_text(DEFAULT_LOCALE, 'ui.hkex_announcements_table_official_url'),
        translate_text(DEFAULT_LOCALE, 'ui.hkex_announcements_table_event_tags'),
    )


def test_streamlit_hkex_announcements_surface_renders_empty_state(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, 'get_ccass_service', lambda: service)

    app = AppTest.from_file('streamlit_app.py').run(timeout=10)
    app.text_input[0].input('1592')
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, 'ui.hkex_announcements_heading') in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, 'ui.hkex_announcements_empty') in block.value for block in app.info)
    assert any(translate_text(DEFAULT_LOCALE, 'ui.hkex_announcements_export_heading') in block.value for block in app.markdown)
    assert len(service.calls) == 1


def test_streamlit_company_section_renders_identity_details(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, 'get_ccass_service', lambda: service)

    app = AppTest.from_file('streamlit_app.py').run(timeout=10)
    app.text_input[0].input('1592')
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, 'report.section.company') in block.value for block in app.markdown)
    assert any(
        translate_text(DEFAULT_LOCALE, 'report.company.lookup_status', value=translate_text(DEFAULT_LOCALE, 'report.company.lookup_status.success'))
        in block.value
        for block in app.markdown
    )
    assert any(
        translate_text(DEFAULT_LOCALE, 'report.company.lookup_method', value=translate_text(DEFAULT_LOCALE, 'report.company.lookup_method.extracted_from_url'))
        in block.value
        for block in app.markdown
    )
    assert any(
        translate_text(DEFAULT_LOCALE, 'report.company.metadata_resolution_note') in block.value
        for block in app.markdown
    )
    assert len(service.calls) == 1


def test_streamlit_data_quality_surface_renders_warning_summary(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, 'get_ccass_service', lambda: service)

    app = AppTest.from_file('streamlit_app.py').run(timeout=10)
    app.text_input[0].input('1592')
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, 'ui.data_quality_heading') in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, 'ui.data_quality_help_caption') in block.value for block in app.caption)
    assert any('TEST FIXTURE warning' in block.value for block in app.warning)
    assert len(service.calls) == 1


def test_streamlit_data_quality_surface_renders_empty_state(monkeypatch, previous_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(previous_response)
    monkeypatch.setattr(ccass_service, 'get_ccass_service', lambda: service)

    app = AppTest.from_file('streamlit_app.py').run(timeout=10)
    app.text_input[0].input('1592')
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, 'ui.data_quality_heading') in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, 'ui.data_quality_help_caption') in block.value for block in app.caption)
    assert any(translate_text(DEFAULT_LOCALE, 'ui.data_quality_no_warnings') in block.value for block in app.info)
    assert len(service.calls) == 1


def test_build_full_summary_markdown_renders_status_table(current_response, previous_response):
    prepared = PreparedReport(
        code=current_response.metadata.code,
        markdown='',
        chatgpt_payload='',
        filename='01592_ccass_report.md',
        response=current_response,
        analysis=AnalysisResult(previous_available=True),
    )

    markdown = build_full_summary_markdown(
        prepared,
        history_snapshots=(previous_response,),
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, 'ui.full_summary_table_section') in markdown
    assert translate_text(DEFAULT_LOCALE, 'ui.full_summary_table_status') in markdown
    assert translate_text(DEFAULT_LOCALE, 'ui.full_summary_table_note') in markdown
    assert translate_text(DEFAULT_LOCALE, 'report.section.company').removeprefix('## ') in markdown
    assert translate_text(DEFAULT_LOCALE, 'ui.full_summary_note_changes_available') in markdown
    assert translate_text(DEFAULT_LOCALE, 'ui.full_summary_note_concentration_history', snapshot_count=2) in markdown



def test_streamlit_full_summary_surface_renders_anchor_and_heading(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, 'get_ccass_service', lambda: service)

    app = AppTest.from_file('streamlit_app.py').run(timeout=10)
    app.text_input[0].input('1592')
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(
        f"<a id='{localized_report_anchor('full_summary')}'></a>" in block.value
        for block in app.markdown
    )
    assert any(
        translate_text(DEFAULT_LOCALE, 'ui.full_summary_heading') in block.value
        for block in app.markdown
    )
    assert any(
        translate_text(DEFAULT_LOCALE, 'ui.full_summary_table_section') in block.value
        for block in app.markdown
    )
    assert len(service.calls) == 1


def test_streamlit_all_parsed_tables_surface_renders_heading_and_sections(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, 'get_ccass_service', lambda: service)

    app = AppTest.from_file('streamlit_app.py').run(timeout=10)
    app.text_input[0].input('1592')
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(
        f"<a id='{localized_report_anchor('all_parsed_tables')}'></a>" in block.value
        for block in app.markdown
    )
    assert any(
        translate_text(DEFAULT_LOCALE, 'ui.all_parsed_tables_heading') in block.value
        for block in app.markdown
    )
    assert any(
        translate_text(DEFAULT_LOCALE, 'report.section.holdings') in block.value
        for block in app.markdown
    )
    assert any(
        translate_text(DEFAULT_LOCALE, 'report.section.price_history') in block.value
        for block in app.markdown
    )
    assert len(service.calls) == 1


def test_streamlit_all_tables_surface_renders_anchor_and_heading(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, 'get_ccass_service', lambda: service)

    app = AppTest.from_file('streamlit_app.py').run(timeout=10)
    app.text_input[0].input('1592')
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(
        f"<a id='{localized_report_anchor('all_tables')}'></a>" in block.value
        for block in app.markdown
    )
    assert any(
        f"## {translate_text(DEFAULT_LOCALE, 'nav.all_tables')}" in block.value
        for block in app.markdown
    )
    assert len(service.calls) == 1


def test_streamlit_price_history_surface_renders_unavailable_state(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, 'get_ccass_service', lambda: service)

    app = AppTest.from_file('streamlit_app.py').run(timeout=10)
    app.text_input[0].input('1592')
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, 'report.section.price_history') in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, 'report.price_history.unavailable') in block.value for block in app.markdown)
    assert len(service.calls) == 1


def test_streamlit_concentration_history_surface_renders_history_tables(monkeypatch, tmp_path, current_response, previous_response):
    import app.services.ccass as ccass_service

    repository = NormalizedSnapshotRepository(tmp_path / 'history.db')
    repository.save_response(previous_response, source_id='webbsite')
    repository.save_response(current_response, source_id='webbsite')
    monkeypatch.setenv('CCASS_SQLITE_PATH', str(tmp_path / 'history.db'))

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, 'get_ccass_service', lambda: service)

    app = AppTest.from_file('streamlit_app.py').run(timeout=10)
    app.text_input[0].input('1592')
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, 'report.section.concentration_history') in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, 'report.concentration_history.latest_values') in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, 'report.concentration_history.participant_count_history') in block.value for block in app.markdown)
    assert len(service.calls) == 1


def test_streamlit_report_navigation_links_cover_report_sections():
    from app.streamlit_ui import streamlit_report_navigation_links

    links = streamlit_report_navigation_links(DEFAULT_LOCALE)

    assert '#fetch-summary' in links
    assert '#company' in links
    assert '#metadata' in links
    assert '#data-quality-warnings' in links


def test_build_raw_preview_tables_exposes_summary_and_holdings_rows(current_response):
    tables = build_raw_preview_tables(current_response, locale=DEFAULT_LOCALE)

    assert len(tables) == 2

    summary, holdings = tables
    assert summary.table_index == 0
    assert summary.title == translate_text(DEFAULT_LOCALE, "ui.raw_previews_summary_title")
    assert summary.shape == (9, 2)
    assert summary.columns == (
        translate_text(DEFAULT_LOCALE, "ui.raw_previews_metric"),
        translate_text(DEFAULT_LOCALE, "ui.raw_previews_value"),
    )
    assert summary.sample_rows[0] == {summary.columns[0]: "Code", summary.columns[1]: "01592"}

    assert holdings.table_index == 1
    assert holdings.title == translate_text(DEFAULT_LOCALE, "ui.raw_previews_holdings_title")
    assert holdings.shape == (len(current_response.holdings), 9)
    assert holdings.columns == (
        "Rank",
        "CCASS ID",
        "Participant",
        "Shares",
        "Last change",
        "% issued",
        "% CCASS",
        "Cumulative %",
        "Category",
    )
    assert holdings.sample_rows[0]["Rank"] == 1
    assert holdings.sample_rows[0]["CCASS ID"] == "B00001"


def test_build_raw_preview_tables_uses_localized_no_data_placeholders():
    partial_response = CcassResponse(
        metadata=SourceMetadata(
            code="01592",
            name=None,
            issue_id=1592,
            holdings_date=None,
            fetched_at=datetime(2026, 7, 20, 9, 0, 0),
            source_url="https://example.com/ccass/01592",
        ),
        holdings_summary=HoldingsSummary(
            participant_count=0,
            total_in_ccass_shares=None,
            total_in_ccass_pct_of_issued=None,
            issued_shares=None,
            issued_shares_as_of=None,
            non_ccass_shares=None,
            non_ccass_pct_of_issued=None,
            top5_pct_of_issued=None,
            top10_pct_of_issued=None,
            top5_pct_of_ccass=None,
            top10_pct_of_ccass=None,
        ),
        holdings=[
            HoldingRow(
                rank=1,
                participant_id="B00001",
                participant="Example Participant",
                shares=1000,
                last_change=None,
                pct_of_issued=1.2345,
                pct_of_ccass=None,
                cumulative_pct_of_issued=None,
                participant_category=None,
            )
        ],
    )

    summary, holdings = build_raw_preview_tables(partial_response, locale=DEFAULT_LOCALE)

    assert summary.sample_rows[1][summary.columns[1]] == translate_text(DEFAULT_LOCALE, "report.data_not_available")
    assert summary.sample_rows[3][summary.columns[1]] == translate_text(DEFAULT_LOCALE, "report.data_not_available")
    assert holdings.sample_rows[0]["Last change"] == translate_text(DEFAULT_LOCALE, "report.data_not_available")
    assert holdings.sample_rows[0]["Category"] == translate_text(DEFAULT_LOCALE, "report.data_not_available")


def test_build_download_artifacts_exposes_combined_csv_and_workbook(current_response):
    artifacts = build_download_artifacts(current_response)

    assert artifacts.combined_csv_filename == "01592_all_ccass_data.csv"
    assert artifacts.workbook_filename == "01592_all_sections.xlsx"
    assert artifacts.raw_preview_summary_filename == "01592_raw_preview_summary.csv"
    assert artifacts.raw_preview_holdings_filename == "01592_raw_preview_holdings.csv"
    assert artifacts.combined_csv_preview.splitlines()[0].startswith("code,")
    assert artifacts.combined_csv_preview.splitlines()[1].split(",")[0] == "01592"

    with zipfile.ZipFile(BytesIO(artifacts.workbook_bytes)) as workbook_archive:
        workbook_xml = ET.fromstring(workbook_archive.read("xl/workbook.xml"))

    namespace = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    sheet_names = [
        sheet.attrib["name"]
        for sheet in workbook_xml.findall("a:sheets/a:sheet", namespace)
    ]
    assert sheet_names == [
        "Combined CSV",
        "Report Metadata",
        "Raw Preview Summary",
        "Raw Preview Holdings",
    ]


def test_build_download_artifacts_uses_localized_no_data_placeholders():
    partial_response = CcassResponse(
        metadata=SourceMetadata(
            code="01592",
            name=None,
            issue_id=1592,
            holdings_date=None,
            fetched_at=datetime(2026, 7, 20, 9, 0, 0),
            source_url="https://example.com/ccass/01592",
        ),
        holdings_summary=HoldingsSummary(
            participant_count=0,
            total_in_ccass_shares=None,
            total_in_ccass_pct_of_issued=None,
            issued_shares=None,
            issued_shares_as_of=None,
            non_ccass_shares=None,
            non_ccass_pct_of_issued=None,
            top5_pct_of_issued=None,
            top10_pct_of_issued=None,
            top5_pct_of_ccass=None,
            top10_pct_of_ccass=None,
        ),
        holdings=[
            HoldingRow(
                rank=1,
                participant_id="B00001",
                participant="Example Participant",
                shares=1000,
                last_change=None,
                pct_of_issued=1.2345,
                pct_of_ccass=None,
                cumulative_pct_of_issued=None,
                participant_category=None,
            )
        ],
    )

    artifacts = build_download_artifacts(partial_response, locale=DEFAULT_LOCALE)
    preview_summary = artifacts.raw_preview_summary_bytes.decode("utf-8-sig")
    preview_holdings = artifacts.raw_preview_holdings_bytes.decode("utf-8-sig")

    assert translate_text(DEFAULT_LOCALE, "report.data_not_available") in preview_summary
    assert translate_text(DEFAULT_LOCALE, "report.data_not_available") in preview_holdings

def test_streamlit_raw_previews_surface_renders_help_caption(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, "get_ccass_service", lambda: service)

    app = AppTest.from_file("streamlit_app.py").run(timeout=10)
    app.text_input[0].input("1592")
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, "ui.raw_previews_heading") in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, "ui.raw_previews_help_caption") in block.value for block in app.caption)
    assert any(translate_text(DEFAULT_LOCALE, "ui.raw_previews_expander") in block.label for block in app.expander)

def test_streamlit_downloads_surface_renders_combined_csv_and_workbook(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, "get_ccass_service", lambda: service)

    app = AppTest.from_file("streamlit_app.py").run(timeout=10)
    app.text_input[0].input("1592")
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any(translate_text(DEFAULT_LOCALE, "ui.downloads_heading") in block.value for block in app.markdown)
    assert any("匯出流程" in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, "ui.downloads_workflow_caption") in block.value for block in app.caption)
    assert any(translate_text(DEFAULT_LOCALE, "ui.downloads_caption") in block.value for block in app.caption)
    download_labels = [button.label for button in app.download_button]
    assert translate_text(DEFAULT_LOCALE, "ui.downloads_download_combined_csv") in download_labels
    assert translate_text(DEFAULT_LOCALE, "ui.downloads_download_excel_workbook") in download_labels
    assert translate_text(DEFAULT_LOCALE, "ui.downloads_download_markdown_report") in download_labels
    assert any(translate_text(DEFAULT_LOCALE, "ui.downloads_report_markdown") in block.value for block in app.markdown)
    assert any("前 80 行 CSV" in block.value for block in app.caption)
    assert any("各章節下載" in block.label for block in app.expander)
    assert any("原始預覽摘要 CSV" in block.value for block in app.markdown)


def test_streamlit_locale_switch_rerenders_without_refetch(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    service = SuccessfulService(current_response)
    monkeypatch.setattr(ccass_service, "get_ccass_service", lambda: service)

    app = AppTest.from_file("streamlit_app.py").run(timeout=10)
    app.text_input[0].input("1592")
    app.button[0].click().run(timeout=10)

    assert len(service.calls) == 1
    assert any(translate_text(DEFAULT_LOCALE, "ui.raw_previews_heading") in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, "ui.chart_help_heading") in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, "report.section.concentration_history") in block.value for block in app.markdown)
    assert any(translate_text(DEFAULT_LOCALE, "report.section.price_history") in block.value for block in app.markdown)

    try:
        app.selectbox[0].select("en").run(timeout=10)
    except Exception:
        try:
            app.selectbox[0].select("English").run(timeout=10)
        except Exception:
            app.session_state["locale"] = "en"
            app.run(timeout=10)

    assert len(service.calls) == 1
    assert any(translate_text('en', 'ui.sidebar_query_input_caption') in block.value for block in app.caption)
    assert any("## Fetch Summary" in block.value for block in app.markdown)
    assert any(translate_text('en', 'ui.chart_help_heading') in block.value for block in app.markdown)
    assert any(translate_text('en', 'ui.chart_help_surface_caption') in block.value for block in app.caption)
    assert any(button.label == "Download All CCASS Data CSV" for button in app.download_button)
    assert any(button.label == "Download Markdown Report" for button in app.download_button)


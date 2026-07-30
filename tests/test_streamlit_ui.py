import base64
import re
import zipfile
from io import BytesIO
from xml.etree import ElementTree as ET

from streamlit.testing.v1 import AppTest

from app.errors import ErrorCode, PlatformError
from app.streamlit_ui import (
    STREAMLIT_NAV_SECTIONS,
    STREAMLIT_SIDEBAR_CONTROL_LABELS,
    build_download_artifacts,
    build_raw_preview_tables,
    copy_button_html,
    prepare_report,
    resolve_streamlit_query_input,
    streamlit_navigation_links,
)
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.report import CHATGPT_COPY_HEADER, SECTION_HEADINGS


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
    assert progress[-1] == (100, "Report ready")


async def test_prepare_report_network_failure_keeps_all_sections():
    prepared = await prepare_report(
        "1592",
        holdings_limit=20,
        big_change_threshold=500,
        service=FailingService(),
    )

    assert prepared.fetch_error.startswith("SOURCE_UNAVAILABLE:")
    assert "## Fetch Summary" in prepared.markdown
    assert [line for line in prepared.markdown.splitlines() if line.startswith("## ")] == list(
        SECTION_HEADINGS
    )


async def test_optional_previous_snapshot_failure_preserves_report(current_response):
    def broken_previous_loader(response):
        raise OSError("Offline fixture database unavailable")

    prepared = await prepare_report(
        "1592",
        holdings_limit=20,
        big_change_threshold=500,
        service=SuccessfulService(current_response),
        previous_loader=broken_previous_loader,
    )

    assert "Previous-snapshot enrichment is unavailable (OSError)." in prepared.markdown
    assert "DATA NOT AVAILABLE — No previous snapshot was supplied" in prepared.markdown


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


def test_streamlit_abc_shows_validation_error_without_network():
    app = AppTest.from_file("streamlit_app.py").run(timeout=10)
    app.text_input[0].input("abc")
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any("Validation error" in error.value for error in app.error)


def test_resolve_streamlit_query_input_supports_issue_id_lookup(tmp_path, current_response):
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    repository.save_response(current_response, source_id="webbsite")

    assert resolve_streamlit_query_input(
        str(current_response.metadata.issue_id),
        "Webb-site Issue ID",
        repository=repository,
    ) == "01592"
    assert resolve_streamlit_query_input("1592", "Stock Code") == "01592"


def test_streamlit_navigation_links_cover_required_sections():
    links = streamlit_navigation_links()

    assert STREAMLIT_NAV_SECTIONS == (
        "Fetch Summary",
        "All Tables",
        "DT Rainbow",
        "HKEX Announcements",
        "Company",
        "Holdings",
        "Changes",
        "Big Changes",
        "Concentration",
        "Price",
        "Raw Previews",
        "Copy for ChatGPT",
        "Downloads",
    )
    assert "#fetch-summary" in links
    assert "#all-tables" in links
    assert "#dt-rainbow" in links
    assert "#hkex-announcements" in links
    assert "#copy-for-chatgpt" in links
    assert "#downloads" in links


def test_streamlit_sidebar_controls_cover_required_v1_surface():
    assert STREAMLIT_SIDEBAR_CONTROL_LABELS == (
        "Input Type",
        "Stock Code / Issue ID",
        "Timeout",
        "Announcement Period",
        "Source Mode",
        "Data Date",
        "History Range",
        "Top N",
        "Percentage Basis",
        "Fetch",
    )

def test_build_raw_preview_tables_exposes_summary_and_holdings_rows(current_response):
    tables = build_raw_preview_tables(current_response)

    assert len(tables) == 2

    summary, holdings = tables
    assert summary.table_index == 0
    assert summary.title == "Parsed Holdings Summary"
    assert summary.shape == (9, 2)
    assert summary.columns == ("Metric", "Value")
    assert summary.sample_rows[0] == {"Metric": "Code", "Value": "01592"}

    assert holdings.table_index == 1
    assert holdings.title == "Parsed Holdings Table"
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


def test_streamlit_downloads_surface_renders_combined_csv_and_workbook(monkeypatch, current_response):
    import app.services.ccass as ccass_service

    monkeypatch.setattr(ccass_service, "get_ccass_service", lambda: SuccessfulService(current_response))

    app = AppTest.from_file("streamlit_app.py").run(timeout=10)
    app.text_input[0].input("1592")
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any("Downloads" in block.value for block in app.markdown)
    download_labels = [button.label for button in app.download_button]
    assert "Download combined CSV" in download_labels
    assert "Download Excel workbook" in download_labels

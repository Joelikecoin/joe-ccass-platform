import base64
import re

from streamlit.testing.v1 import AppTest

from app.errors import ErrorCode, PlatformError
from app.streamlit_ui import copy_button_html, prepare_report
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

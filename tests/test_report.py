from app.errors import ErrorCode, PlatformError
from ccass_core.compute import compute_analysis
from ccass_core.report import (
    CHATGPT_COPY_HEADER,
    SECTION_HEADINGS,
    build_chatgpt_copy_payload,
    build_markdown_report,
)


def test_report_has_required_sections_in_exact_order(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    report = build_markdown_report(current_response, code="01592", analysis=analysis)

    assert report.startswith("# CCASS Report — 01592 TEST FIXTURE — GOLDEN STOCK\n")
    positions = [report.index(heading) for heading in SECTION_HEADINGS]
    assert positions == sorted(positions)
    assert [line for line in report.splitlines() if line.startswith("## ")] == list(
        SECTION_HEADINGS
    )


def test_network_failure_report_is_readable_and_keeps_fetch_summary():
    error = PlatformError(
        ErrorCode.SOURCE_TIMEOUT,
        "Both mirror requests timed out.",
        retry_recommended=True,
    )
    report = build_markdown_report(None, code="01592", fetch_error=f"{error.code}: {error.message}")

    assert "## Fetch Summary" in report
    assert "DATA NOT AVAILABLE — SOURCE_TIMEOUT: Both mirror requests timed out." in report
    assert [line for line in report.splitlines() if line.startswith("## ")] == list(
        SECTION_HEADINGS
    )


def test_chatgpt_copy_payload_has_safety_header_and_complete_report(current_response):
    report = build_markdown_report(current_response, code="01592")
    payload = build_chatgpt_copy_payload(report)

    assert payload.startswith(CHATGPT_COPY_HEADER + "\n\n# CCASS Report")
    assert payload.endswith(report)
    assert "not proof of beneficial ownership" in payload

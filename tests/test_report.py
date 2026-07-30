import warnings

from app.errors import ErrorCode, PlatformError
from ccass_core.compute import compute_analysis
from ccass_core.report import (
    CHATGPT_COPY_HEADER,
    DEFAULT_LOCALE,
    TRANSLATION_REGISTRY,
    build_chatgpt_copy_payload,
    build_markdown_report,
    report_section_headings,
    translate_text,
)


def test_report_has_required_sections_in_exact_order(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    report = build_markdown_report(current_response, code="01592", analysis=analysis, locale=DEFAULT_LOCALE)

    assert report.startswith(f"# {translate_text(DEFAULT_LOCALE, 'report.title')} ? 01592 ")
    positions = [report.index(heading) for heading in report_section_headings(DEFAULT_LOCALE)]
    assert positions == sorted(positions)
    assert [line for line in report.splitlines() if line.startswith("## ")] == list(
        report_section_headings(DEFAULT_LOCALE)
    )


def test_report_supports_english_locale(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    report = build_markdown_report(current_response, code="01592", analysis=analysis, locale="en")

    assert report.startswith("# CCASS Report ? 01592 ")
    assert [line for line in report.splitlines() if line.startswith("## ")] == list(
        report_section_headings("en")
    )


def test_network_failure_report_is_readable_and_keeps_fetch_summary():
    error = PlatformError(
        ErrorCode.SOURCE_TIMEOUT,
        "Both mirror requests timed out.",
        retry_recommended=True,
    )
    report = build_markdown_report(
        None,
        code="01592",
        fetch_error=f"{error.code}: {error.message}",
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "report.section.fetch_summary") in report
    assert (
        f"{translate_text(DEFAULT_LOCALE, 'report.data_not_available')} ? SOURCE_TIMEOUT: Both mirror requests timed out."
        in report
    )
    assert [line for line in report.splitlines() if line.startswith("## ")] == list(
        report_section_headings(DEFAULT_LOCALE)
    )


def test_chatgpt_copy_payload_has_safety_header_and_complete_report(current_response):
    report = build_markdown_report(current_response, code="01592", locale=DEFAULT_LOCALE)
    payload = build_chatgpt_copy_payload(report)

    assert payload.startswith(CHATGPT_COPY_HEADER + f"\n\n# {translate_text(DEFAULT_LOCALE, 'report.title')} ?")
    assert payload.endswith(report)
    assert "not proof of beneficial ownership" in payload


def test_translate_text_falls_back_to_english_with_warning(monkeypatch):
    monkeypatch.setitem(TRANSLATION_REGISTRY["en"], "test.fallback.key", "English fallback")
    monkeypatch.delitem(TRANSLATION_REGISTRY["zh_HK"], "test.fallback.key", raising=False)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = translate_text("zh_HK", "test.fallback.key")

    assert value == "English fallback"
    assert any("falling back to English" in str(warning.message) for warning in caught)

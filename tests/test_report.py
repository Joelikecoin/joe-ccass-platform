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

    assert report.startswith(f"# {translate_text(DEFAULT_LOCALE, 'report.title')}")
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


def test_report_includes_company_section_identity_details(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    report = build_markdown_report(current_response, code="01592", analysis=analysis, locale=DEFAULT_LOCALE)

    assert translate_text(DEFAULT_LOCALE, "report.section.company") in report
    assert translate_text(DEFAULT_LOCALE, "report.metadata.stock_name", value=current_response.metadata.name) in report
    assert translate_text(DEFAULT_LOCALE, "report.metadata.code", value=current_response.metadata.code) in report
    assert translate_text(DEFAULT_LOCALE, "report.metadata.issue_id", value=current_response.metadata.issue_id) in report
    assert translate_text(
        DEFAULT_LOCALE,
        "report.company.lookup_status",
        value=translate_text(DEFAULT_LOCALE, "report.company.lookup_status.success"),
    ) in report
    assert translate_text(
        DEFAULT_LOCALE,
        "report.company.lookup_method",
        value=translate_text(DEFAULT_LOCALE, "report.company.lookup_method.extracted_from_url"),
    ) in report
    assert translate_text(DEFAULT_LOCALE, "report.company.metadata_resolution_note") in report
    assert translate_text(DEFAULT_LOCALE, "report.section.metadata") in report
    assert translate_text(DEFAULT_LOCALE, "report.metadata.attribution", value=current_response.metadata.attribution) in report


def test_report_includes_data_quality_warning_summary(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    report = build_markdown_report(current_response, code="01592", analysis=analysis, locale=DEFAULT_LOCALE)

    assert translate_text(DEFAULT_LOCALE, "report.section.data_quality_warnings") in report
    assert "TEST FIXTURE warning" in report


def test_report_includes_price_history_surface_as_unavailable(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    report = build_markdown_report(current_response, code="01592", analysis=analysis, locale=DEFAULT_LOCALE)

    assert translate_text(DEFAULT_LOCALE, "report.section.price_history") in report
    assert translate_text(DEFAULT_LOCALE, "report.price_history.unavailable") in report


def test_report_includes_concentration_history_surface_from_snapshots(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    report = build_markdown_report(
        current_response,
        code="01592",
        analysis=analysis,
        history_snapshots=(previous_response,),
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "report.section.concentration_history") in report
    assert translate_text(DEFAULT_LOCALE, "report.concentration_history.latest_values") in report
    assert translate_text(DEFAULT_LOCALE, "report.concentration_history.participant_count_history") in report
    assert "2026-07-19" in report and "2026-07-20" in report


def test_report_states_no_data_quality_warnings_when_empty(previous_response, current_response):
    analysis = compute_analysis(previous_response, current_response, big_change_threshold=500)
    report = build_markdown_report(previous_response, code="01592", analysis=analysis, locale=DEFAULT_LOCALE)

    assert translate_text(DEFAULT_LOCALE, "report.no_additional_warning") in report


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

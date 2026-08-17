import warnings
from datetime import UTC, datetime

from app.errors import ErrorCode, PlatformError
from app.models import (
    AnnouncementRow,
    AnnouncementsMetadata,
    AnnouncementsResponse,
    CapitalInformationMetadata,
    CapitalInformationResponse,
    OfficerRow,
    OfficersMetadata,
    OfficersResponse,
    PriceHistoryMetadata,
    PriceHistoryResponse,
    PriceHistoryRow,
)
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


def test_report_zh_hk_translations_do_not_return_placeholder_marks():
    assert "?" not in translate_text("zh_HK", "ui.app_title")
    assert "?" not in translate_text("zh_HK", "report.metadata.issue_id", value=15920)


def _ready_officers_response() -> OfficersResponse:
    return OfficersResponse(
        metadata=OfficersMetadata(
            code="01351",
            name="輝煌明天",
            source_name="同花順 F10 managers",
            source_url="https://stockpage.10jqka.com.cn/basicweb/176/HK1351/manager.html",
            fetched_at=datetime(2026, 7, 21, 9, 0, tzinfo=UTC),
            data_as_of=None,
            officers_count=1,
            source_status="ready",
        ),
        officers=[
            OfficerRow(
                name="董晖",
                positions=["主席", "执行董事", "行政总裁"],
                tenure_from=None,
                tenure_to=None,
                is_current=True,
                sex="男",
                age=39,
                education="本科",
                salary="178.80万",
                biography="董晖先生，于2018年11月8日获委任。",
            )
        ],
        data_quality_warnings=[],
    )


def test_report_renders_ready_officers_source_note(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    report = build_markdown_report(
        current_response,
        code="01592",
        analysis=analysis,
        officers=_ready_officers_response(),
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "ui.officers_source_ready") in report
    assert "董晖" in report


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
    assert translate_text(
        DEFAULT_LOCALE,
        "report.fetch.data_as_of",
        value=current_response.metadata.data_as_of,
    ) in report


def test_report_includes_company_information_sections_as_unavailable(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    report = build_markdown_report(current_response, code="01592", analysis=analysis, locale=DEFAULT_LOCALE)

    assert translate_text(DEFAULT_LOCALE, "report.section.announcements") in report
    assert translate_text(DEFAULT_LOCALE, "report.section.stock_events") in report
    assert translate_text(DEFAULT_LOCALE, "report.section.capital_information") in report
    assert translate_text(DEFAULT_LOCALE, "report.section.officers") in report
    assert translate_text(DEFAULT_LOCALE, "ui.hkex_announcements_unavailable") in report
    assert translate_text(DEFAULT_LOCALE, "ui.stock_events_unavailable") in report
    assert translate_text(DEFAULT_LOCALE, "ui.capital_information_unavailable") in report
    assert translate_text(DEFAULT_LOCALE, "ui.officers_unavailable") in report


def test_report_includes_related_context_hints(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    report = build_markdown_report(current_response, code="01592", analysis=analysis, locale=DEFAULT_LOCALE)

    assert translate_text(DEFAULT_LOCALE, "ui.related_context_caption") in report
    assert translate_text(DEFAULT_LOCALE, "ui.related_context_company") in report
    assert translate_text(DEFAULT_LOCALE, "ui.related_context_movement") in report
    assert translate_text(DEFAULT_LOCALE, "ui.related_context_history") in report
    assert translate_text(DEFAULT_LOCALE, "ui.related_context_operations") in report
    assert "(#announcements)" in report
    assert "(#stock-events)" in report
    assert "(#capital-information)" in report
    assert "(#officers)" in report
    assert "(#holdings)" in report
    assert "(#broker-distribution)" in report
    assert "(#changes)" in report
    assert "(#big-changes)" in report
    assert "(#concentration)" in report
    assert "(#concentration-history)" in report
    assert "(#price-history)" in report
    assert "(#metadata)" in report
    assert "(#fetch-summary)" in report
    assert "(#data-quality-warnings)" in report


def test_report_includes_announcements_surface_when_available(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    announcements = AnnouncementsResponse(
        metadata=AnnouncementsMetadata(
            code="01592",
            name="TEST FIXTURE ??GOLDEN STOCK",
            source_name="HKEXnews",
            source_url="https://www1.hkexnews.hk/search/titlesearch.xhtml?category=0&lang=EN&market=SEHK&stockId=189695",
            fetched_at=current_response.metadata.fetched_at,
            earliest_announcement_date=current_response.metadata.holdings_date,
            latest_announcement_date=current_response.metadata.holdings_date,
            announcement_count=1,
        ),
        announcements=[
            AnnouncementRow(
                announcement_date=current_response.metadata.holdings_date,
                title="Sample HKEX announcement",
                source="HKEXnews",
                link="https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0720/2026072000123.pdf",
            )
        ],
    )
    report = build_markdown_report(
        current_response,
        code="01592",
        analysis=analysis,
        announcements=announcements,
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "report.section.announcements") in report
    assert "Sample HKEX announcement" in report
    assert "HKEXnews" in report
    assert "2026-07-20" in report
    assert "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0720/2026072000123.pdf" in report


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


def test_report_includes_price_history_surface_when_available(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    price_history = PriceHistoryResponse(
        metadata=PriceHistoryMetadata(
            code="01592",
            name="Sample Company",
            ticker="01592.HK",
            price_date_from=current_response.metadata.holdings_date,
            price_date_to=current_response.metadata.holdings_date,
            source_name="Yahoo Finance",
            source_url="https://query1.finance.yahoo.com/v8/finance/chart/01592.HK",
            fetched_at=current_response.metadata.fetched_at,
            adjustment_state="adjusted",
            currency="HKD",
            adjustment_note="Adjusted close values are available from Yahoo Finance.",
        ),
        prices=[
            PriceHistoryRow(
                price_date=current_response.metadata.holdings_date,
                open=1.0,
                high=1.1,
                low=0.9,
                close=1.05,
                adjusted_close=1.01,
                volume=1000,
                turnover=1050.0,
            )
        ],
    )
    report = build_markdown_report(
        current_response,
        code="01592",
        analysis=analysis,
        price_history=price_history,
        locale=DEFAULT_LOCALE,
    )

    assert translate_text(DEFAULT_LOCALE, "report.section.price_history") in report
    assert translate_text(DEFAULT_LOCALE, "report.price_history.metadata_heading") in report
    assert translate_text(DEFAULT_LOCALE, "report.price_history.table_heading") in report
    assert translate_text(DEFAULT_LOCALE, "report.price_history.unavailable") not in report
    assert "Yahoo Finance" in report
    assert current_response.metadata.holdings_date.isoformat() in report


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
    assert "Visual" in report
    assert translate_text(DEFAULT_LOCALE, "report.concentration_history.participant_count_history") in report
    assert "2026-07-19" in report and "2026-07-20" in report


def test_report_includes_broker_distribution_surface_from_holdings(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response, big_change_threshold=500)
    report = build_markdown_report(current_response, code="01592", analysis=analysis, locale=DEFAULT_LOCALE)

    assert translate_text(DEFAULT_LOCALE, "report.section.broker_distribution") in report
    assert translate_text(DEFAULT_LOCALE, "report.broker_distribution.summary_participant_count") in report
    assert translate_text(DEFAULT_LOCALE, "report.broker_distribution.top_brokers_heading") in report
    assert translate_text(DEFAULT_LOCALE, "report.broker_distribution.table_visual") in report
    assert "TEST FIXTURE BROKER ONE" in report
    assert "TEST FIXTURE BROKER TWO" in report
    assert translate_text(DEFAULT_LOCALE, "report.broker_distribution.visual_note") in report


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

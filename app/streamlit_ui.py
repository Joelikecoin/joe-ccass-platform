import base64
import csv
import html
import io
import re
import tempfile
import warnings
from datetime import date
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import zipfile
from xml.sax.saxutils import escape as xml_escape

from app.errors import ErrorCode, PlatformError
from app.data_quality import structured_warning, warning_code
from app.models import (
    AnnouncementsResponse,
    CapitalInformationResponse,
    CcassResponse,
    OfficersResponse,
    PriceHistoryResponse,
    StockEventsResponse,
)
from app.services.announcements import get_announcements_service
from app.services.capital_information import get_capital_information_service
from app.services.officers import get_officers_service
from app.services.stock_events import get_stock_events_service
from app.services.price_history import get_price_history_service
from app.sources.registry import WEBBSITE_SOURCE_ID
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.collector import export_latest_csv
from ccass_core.compute import AnalysisResult, compute_analysis
from ccass_core.normalize import normalize_stock_code
from ccass_core.report import (
    DEFAULT_LOCALE,
    REPORT_SECTION_KEYS,
    SUPPORTED_LOCALES,
    build_chatgpt_copy_payload,
    build_markdown_report,
    localized_report_anchor,
    report_filename,
    report_section_headings,
    translate_text,
)

NAV_SECTION_KEYS = (
    "full_summary",
    "company",
    "metadata",
    "fetch_summary",
    "all_tables",
    "dt_rainbow",
    "hkex_announcements",
    "stock_events",
    "capital_information",
    "officers",
    "holdings",
    "changes",
    "big_changes",
    "concentration",
    "price",
    "raw_previews",
    "copy_for_chatgpt",
    "downloads",
)

STREAMLIT_NAV_SECTIONS = tuple(
    translate_text(DEFAULT_LOCALE, f"nav.{key}") for key in NAV_SECTION_KEYS
)
STREAMLIT_SIDEBAR_CONTROL_LABELS = (
    translate_text(DEFAULT_LOCALE, "ui.sidebar_input_type"),
    translate_text(DEFAULT_LOCALE, "ui.sidebar_stock_code_issue_id"),
    translate_text(DEFAULT_LOCALE, "ui.sidebar_timeout"),
    translate_text(DEFAULT_LOCALE, "ui.sidebar_announcement_period"),
    translate_text(DEFAULT_LOCALE, "ui.sidebar_source_mode"),
    translate_text(DEFAULT_LOCALE, "ui.sidebar_data_date"),
    translate_text(DEFAULT_LOCALE, "ui.sidebar_history_range"),
    translate_text(DEFAULT_LOCALE, "ui.sidebar_top_n"),
    translate_text(DEFAULT_LOCALE, "ui.sidebar_percentage_basis"),
    translate_text(DEFAULT_LOCALE, "ui.fetch"),
)

STREAMLIT_SOURCE_MODES = ("auto", "webbsite", "google_drive_csv")
STREAMLIT_ANNOUNCEMENT_PERIODS = ("All", "7 days", "30 days", "90 days")
STREAMLIT_HISTORY_RANGES = ("Latest", "7 days", "30 days", "90 days", "Custom")
STREAMLIT_PERCENTAGE_BASES = ("CCASS", "Issued Shares")
HOLDINGS_PREVIEW_COLUMNS = (
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


class StockDataService(Protocol):
    async def get_stock_data(
        self, code: str | int, holdings_limit: int = 15
    ) -> CcassResponse: ...


@dataclass(frozen=True, slots=True)
class PreparedReport:
    code: str
    markdown: str
    chatgpt_payload: str
    filename: str
    response: CcassResponse | None
    analysis: AnalysisResult | None = None
    announcements: AnnouncementsResponse | None = None
    stock_events: StockEventsResponse | None = None
    capital_information: CapitalInformationResponse | None = None
    officers: OfficersResponse | None = None
    price_history: PriceHistoryResponse | None = None
    fetch_error: str | None = None


@dataclass(frozen=True, slots=True)
class RawPreviewTable:
    table_index: int
    title: str
    shape: tuple[int, int]
    columns: tuple[str, ...]
    sample_rows: tuple[dict[str, object], ...]


@dataclass(frozen=True, slots=True)
class DownloadArtifacts:
    combined_csv_bytes: bytes
    combined_csv_filename: str
    combined_csv_preview: str
    workbook_bytes: bytes
    workbook_filename: str
    raw_preview_summary_bytes: bytes
    raw_preview_summary_filename: str
    raw_preview_holdings_bytes: bytes
    raw_preview_holdings_filename: str


async def prepare_report(
    raw_code: str,
    *,
    holdings_limit: int,
    big_change_threshold: int,
    service: StockDataService,
    locale: str = DEFAULT_LOCALE,
    history_snapshots: Sequence[CcassResponse] | None = None,
    previous_loader: Callable[[CcassResponse], CcassResponse | None] | None = None,
    announcements_enabled: bool = False,
    announcement_start_date: date | None = None,
    announcement_end_date: date | None = None,
    price_history_enabled: bool = False,
    price_history_start_date: date | None = None,
    price_history_end_date: date | None = None,
    progress: Callable[[int, str], None] | None = None,
) -> PreparedReport:
    code = normalize_stock_code(raw_code)
    _progress(progress, 15, ui_text(locale, "progress_validated_stock_code"))
    try:
        _progress(progress, 30, ui_text(locale, "progress_fetching_source"))
        response = await service.get_stock_data(code, holdings_limit=holdings_limit)
    except PlatformError as exc:
        error = f"{exc.code}: {exc.message}"
        _progress(progress, 75, ui_text(locale, "progress_source_unavailable"))
        markdown = build_markdown_report(None, code=code, fetch_error=error, locale=locale)
        _progress(progress, 100, ui_text(locale, "progress_ready_with_error_details"))
        return PreparedReport(
            code=code,
            markdown=markdown,
            chatgpt_payload=build_chatgpt_copy_payload(markdown),
            filename=report_filename(code),
            response=None,
            fetch_error=error,
        )

    _progress(progress, 65, ui_text(locale, "progress_computing_analysis"))
    try:
        previous = previous_loader(response) if previous_loader else None
    except Exception as exc:
        response.data_quality_warnings.append(
            structured_warning(
                "DATA_LIMITATION",
                "PREVIOUS_SNAPSHOT_ENRICHMENT_UNAVAILABLE",
                f"Previous-snapshot enrichment is unavailable ({type(exc).__name__}).",
            )
        )
        previous = None
    announcements: AnnouncementsResponse | None = None
    stock_events: StockEventsResponse | None = None
    capital_information: CapitalInformationResponse | None = None
    officers: OfficersResponse | None = None
    price_history: PriceHistoryResponse | None = None
    if announcements_enabled:
        try:
            announcements = await get_announcements_service().get_announcements(
                code,
                start_date=announcement_start_date,
                end_date=announcement_end_date,
            )
        except PlatformError as exc:
            response.data_quality_warnings.append(
                structured_warning(
                    "DATA_LIMITATION",
                    "ANNOUNCEMENTS_UNAVAILABLE",
                    f"Announcements are unavailable ({exc.code}: {exc.message}).",
                )
            )
        except Exception as exc:
            response.data_quality_warnings.append(
                structured_warning(
                    "DATA_LIMITATION",
                    "ANNOUNCEMENTS_UNAVAILABLE",
                    f"Announcements are unavailable ({type(exc).__name__}).",
                )
            )
    try:
        stock_events = await get_stock_events_service().get_stock_events(code)
    except PlatformError as exc:
        stock_events = None
        response.data_quality_warnings.append(
            structured_warning(
                "DATA_LIMITATION",
                "STOCK_EVENTS_UNAVAILABLE",
                f"Stock events are unavailable ({exc.code}: {exc.message}).",
            )
        )
    except Exception as exc:
        stock_events = None
        response.data_quality_warnings.append(
            structured_warning(
                "DATA_LIMITATION",
                "STOCK_EVENTS_UNAVAILABLE",
                f"Stock events are unavailable ({type(exc).__name__}).",
            )
        )
    else:
        response.data_quality_warnings.extend(stock_events.data_quality_warnings)
    try:
        capital_information = await get_capital_information_service().get_capital_information(code)
    except PlatformError as exc:
        capital_information = None
        response.data_quality_warnings.append(
            structured_warning(
                "DATA_LIMITATION",
                "CAPITAL_INFORMATION_UNAVAILABLE",
                f"Capital information is unavailable ({exc.code}: {exc.message}).",
            )
        )
    except Exception as exc:
        capital_information = None
        response.data_quality_warnings.append(
            structured_warning(
                "DATA_LIMITATION",
                "CAPITAL_INFORMATION_UNAVAILABLE",
                f"Capital information is unavailable ({type(exc).__name__}).",
            )
        )
    else:
        response.data_quality_warnings.extend(capital_information.data_quality_warnings)
    try:
        officers = await get_officers_service().get_officers(code)
    except PlatformError as exc:
        officers = None
        response.data_quality_warnings.append(
            structured_warning(
                "DATA_LIMITATION",
                "OFFICERS_UNAVAILABLE",
                f"Officers are unavailable ({exc.code}: {exc.message}).",
            )
        )
    except Exception as exc:
        officers = None
        response.data_quality_warnings.append(
            structured_warning(
                "DATA_LIMITATION",
                "OFFICERS_UNAVAILABLE",
                f"Officers are unavailable ({type(exc).__name__}).",
            )
        )
    else:
        response.data_quality_warnings.extend(officers.data_quality_warnings)
    if price_history_enabled:
        try:
            price_history = await get_price_history_service().get_price_history(
                code,
                start_date=price_history_start_date,
                end_date=price_history_end_date,
            )
        except PlatformError as exc:
            response.data_quality_warnings.append(
                structured_warning(
                    "DATA_LIMITATION",
                    "PRICE_HISTORY_UNAVAILABLE",
                    f"Price history is unavailable ({exc.code}: {exc.message}).",
                )
            )
        except Exception as exc:
            response.data_quality_warnings.append(
                structured_warning(
                    "DATA_LIMITATION",
                    "PRICE_HISTORY_UNAVAILABLE",
                    f"Price history is unavailable ({type(exc).__name__}).",
                )
            )
        else:
            response.data_quality_warnings.extend(price_history.data_quality_warnings)
    analysis = compute_analysis(
        response,
        previous=previous,
        big_change_threshold=big_change_threshold,
    )
    _progress(progress, 85, ui_text(locale, "progress_rendering_report"))
    markdown = build_markdown_report(
        response,
        code=code,
        analysis=analysis,
        history_snapshots=history_snapshots,
        announcements=announcements,
        stock_events=stock_events,
        capital_information=capital_information,
        officers=officers,
        price_history=price_history,
        locale=locale,
    )
    _progress(progress, 100, ui_text(locale, "progress_ready"))
    return PreparedReport(
        code=code,
        markdown=markdown,
        chatgpt_payload=build_chatgpt_copy_payload(markdown),
        filename=report_filename(code),
        response=response,
        analysis=analysis,
        announcements=announcements,
        stock_events=stock_events,
        capital_information=capital_information,
        officers=officers,
        price_history=price_history,
    )


def ui_text(locale: str, key: str, /, **values: object) -> str:
    return translate_text(locale, f"ui.{key}", **values)


def nav_text(locale: str, key: str) -> str:
    return translate_text(locale, f"nav.{key}")


def _option_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def streamlit_navigation_sections(locale: str = DEFAULT_LOCALE) -> tuple[str, ...]:
    return tuple(nav_text(locale, key) for key in NAV_SECTION_KEYS)


def streamlit_navigation_links(locale: str = DEFAULT_LOCALE) -> str:
    anchor_overrides = {
        "price": "price-history",
    }
    return " | ".join(
        f"[{nav_text(locale, key)}](#{anchor_overrides.get(key, localized_report_anchor(key))})"
        for key in NAV_SECTION_KEYS
    )


def streamlit_report_navigation_links(locale: str = DEFAULT_LOCALE) -> str:
    report_headings = report_section_headings(locale)
    return " | ".join(
        f"[{heading.removeprefix('## ')}](#{localized_report_anchor(key)})"
        for key, heading in zip(REPORT_SECTION_KEYS, report_headings, strict=True)
    )


def streamlit_sidebar_control_labels(locale: str = DEFAULT_LOCALE) -> tuple[str, ...]:
    return (
        ui_text(locale, "sidebar_input_type"),
        ui_text(locale, "sidebar_stock_code_issue_id"),
        ui_text(locale, "sidebar_timeout"),
        ui_text(locale, "sidebar_announcement_period"),
        ui_text(locale, "sidebar_source_mode"),
        ui_text(locale, "sidebar_data_date"),
        ui_text(locale, "sidebar_history_range"),
        ui_text(locale, "sidebar_top_n"),
        ui_text(locale, "sidebar_percentage_basis"),
        ui_text(locale, "fetch"),
    )


STREAMLIT_SIDEBAR_CONTROL_LABELS = streamlit_sidebar_control_labels(DEFAULT_LOCALE)


def streamlit_hkex_announcements_columns(locale: str = DEFAULT_LOCALE) -> tuple[str, ...]:
    return (
        ui_text(locale, "hkex_announcements_table_announcement_date"),
        ui_text(locale, "hkex_announcements_table_title"),
        ui_text(locale, "hkex_announcements_table_source"),
        ui_text(locale, "hkex_announcements_table_link"),
    )


def streamlit_chart_help_sections(locale: str = DEFAULT_LOCALE) -> tuple[tuple[str, str], ...]:
    return (
        (ui_text(locale, "chart_help_rainbow_title"), ui_text(locale, "chart_help_rainbow_body")),
        (ui_text(locale, "chart_help_concentration_title"), ui_text(locale, "chart_help_concentration_body")),
        (ui_text(locale, "chart_help_price_title"), ui_text(locale, "chart_help_price_body")),
        (ui_text(locale, "chart_help_announcements_title"), ui_text(locale, "chart_help_announcements_body")),
        (ui_text(locale, "chart_help_cross_check_title"), ui_text(locale, "chart_help_cross_check_body")),
    )


def split_report_markdown_sections(markdown: str, locale: str = DEFAULT_LOCALE) -> dict[str, str]:
    anchor_to_key = {localized_report_anchor(section_key): section_key for section_key in REPORT_SECTION_KEYS}
    anchor_pattern = re.compile(r"""<a id=['"]([^'"]+)['"]></a>""")
    sections: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for line in markdown.splitlines():
        normalized = line.strip()
        match = anchor_pattern.fullmatch(normalized)
        if match is not None:
            section_key = anchor_to_key.get(match.group(1))
        else:
            section_key = None

        if section_key is not None:
            if current_key is not None and current_lines:
                sections[current_key] = "\n".join(current_lines).rstrip()
            current_key = section_key
            current_lines = []
            continue
        if current_key is not None:
            current_lines.append(line)

    if current_key is not None and current_lines:
        sections[current_key] = "\n".join(current_lines).rstrip()

    return sections


def streamlit_responsive_layout_css() -> str:
    """Return a small responsive stylesheet for the existing Streamlit layout."""
    return """
<style>
    .block-container {
        max-width: 100%;
    }

    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stMarkdownContainer"] a {
        overflow-wrap: anywhere;
        word-break: break-word;
    }

    div[data-testid="stTable"],
    div[data-testid="stDataFrame"] {
        overflow-x: auto;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }

        section[data-testid="stSidebar"] > div {
            padding: 1rem 0.75rem 1.5rem;
        }

        section[data-testid="stSidebar"] button,
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] select,
        section[data-testid="stSidebar"] textarea {
            width: 100%;
        }

        div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap;
        }

        div[data-testid="column"] {
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }

        div[data-testid="stDownloadButton"] button,
        div[data-testid="stButton"] button {
            width: 100%;
        }
    }
</style>
""".strip()


def build_raw_preview_tables(
    response: CcassResponse,
    *,
    sample_size: int = 5,
    locale: str = DEFAULT_LOCALE,
) -> tuple[RawPreviewTable, ...]:
    summary_rows = _summary_preview_rows(response, locale)
    holdings_rows = _holding_preview_rows(response, locale)
    return (
        RawPreviewTable(
            table_index=0,
            title=ui_text(locale, "raw_previews_summary_title"),
            shape=(len(summary_rows), 2),
            columns=(ui_text(locale, "raw_previews_metric"), ui_text(locale, "raw_previews_value")),
            sample_rows=tuple(summary_rows[:sample_size]),
        ),
        RawPreviewTable(
            table_index=1,
            title=ui_text(locale, "raw_previews_holdings_title"),
            shape=(len(holdings_rows), len(HOLDINGS_PREVIEW_COLUMNS)),
            columns=HOLDINGS_PREVIEW_COLUMNS,
            sample_rows=tuple(holdings_rows[:sample_size]),
        ),
    )


def build_download_artifacts(
    response: CcassResponse,
    *,
    preview_line_count: int = 80,
    locale: str = DEFAULT_LOCALE,
) -> DownloadArtifacts:
    raw_preview_tables = build_raw_preview_tables(response, locale=locale)
    combined_csv_bytes = _build_combined_csv_bytes(response)
    workbook_bytes = _build_download_workbook_bytes(response, combined_csv_bytes, raw_preview_tables, locale=locale)
    return DownloadArtifacts(
        combined_csv_bytes=combined_csv_bytes,
        combined_csv_filename=f"{response.metadata.code}_all_ccass_data.csv",
        combined_csv_preview=_csv_preview_text(combined_csv_bytes, preview_line_count=preview_line_count),
        workbook_bytes=workbook_bytes,
        workbook_filename=f"{response.metadata.code}_all_sections.xlsx",
        raw_preview_summary_bytes=_table_to_csv_bytes(raw_preview_tables[0]),
        raw_preview_summary_filename=f"{response.metadata.code}_raw_preview_summary.csv",
        raw_preview_holdings_bytes=_table_to_csv_bytes(raw_preview_tables[1]),
        raw_preview_holdings_filename=f"{response.metadata.code}_raw_preview_holdings.csv",
    )


def build_full_summary_markdown(
    prepared: PreparedReport,
    *,
    history_snapshots: Sequence[CcassResponse] | None = None,
    locale: str = DEFAULT_LOCALE,
) -> str:
    response = prepared.response
    if response is None:
        return ui_text(locale, "full_summary_unavailable")

    analysis = prepared.analysis or AnalysisResult()
    summary = response.holdings_summary
    raw_preview_count = len(build_raw_preview_tables(response, locale=locale))
    snapshot_count = len(tuple(history_snapshots or ())) + 1
    warning_count = len(response.data_quality_warnings)
    announcements = prepared.announcements
    stock_events = prepared.stock_events
    capital_information = prepared.capital_information
    officers = prepared.officers

    def section_label(key: str) -> str:
        return translate_text(locale, key).removeprefix("## ")

    rows = [
        (
            section_label("report.section.analysis_ready_summary"),
            ui_text(locale, "full_summary_status_available"),
            ui_text(locale, "full_summary_note_analysis_ready_summary"),
        ),
        (
            section_label("report.section.company"),
            ui_text(locale, "full_summary_status_available"),
            ui_text(
                locale,
                "full_summary_note_company",
                code=response.metadata.code,
                issue_id=response.metadata.issue_id,
            ),
        ),
        (
            section_label("report.section.announcements"),
            ui_text(
                locale,
                "full_summary_status_available" if announcements is not None else "full_summary_status_unavailable",
            ),
            ui_text(
                locale,
                "full_summary_note_announcements_available"
                if announcements is not None
                else "full_summary_note_announcements",
                announcement_count=len(announcements.announcements) if announcements is not None else 0,
            ),
        ),
        (
            section_label("report.section.stock_events"),
            ui_text(
                locale,
                "full_summary_status_available" if stock_events is not None else "full_summary_status_unavailable",
            ),
            ui_text(
                locale,
                "full_summary_note_stock_events_pending"
                if stock_events is not None
                else "full_summary_note_stock_events",
            ),
        ),
        (
            section_label("report.section.capital_information"),
            ui_text(
                locale,
                "full_summary_status_available" if capital_information is not None else "full_summary_status_unavailable",
            ),
            ui_text(
                locale,
                "full_summary_note_capital_information_pending"
                if capital_information is not None
                else "full_summary_note_capital_information",
            ),
        ),
        (
            section_label("report.section.officers"),
            ui_text(locale, "full_summary_status_available" if officers is not None else "full_summary_status_unavailable"),
            ui_text(
                locale,
                "full_summary_note_officers_pending" if officers is not None else "full_summary_note_officers",
            ),
        ),
        (
            section_label("report.section.metadata"),
            ui_text(locale, "full_summary_status_available"),
            ui_text(locale, "full_summary_note_metadata"),
        ),
        (
            section_label("report.section.fetch_summary"),
            ui_text(locale, "full_summary_status_available"),
            ui_text(locale, "full_summary_note_fetch_summary"),
        ),
        (
            section_label("report.section.holdings"),
            ui_text(locale, "full_summary_status_available"),
            ui_text(locale, "full_summary_note_holdings", participant_count=summary.participant_count),
        ),
        (
            section_label("report.section.changes"),
            ui_text(
                locale,
                "full_summary_status_available" if analysis.previous_available else "full_summary_status_unavailable",
            ),
            ui_text(
                locale,
                "full_summary_note_changes_available" if analysis.previous_available else "full_summary_note_changes_unavailable",
            ),
        ),
        (
            section_label("report.section.big_changes"),
            ui_text(
                locale,
                "full_summary_status_available" if analysis.previous_available else "full_summary_status_unavailable",
            ),
            ui_text(
                locale,
                "full_summary_note_big_changes_available" if analysis.previous_available else "full_summary_note_big_changes_unavailable",
            ),
        ),
        (
            section_label("report.section.concentration"),
            ui_text(locale, "full_summary_status_available"),
            ui_text(
                locale,
                "full_summary_note_concentration",
                top5_pct_of_issued=_format_percent(summary.top5_pct_of_issued, locale),
                top10_pct_of_issued=_format_percent(summary.top10_pct_of_issued, locale),
            ),
        ),
        (
            section_label("report.section.concentration_history"),
            ui_text(locale, "full_summary_status_available"),
            ui_text(locale, "full_summary_note_concentration_history", snapshot_count=snapshot_count),
        ),
        (
            section_label("report.section.price_history"),
            ui_text(
                locale,
                "full_summary_status_available" if prepared.price_history is not None else "full_summary_status_unavailable",
            ),
            ui_text(
                locale,
                "full_summary_note_price_history_available"
                if prepared.price_history is not None
                else "full_summary_note_price_history_unavailable",
                price_date_from=prepared.price_history.metadata.price_date_from if prepared.price_history else "",
                price_date_to=prepared.price_history.metadata.price_date_to if prepared.price_history else "",
                source_name=prepared.price_history.metadata.source_name if prepared.price_history else "",
            ),
        ),
        (
            ui_text(locale, "raw_previews_heading"),
            ui_text(locale, "full_summary_status_available"),
            ui_text(locale, "full_summary_note_raw_previews", table_count=raw_preview_count),
        ),
        (
            ui_text(locale, "copy_for_chatgpt"),
            ui_text(locale, "full_summary_status_available"),
            ui_text(locale, "full_summary_note_copy_functions"),
        ),
        (
            ui_text(locale, "downloads_heading"),
            ui_text(locale, "full_summary_status_available"),
            ui_text(locale, "full_summary_note_downloads"),
        ),
        (
            ui_text(locale, "data_quality_heading"),
            ui_text(locale, "full_summary_status_available"),
            ui_text(
                locale,
                "full_summary_note_data_quality_no_warnings"
                if warning_count == 0
                else "full_summary_note_data_quality_warnings",
                warning_count=warning_count,
            ),
        ),
    ]
    lines = [
        f"| {ui_text(locale, 'full_summary_table_section')} | {ui_text(locale, 'full_summary_table_status')} | {ui_text(locale, 'full_summary_table_note')} |",
        "|---|---|---|",
    ]
    lines.extend(f"| {section} | {status} | {note} |" for section, status, note in rows)
    return "\n".join(lines)


def build_data_confidence_markdown(
    prepared: PreparedReport,
    *,
    locale: str = DEFAULT_LOCALE,
) -> str:
    response = prepared.response
    if response is None:
        return ui_text(locale, "report.data_not_available")

    metadata = response.metadata
    rows: list[tuple[str, str]] = [
        (translate_text(locale, "report.metadata.source", value=_display_text(metadata.source_name, locale)), _display_text(metadata.source_name, locale)),
        (translate_text(locale, "report.metadata.source_url", value=_display_text(metadata.source_url, locale)), _display_text(metadata.source_url, locale)),
        (translate_text(locale, "report.metadata.settlement_note", value=_display_text(metadata.settlement_note, locale)), _display_text(metadata.settlement_note, locale)),
        (translate_text(locale, "report.metadata.attribution", value=_display_text(metadata.attribution, locale)), _display_text(metadata.attribution, locale)),
        (translate_text(locale, "report.fetch.data_as_of", value=_display_text(metadata.data_as_of, locale)), _display_text(metadata.data_as_of, locale)),
        (translate_text(locale, "report.fetch.fetched_at", value=_display_text(metadata.fetched_at, locale)), _display_text(metadata.fetched_at, locale)),
        (ui_text(locale, "data_confidence_freshness"), _response_freshness_label(response)),
        (ui_text(locale, "data_confidence_provenance"), _response_provenance_label(response)),
        (ui_text(locale, "data_confidence_fallback"), _yes_no(metadata.cached, locale)),
        (translate_text(locale, "report.metadata.warning_count", value=len(response.data_quality_warnings)), str(len(response.data_quality_warnings))),
    ]
    lines = [
        f"| {translate_text(locale, 'report.table.metric')} | {translate_text(locale, 'report.table.value')} |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def build_report_flow_markdown(*, locale: str = DEFAULT_LOCALE) -> str:
    def section_title(section_key: str) -> str:
        return translate_text(locale, f"report.section.{section_key}").removeprefix("## ").strip()

    visible_first = ", ".join(
        f"[{section_title(key)}](#{localized_report_anchor(key)})"
        for key in ("analysis_ready_summary", "company", "metadata", "fetch_summary", "holdings_summary", "concentration")
    )
    collapsed_details = ", ".join(
        f"[{section_title(key)}](#{localized_report_anchor(key)})"
        for key in ("announcements", "stock_events", "capital_information", "officers", "holdings", "changes", "big_changes", "concentration_history", "price_history")
    )
    actions = ", ".join(
        [
            translate_text(locale, "ui.report_detail_download_copy"),
            translate_text(locale, "ui.copy_for_chatgpt"),
            translate_text(locale, "ui.copy_report"),
            translate_text(locale, "ui.raw_markdown"),
        ]
    )
    lines = [
        f"| {translate_text(locale, 'ui.report_flow_visible_first')} | {visible_first} |",
        f"| {translate_text(locale, 'ui.report_flow_collapsed_details')} | {collapsed_details} |",
        f"| {translate_text(locale, 'ui.report_flow_actions')} | {actions} |",
    ]
    return "\n".join(
        [
            f"| {translate_text(locale, 'report.table.metric')} | {translate_text(locale, 'report.table.value')} |",
            "|---|---|",
            *lines,
        ]
    )


def build_report_action_strip(*, locale: str = DEFAULT_LOCALE) -> str:
    return " | ".join(
        [
            f"[{ui_text(locale, 'copy_for_chatgpt')}](#{localized_report_anchor('copy_for_chatgpt')})",
            f"[{ui_text(locale, 'copy_report')}](#{localized_report_anchor('copy_for_chatgpt')})",
            f"[{ui_text(locale, 'raw_previews_heading')}](#{localized_report_anchor('raw_previews')})",
            f"[{ui_text(locale, 'raw_markdown')}](#{localized_report_anchor('raw_markdown')})",
        ]
    )


def _display_text(value: object | None, locale: str) -> str:
    if value is None or value == "":
        return translate_text(locale, "report.data_not_available")
    if hasattr(value, "isoformat") and not isinstance(value, (str, bytes)):
        return str(value.isoformat())
    return str(value)


def _yes_no(value: bool | None, locale: str) -> str:
    if value is None:
        return translate_text(locale, "report.data_not_available")
    return "Yes" if locale == "en" and value else "No" if locale == "en" else "是" if value else "否"


def _response_warning_codes(response: CcassResponse) -> set[str]:
    codes: set[str] = set()
    for warning in response.data_quality_warnings:
        code = warning_code(warning)
        if code:
            codes.add(code)
    return codes


def _response_freshness_label(response: CcassResponse) -> str:
    warning_codes = _response_warning_codes(response)
    if response.metadata.cached or {"CSV_FALLBACK_USED", "CACHED_SNAPSHOT"} & warning_codes:
        return "cached"
    if {"STALE_DATA", "STALE_LKG"} & warning_codes:
        return "stale"
    if warning_codes & {
        "ANNOUNCEMENTS_UNAVAILABLE",
        "PRICE_HISTORY_UNAVAILABLE",
        "PREVIOUS_SNAPSHOT_ENRICHMENT_UNAVAILABLE",
    }:
        return "partial"
    if response.data_quality_warnings:
        return "unknown"
    return "fresh"


def _response_provenance_label(response: CcassResponse) -> str:
    warning_codes = _response_warning_codes(response)
    if response.metadata.cached or {"CSV_FALLBACK_USED", "CACHED_SNAPSHOT"} & warning_codes:
        return "fallback"
    return "primary"


def resolve_streamlit_query_input(
    raw_value: str,
    input_type: str,
    *,
    repository: NormalizedSnapshotRepository | None = None,
) -> str:
    if input_type == "Stock Code":
        return normalize_stock_code(raw_value)
    if input_type == "Webb-site Issue ID":
        if repository is None:
            raise ValueError("repository is required for Webb-site Issue ID lookup")
        issue_id = _parse_positive_int(raw_value, label="Webb-site Issue ID")
        code = repository.stock_code_for_issue_id(source_id=WEBBSITE_SOURCE_ID, issue_id=issue_id)
        if code is None:
            raise PlatformError(
                ErrorCode.NOT_FOUND,
                f"No verified stock code is available for Webb-site issue ID {issue_id}.",
                status_code=404,
            )
        return code
    raise ValueError(f"Unsupported input type: {input_type}")


def _parse_positive_int(raw_value: str, *, label: str) -> int:
    try:
        value = int(raw_value.strip())
    except ValueError as exc:
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            f"{label} must be a positive integer.",
            status_code=400,
        ) from exc
    if value <= 0:
        raise PlatformError(
            ErrorCode.INVALID_SCHEMA,
            f"{label} must be a positive integer.",
            status_code=400,
        )
    return value


def copy_button_html(label: str, payload: str, *, element_id: str) -> str:
    """Create a clipboard button without interpolating raw report text into JavaScript."""
    encoded = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    safe_label = html.escape(label)
    safe_id = "".join(character for character in element_id if character.isalnum() or character in "-_")
    return f"""
<button id="{safe_id}" style="padding:.45rem .8rem;border-radius:.45rem;border:1px solid #888;cursor:pointer">
  {safe_label}
</button>
<span id="{safe_id}-status" style="margin-left:.5rem"></span>
<script>
document.getElementById("{safe_id}").addEventListener("click", async () => {{
  const bytes = Uint8Array.from(atob("{encoded}"), value => value.charCodeAt(0));
  const text = new TextDecoder().decode(bytes);
  const status = document.getElementById("{safe_id}-status");
  try {{
    await navigator.clipboard.writeText(text);
    status.textContent = "Copied";
  }} catch (error) {{
    status.textContent = "Use the copy icon in Raw Markdown below";
  }}
}});
</script>
""".strip()


class _SingleResponseStore:
    def __init__(self, response: CcassResponse) -> None:
        self._response = response

    def latest_all(self) -> list[CcassResponse]:
        return [self._response]


def _build_combined_csv_bytes(response: CcassResponse) -> bytes:
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "combined.csv"
        export_latest_csv(_SingleResponseStore(response), output_path)
        return output_path.read_bytes()


def _build_download_workbook_bytes(
    response: CcassResponse,
    combined_csv_bytes: bytes,
    raw_preview_tables: tuple[RawPreviewTable, ...],
    *,
    locale: str = DEFAULT_LOCALE,
) -> bytes:
    combined_rows, combined_headers = _csv_rows_from_bytes(combined_csv_bytes)
    workbook_sheets = [
        (
            "Combined CSV",
            combined_headers,
            combined_rows,
        ),
        (
            "Report Metadata",
            ("Field", "Value"),
            [
                {"Field": "Code", "Value": response.metadata.code},
                {"Field": "Stock name", "Value": response.metadata.name or translate_text(locale, "report.data_not_available")},
                {"Field": "Issue ID", "Value": response.metadata.issue_id},
                {"Field": "Holdings date", "Value": response.metadata.holdings_date or translate_text(locale, "report.data_not_available")},
                {"Field": "Participant count", "Value": response.holdings_summary.participant_count},
            ],
        ),
        (
            "Raw Preview Summary",
            raw_preview_tables[0].columns,
            list(raw_preview_tables[0].sample_rows),
        ),
        (
            "Raw Preview Holdings",
            raw_preview_tables[1].columns,
            list(raw_preview_tables[1].sample_rows),
        ),
    ]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        sheet_names = [sheet_name for sheet_name, _, _ in workbook_sheets]
        archive.writestr("[Content_Types].xml", _build_xlsx_content_types(len(workbook_sheets)))
        archive.writestr("_rels/.rels", _build_xlsx_root_rels())
        archive.writestr("xl/workbook.xml", _build_xlsx_workbook_xml(sheet_names))
        archive.writestr("xl/_rels/workbook.xml.rels", _build_xlsx_workbook_rels(len(workbook_sheets)))
        for index, (_, headers, rows) in enumerate(workbook_sheets, start=1):
            archive.writestr(
                f"xl/worksheets/sheet{index}.xml",
                _build_xlsx_sheet_xml(headers, rows),
            )
    return buffer.getvalue()


def _csv_rows_from_bytes(csv_bytes: bytes) -> tuple[list[dict[str, object]], tuple[str, ...]]:
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    headers = tuple(reader.fieldnames or ())
    return [dict(row) for row in reader], headers


def _build_xlsx_content_types(sheet_count: int) -> str:
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        f'{overrides}'
        '</Types>'
    )


def _build_xlsx_root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        '</Relationships>'
    )


def _build_xlsx_workbook_xml(sheet_names: tuple[str, ...]) -> str:
    sheets_xml = "".join(
        f'<sheet name="{xml_escape(sheet_name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, sheet_name in enumerate(sheet_names, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{sheets_xml}</sheets>'
        '</workbook>'
    )


def _build_xlsx_workbook_rels(sheet_count: int) -> str:
    relationships = "".join(
        f'<Relationship Id="rId{index}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'{relationships}'
        '</Relationships>'
    )


def _build_xlsx_sheet_xml(headers: tuple[str, ...], rows: list[dict[str, object]]) -> str:
    sheet_rows = []
    if headers:
        sheet_rows.append(_build_xlsx_row_xml(1, headers))
        for row_index, row in enumerate(rows, start=2):
            values = [row.get(header, "") for header in headers]
            sheet_rows.append(_build_xlsx_row_xml(row_index, values))
    else:
        sheet_rows.append(_build_xlsx_row_xml(1, ("",)))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        '</worksheet>'
    )


def _build_xlsx_row_xml(row_number: int, values: tuple[object, ...] | list[object]) -> str:
    cells = "".join(
        _build_xlsx_cell_xml(row_number, column_number, value)
        for column_number, value in enumerate(values, start=1)
    )
    return f'<row r="{row_number}">{cells}</row>'


def _build_xlsx_cell_xml(row_number: int, column_number: int, value: object) -> str:
    cell_ref = f"{_xlsx_column_letter(column_number)}{row_number}"
    text = _xlsx_text(value)
    return f'<c r="{cell_ref}" t="inlineStr"><is><t>{xml_escape(text)}</t></is></c>'


def _xlsx_column_letter(column_number: int) -> str:
    letters = ""
    while column_number:
        column_number, remainder = divmod(column_number - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def _xlsx_text(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat") and not isinstance(value, (str, bytes)):
        return str(value.isoformat())
    return str(value)


def _csv_preview_text(csv_bytes: bytes, *, preview_line_count: int) -> str:
    text = csv_bytes.decode("utf-8-sig")
    lines = text.splitlines()
    return "\n".join(lines[:preview_line_count])


def _table_to_csv_bytes(table: RawPreviewTable) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=table.columns, lineterminator="\n")
    writer.writeheader()
    for row in table.sample_rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8-sig")


def _summary_preview_rows(response: CcassResponse, locale: str) -> list[dict[str, object]]:
    summary = response.holdings_summary
    metadata = response.metadata
    metric_label = ui_text(locale, "raw_previews_metric")
    value_label = ui_text(locale, "raw_previews_value")
    return [
        {metric_label: "Code", value_label: metadata.code},
        {metric_label: "Stock name", value_label: metadata.name or translate_text(locale, "report.data_not_available")},
        {metric_label: "Issue ID", value_label: metadata.issue_id},
        {metric_label: "Holdings date", value_label: metadata.holdings_date or translate_text(locale, "report.data_not_available")},
        {metric_label: "Participant count", value_label: summary.participant_count},
        {
            metric_label: "Total in CCASS shares",
            value_label: summary.total_in_ccass_shares or translate_text(locale, "report.data_not_available"),
        },
        {
            metric_label: "Issued shares",
            value_label: summary.issued_shares or translate_text(locale, "report.data_not_available"),
        },
        {
            metric_label: "Top 5 / issued",
            value_label: _format_percent(summary.top5_pct_of_issued, locale),
        },
        {
            metric_label: "Top 10 / issued",
            value_label: _format_percent(summary.top10_pct_of_issued, locale),
        },
    ]


def _holding_preview_rows(response: CcassResponse, locale: str) -> list[dict[str, object]]:
    return [
        {
            "Rank": row.rank,
            "CCASS ID": row.participant_id,
            "Participant": row.participant,
            "Shares": row.shares,
            "Last change": row.last_change or translate_text(locale, "report.data_not_available"),
            "% issued": _format_percent(row.pct_of_issued, locale),
            "% CCASS": _format_percent(row.pct_of_ccass, locale),
            "Cumulative %": _format_percent(row.cumulative_pct_of_issued, locale),
            "Category": row.participant_category or translate_text(locale, "report.data_not_available"),
        }
        for row in response.holdings
    ]


def _format_percent(value: float | None, locale: str) -> str:
    return f"{value:.4f}%" if value is not None else translate_text(locale, "report.data_not_available")


def _progress(callback: Callable[[int, str], None] | None, value: int, label: str) -> None:
    if callback:
        callback(value, label)


def _streamlit_anchor_id(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")



def render_prepared_report(prepared: PreparedReport, *, locale: str = DEFAULT_LOCALE) -> tuple[str, str]:
    if prepared.response is None:
        markdown = build_markdown_report(
            None,
            code=prepared.code,
            fetch_error=prepared.fetch_error,
            locale=locale,
        )
    else:
        markdown = build_markdown_report(
            prepared.response,
            code=prepared.code,
            analysis=prepared.analysis,
            announcements=prepared.announcements,
            stock_events=prepared.stock_events,
            capital_information=prepared.capital_information,
            price_history=prepared.price_history,
            locale=locale,
        )
    return markdown, build_chatgpt_copy_payload(markdown)

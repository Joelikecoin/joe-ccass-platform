
import asyncio
import os
import re
import warnings
from datetime import date, timedelta
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.config import get_settings
from app.errors import ErrorCode, PlatformError
from app.services.ccass import get_ccass_service
from app.streamlit_ui import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    build_download_artifacts,
    build_data_confidence_markdown,
    build_full_summary_markdown,
    build_raw_preview_tables,
    build_report_action_strip,
    build_report_flow_markdown,
    build_research_workflow_summary_markdown,
    build_ai_research_context_consumer_entry_from_prepared_report,
    build_ai_research_context_consumer_entry_markdown,
    copy_button_html,
    prepare_report,
    render_prepared_report,
    resolve_streamlit_query_input,
    nav_text,
    streamlit_chart_help_sections,
    streamlit_report_navigation_links,
    streamlit_hkex_announcements_columns,
    streamlit_navigation_links,
    streamlit_responsive_layout_css,
    split_report_markdown_sections,
    ui_text,
)
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.collector import SnapshotStore
from ccass_core.report import localized_report_anchor, translate_text


def _load_streamlit_secrets() -> None:
    try:
        secrets = dict(st.secrets)
    except Exception:
        return
    for key in (
        "API_KEY",
        "DATA_SOURCE",
        "CCASS_CSV_URL",
        "CCASS_CSV_MAX_BYTES",
        "REQUEST_TIMEOUT_SECONDS",
        "CACHE_TTL_SECONDS",
        "MIN_REQUEST_INTERVAL_SECONDS",
    ):
        if key not in os.environ and key in secrets:
            os.environ[key] = str(secrets[key])
    get_settings.cache_clear()


def _option_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _choice_label(locale: str, category: str, value: str) -> str:
    return ui_text(locale, f"{category}.{_option_key(value)}")


def _dedupe_warning_messages(captured: list[warnings.WarningMessage]) -> list[str]:
    seen: set[str] = set()
    messages: list[str] = []
    for warning in captured:
        message = str(warning.message)
        if message not in seen:
            seen.add(message)
            messages.append(message)
    return messages


def _render_fallback_warning(captured: list[warnings.WarningMessage]) -> None:
    messages = _dedupe_warning_messages(captured)
    if messages:
        st.warning("\n".join(messages))


def _report_section_title(locale: str, section_key: str) -> str:
    return translate_text(locale, f"report.section.{section_key}").removeprefix("## ").strip()


def _render_section_expanders(
    *,
    locale: str,
    section_keys: tuple[str, ...],
    sections: dict[str, str],
) -> None:
    for section_key in section_keys:
        section_markdown = sections.get(section_key)
        if not section_markdown:
            continue
        with st.expander(_report_section_title(locale, section_key), expanded=False):
            st.markdown(section_markdown)


def _render_markdown_sections(section_keys: tuple[str, ...], sections: dict[str, str]) -> None:
    for section_key in section_keys:
        section_markdown = sections.get(section_key)
        if section_markdown:
            st.markdown(section_markdown)


def _render_named_expander(label: str, section_markdown: str | None) -> None:
    if not section_markdown:
        return
    with st.expander(label, expanded=False):
        st.markdown(section_markdown)


def _render_dt_rainbow_framework(locale: str) -> None:
    with st.expander(ui_text(locale, "dt_rainbow_heading"), expanded=False):
        st.caption(ui_text(locale, "dt_rainbow_caption"))
        enabled = st.checkbox(ui_text(locale, "dt_rainbow_enable"), value=False, key="dt_rainbow_enabled")
        if not enabled:
            st.session_state.pop("dt_rainbow_requested", None)
            return

        if st.button(ui_text(locale, "dt_rainbow_generate"), key="dt_rainbow_generate_button"):
            st.session_state["dt_rainbow_requested"] = True

        if st.session_state.get("dt_rainbow_requested"):
            with st.spinner(ui_text(locale, "dt_rainbow_loading")):
                st.info(ui_text(locale, "dt_rainbow_unavailable"))


def _render_download_copy_controls(
    *,
    locale: str,
    prepared: object,
    localized_markdown: str,
    localized_chatgpt_payload: str,
) -> None:
    st.markdown(f"<a id='{localized_report_anchor('copy_for_chatgpt')}'></a>", unsafe_allow_html=True)
    with st.expander(ui_text(locale, "report_detail_download_copy"), expanded=False):
        st.markdown(f"## {ui_text(locale, 'copy_for_chatgpt')}")
        st.caption(ui_text(locale, "copy_for_chatgpt_caption"))
        copy_col, report_col = st.columns(2)
        with copy_col:
            st.markdown(f"**{ui_text(locale, 'copy_for_chatgpt')}**")
            components.html(
                copy_button_html(
                    ui_text(locale, "copy_for_chatgpt"),
                    localized_chatgpt_payload,
                    element_id="copy-chatgpt",
                ),
                height=55,
            )
        with report_col:
            st.markdown(f"**{ui_text(locale, 'copy_report')}**")
            components.html(
                copy_button_html(ui_text(locale, "copy_report"), localized_markdown, element_id="copy-report"),
                height=55,
            )

        st.markdown(f"## {ui_text(locale, 'downloads_heading')}")
        st.markdown(f"### {ui_text(locale, 'downloads_workflow_heading')}")
        st.caption(ui_text(locale, "downloads_workflow_caption"))
        response = getattr(prepared, "response", None)
        if response is None:
            st.info(ui_text(locale, "downloads_unavailable"))
        else:
            download_artifacts = build_download_artifacts(response, locale=locale)
            st.caption(ui_text(locale, "downloads_caption"))
            combined_col, workbook_col, report_download_col = st.columns(3)
            with combined_col:
                st.markdown(f"**{ui_text(locale, 'downloads_combined_csv')}**")
                st.download_button(
                    ui_text(locale, "downloads_download_combined_csv"),
                    data=download_artifacts.combined_csv_bytes,
                    file_name=download_artifacts.combined_csv_filename,
                    mime="text/csv",
                    use_container_width=True,
                )
            with workbook_col:
                st.markdown(f"**{ui_text(locale, 'downloads_excel_workbook')}**")
                st.download_button(
                    ui_text(locale, "downloads_download_excel_workbook"),
                    data=download_artifacts.workbook_bytes,
                    file_name=download_artifacts.workbook_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            with report_download_col:
                st.markdown(f"**{ui_text(locale, 'downloads_report_markdown')}**")
                st.download_button(
                    ui_text(locale, "downloads_download_markdown_report"),
                    data=localized_markdown,
                    file_name=getattr(prepared, "filename", "report.md"),
                    mime="text/markdown",
                    use_container_width=True,
                )

            with st.expander(ui_text(locale, "downloads_csv_preview"), expanded=False):
                st.caption(ui_text(locale, "downloads_first_80_csv_lines"))
                st.code(download_artifacts.combined_csv_preview, language="csv")

            with st.expander(ui_text(locale, "downloads_section_specific"), expanded=False):
                section_summary_col, section_holdings_col = st.columns(2)
                with section_summary_col:
                    st.markdown(f"**{ui_text(locale, 'downloads_raw_preview_summary_csv')}**")
                    st.download_button(
                        ui_text(locale, "downloads_download_raw_preview_summary_csv"),
                        data=download_artifacts.raw_preview_summary_bytes,
                        file_name=download_artifacts.raw_preview_summary_filename,
                        mime="text/csv",
                        use_container_width=True,
                    )
                with section_holdings_col:
                    st.markdown(f"**{ui_text(locale, 'downloads_raw_preview_holdings_csv')}**")
                    st.download_button(
                        ui_text(locale, "downloads_download_raw_preview_holdings_csv"),
                        data=download_artifacts.raw_preview_holdings_bytes,
                        file_name=download_artifacts.raw_preview_holdings_filename,
                        mime="text/csv",
                        use_container_width=True,
                    )


def _history_range_start(end_date: date, history_range: str) -> date:
    windows = {
        "7 days": 7,
        "30 days": 30,
        "90 days": 90,
    }
    days = windows.get(history_range)
    if days is None:
        return date(1900, 1, 1)
    return end_date - timedelta(days=days)


def _price_history_range_start(end_date: date, history_range: str) -> date:
    if history_range in {"Latest", "Custom"}:
        return end_date - timedelta(days=90)
    return _history_range_start(end_date, history_range)


def _announcement_period_start(end_date: date, announcement_period: str) -> date:
    windows = {
        "7 days": 7,
        "30 days": 30,
        "90 days": 90,
    }
    days = windows.get(announcement_period)
    if days is None:
        return date(1999, 4, 1)
    return end_date - timedelta(days=days)


_load_streamlit_secrets()
settings = get_settings()
if "locale" not in st.session_state:
    st.session_state.locale = DEFAULT_LOCALE
current_locale = st.session_state.get("locale", DEFAULT_LOCALE)
st.set_page_config(page_title=ui_text(current_locale, "app_title"), page_icon="??", layout="wide")
st.markdown(streamlit_responsive_layout_css(), unsafe_allow_html=True)
st.title(ui_text(current_locale, "app_title"))
st.caption(ui_text(current_locale, "app_caption"))
st.markdown(streamlit_navigation_links(current_locale))
st.caption(ui_text(current_locale, "jump_links_caption"))

with st.sidebar:
    st.header(ui_text(current_locale, "sidebar_header"))
    st.selectbox(
        ui_text(current_locale, "sidebar_language"),
        SUPPORTED_LOCALES,
        key="locale",
        format_func=lambda value: ui_text(value, f"locale_name.{value}"),
    )
    current_locale = st.session_state.get("locale", DEFAULT_LOCALE)
    input_type = st.radio(
        ui_text(current_locale, "sidebar_input_type"),
        ("Stock Code", "Webb-site Issue ID"),
        index=0,
        format_func=lambda value: _choice_label(current_locale, "input_type", value),
    )
    timeout_seconds = st.number_input(
        ui_text(current_locale, "sidebar_timeout"),
        min_value=1.0,
        value=float(settings.request_timeout_seconds),
        step=1.0,
    )
    big_change_threshold = st.number_input(
        ui_text(current_locale, "sidebar_big_change_threshold"),
        min_value=0,
        value=settings.big_changes_threshold_shares,
        step=100000,
    )
    announcement_period = st.selectbox(
        ui_text(current_locale, "sidebar_announcement_period"),
        ("All", "7 days", "30 days", "90 days"),
        index=0,
        format_func=lambda value: _choice_label(current_locale, "announcement_period", value),
    )
    source_mode = st.selectbox(
        ui_text(current_locale, "sidebar_source_mode"),
        ("auto", "webbsite", "google_drive_csv"),
        index=("auto", "webbsite", "google_drive_csv").index(settings.data_source),
        format_func=lambda value: _choice_label(current_locale, "source_mode", value),
    )
    data_date = st.date_input(ui_text(current_locale, "sidebar_data_date"), value=date.today())
    history_range = st.selectbox(
        ui_text(current_locale, "sidebar_history_range"),
        ("Latest", "7 days", "30 days", "90 days", "Custom"),
        index=0,
        format_func=lambda value: _choice_label(current_locale, "history_range", value),
    )
    top_n = st.slider(ui_text(current_locale, "sidebar_top_n"), min_value=5, max_value=100, value=20, step=5)
    percentage_basis = st.selectbox(
        ui_text(current_locale, "sidebar_percentage_basis"),
        ("CCASS", "Issued Shares"),
        index=0,
        format_func=lambda value: _choice_label(current_locale, "percentage_basis", value),
    )
    show_rendered_markdown = st.checkbox(ui_text(current_locale, "sidebar_show_rendered_markdown"), value=True)
    use_local_history = st.checkbox(ui_text(current_locale, "sidebar_use_local_history"), value=True)
    load_price_history = st.checkbox(ui_text(current_locale, "sidebar_load_price_history"), value=False)
    st.caption(
        ui_text(
            current_locale,
            "sidebar_source_mode_caption",
            source_mode=_choice_label(current_locale, "source_mode", source_mode),
            timeout_seconds=timeout_seconds,
            announcement_period=_choice_label(current_locale, "announcement_period", announcement_period),
            data_date=data_date.isoformat(),
            history_range=_choice_label(current_locale, "history_range", history_range),
            percentage_basis=_choice_label(current_locale, "percentage_basis", percentage_basis),
        )
    )
    st.divider()
    st.caption(ui_text(current_locale, "data_source_mode", source_mode=_choice_label(current_locale, "source_mode", source_mode)))
    st.caption(ui_text(current_locale, "hkex_manual_verification"))
    st.caption(ui_text(current_locale, "sidebar_query_input_caption"))
    st.info(ui_text(current_locale, "fetch_guidance_caption"))

    with st.form("ccass-query"):
        if input_type == "Webb-site Issue ID":
            input_placeholder = "e.g. 3601"
            input_max_chars = 8
        else:
            input_placeholder = "e.g. 1592 ? 01592"
            input_max_chars = 5

        raw_code = st.text_input(
            ui_text(current_locale, "sidebar_stock_code_issue_id"),
            placeholder=input_placeholder,
            max_chars=input_max_chars,
        )
        submitted = st.form_submit_button(ui_text(current_locale, "fetch"), type="primary", use_container_width=True)

if submitted:
    st.session_state.pop("prepared_report", None)
    progress_bar = st.progress(0, text=ui_text(current_locale, "progress_starting"))
    fetch_status = st.empty()

    def update_progress(value: int, label: str) -> None:
        progress_bar.progress(value, text=label)

    try:
        os.environ["DATA_SOURCE"] = source_mode
        os.environ["REQUEST_TIMEOUT_SECONDS"] = str(float(timeout_seconds))
        get_settings.cache_clear()

        sqlite_path = Path(os.getenv("CCASS_SQLITE_PATH", "data/ccass_snapshots.db"))
        resolved_code = raw_code
        if input_type == "Webb-site Issue ID":
            if not sqlite_path.is_file():
                raise PlatformError(
                    ErrorCode.NOT_FOUND,
                    "No verified stock code is available for the requested Webb-site issue ID.",
                    status_code=404,
                )
            issue_repository = NormalizedSnapshotRepository(sqlite_path)
            resolved_code = resolve_streamlit_query_input(
                raw_code,
                input_type,
                repository=issue_repository,
            )
        else:
            resolved_code = resolve_streamlit_query_input(raw_code, input_type)
        fetch_status.info(
            ui_text(
                current_locale,
                "fetch_status_running",
                source_mode=_choice_label(current_locale, "source_mode", source_mode),
                code=resolved_code,
            )
        )
        previous_loader = None
        history_snapshots = None
        if use_local_history and sqlite_path.is_file():
            store = SnapshotStore(sqlite_path)
            history_start = _history_range_start(data_date, history_range)
            history_snapshots = tuple(
                snapshot.to_response()
                for snapshot in store.repository.date_range(
                    resolved_code,
                    date_from=history_start,
                    date_to=data_date,
                )
            )

            def load_previous(response):
                return store.previous_for(response.metadata.code, response)
            previous_loader = load_previous
        st.session_state.history_snapshots = history_snapshots
        prepared = asyncio.run(
            prepare_report(
                resolved_code,
                holdings_limit=top_n,
                big_change_threshold=int(big_change_threshold),
                service=get_ccass_service(),
                locale=current_locale,
                history_snapshots=history_snapshots,
                previous_loader=previous_loader,
                announcements_enabled=True,
                announcement_start_date=_announcement_period_start(data_date, announcement_period),
                announcement_end_date=data_date,
                price_history_enabled=load_price_history,
                price_history_start_date=_price_history_range_start(data_date, history_range),
                price_history_end_date=data_date,
                progress=update_progress,
            )
        )
    except PlatformError as exc:
        progress_bar.empty()
        fetch_status.error(ui_text(current_locale, "fetch_status_failure", error=exc.message))
        st.error(f"{ui_text(current_locale, 'validation_error_prefix')} ? {exc.message}")
    except Exception as exc:
        progress_bar.empty()
        fetch_status.error(ui_text(current_locale, "fetch_status_failure", error=type(exc).__name__))
        st.error(f"{ui_text(current_locale, 'unexpected_error_prefix')}: {type(exc).__name__}")
    else:
        st.session_state.prepared_report = prepared
        if prepared.response is None:
            fetch_status.error(
                ui_text(
                    current_locale,
                    "fetch_status_failure",
                    error=prepared.fetch_error or translate_text(current_locale, "report.data_not_available"),
                )
            )
        elif prepared.response.metadata.cached:
            fetch_status.warning(
                ui_text(
                    current_locale,
                    "fetch_status_success_cached",
                    source=prepared.response.metadata.source_name or prepared.response.metadata.source_url,
                    data_as_of=prepared.response.metadata.data_as_of or ui_text(current_locale, "data_not_available"),
                )
            )
        else:
            fetch_status.success(
                ui_text(
                    current_locale,
                    "fetch_status_success",
                    source=prepared.response.metadata.source_name or prepared.response.metadata.source_url,
                    data_as_of=prepared.response.metadata.data_as_of or ui_text(current_locale, "data_not_available"),
                )
            )

prepared = st.session_state.get("prepared_report")
history_snapshots = st.session_state.get("history_snapshots")
if prepared is not None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        localized_markdown, localized_chatgpt_payload = render_prepared_report(prepared, locale=current_locale)

        if prepared.fetch_error:
            st.error(prepared.fetch_error)
            st.info(ui_text(current_locale, "fetch_summary_remaining"))
        st.markdown(build_research_workflow_summary_markdown(prepared.workflow, locale=current_locale))
        research_context_entry = (
            prepared.research_context_entry
            if prepared.research_context_entry is not None
            else build_ai_research_context_consumer_entry_from_prepared_report(prepared)
        )
        if research_context_entry is not None:
            st.markdown(build_ai_research_context_consumer_entry_markdown(research_context_entry))
        st.markdown(f"<a id='{localized_report_anchor('full_summary')}'></a>", unsafe_allow_html=True)
        st.markdown(f"## {ui_text(current_locale, 'full_summary_heading')}")
        st.caption(ui_text(current_locale, 'full_summary_caption'))
        if prepared.response is None:
            st.info(ui_text(current_locale, 'full_summary_unavailable'))
        else:
            st.markdown(
                build_full_summary_markdown(
                    prepared,
                    history_snapshots=history_snapshots,
                    locale=current_locale,
                )
            )
            st.markdown(f"### {ui_text(current_locale, 'data_confidence_heading')}")
            st.caption(ui_text(current_locale, 'data_confidence_caption'))
            st.markdown(build_data_confidence_markdown(prepared, locale=current_locale))
        st.markdown(f"<a id='{localized_report_anchor('all_tables')}'></a>", unsafe_allow_html=True)
        st.markdown(f"## {nav_text(current_locale, 'all_tables')}")
        st.markdown(f"### {ui_text(current_locale, 'report_navigation_heading')}")
        st.caption(ui_text(current_locale, 'report_navigation_caption'))
        st.markdown(streamlit_report_navigation_links(current_locale))
        st.markdown(f"### {ui_text(current_locale, 'data_quality_heading')}")
        st.caption(ui_text(current_locale, 'data_quality_caption'))
        st.caption(ui_text(current_locale, 'data_quality_help_caption'))
        if prepared.response is None:
            st.info(ui_text(current_locale, 'data_quality_unavailable'))
        else:
            quality_warnings = list(prepared.response.data_quality_warnings)
            if quality_warnings:
                st.warning("\n".join(f"- {warning}" for warning in quality_warnings))
            else:
                st.info(ui_text(current_locale, 'data_quality_no_warnings'))
        st.markdown(f"<a id='{localized_report_anchor('all_parsed_tables')}'></a>", unsafe_allow_html=True)
        st.markdown(f"## {ui_text(current_locale, 'all_parsed_tables_heading')}")
        st.caption(ui_text(current_locale, 'all_parsed_tables_caption'))
        report_sections = split_report_markdown_sections(localized_markdown, locale=current_locale)
        if prepared.response is None:
            st.info(ui_text(current_locale, "report_details_unavailable"))
        else:
            st.markdown(f"### {ui_text(current_locale, 'report_details_heading')}")
            st.caption(ui_text(current_locale, "report_details_caption"))
            st.markdown(build_report_action_strip(locale=current_locale))
            st.markdown(f"### {ui_text(current_locale, 'report_flow_heading')}")
            st.caption(ui_text(current_locale, 'report_flow_caption'))
            st.markdown(build_report_flow_markdown(locale=current_locale))
            _render_markdown_sections(("company",), report_sections)
            st.markdown(f"### {ui_text(current_locale, 'company_information_heading')}")
            st.caption(ui_text(current_locale, "company_information_caption"))
            _render_download_copy_controls(
                locale=current_locale,
                prepared=prepared,
                localized_markdown=localized_markdown,
                localized_chatgpt_payload=localized_chatgpt_payload,
            )
            _render_named_expander(
                ui_text(current_locale, "hkex_announcements_heading"),
                report_sections.get("announcements"),
            )
            _render_named_expander(
                ui_text(current_locale, "stock_events_heading"),
                report_sections.get("stock_events"),
            )
            _render_named_expander(
                ui_text(current_locale, "officers_heading"),
                report_sections.get("officers"),
            )
            _render_markdown_sections(("metadata", "holdings_summary", "concentration"), report_sections)
            _render_named_expander(
                ui_text(current_locale, "report_detail_holdings_detail"),
                report_sections.get("holdings"),
            )
            _render_named_expander(
                _report_section_title(current_locale, "changes"),
                report_sections.get("changes"),
            )
            _render_named_expander(
                _report_section_title(current_locale, "big_changes"),
                report_sections.get("big_changes"),
            )
            with st.expander(ui_text(current_locale, "report_detail_historical_information"), expanded=False):
                _render_markdown_sections(("concentration_history", "price_history"), report_sections)

        if show_rendered_markdown:
            st.markdown(f"### {ui_text(current_locale, 'rendered_markdown')}")
            st.caption(ui_text(current_locale, "rendered_markdown_caption"))
            with st.expander(ui_text(current_locale, "rendered_markdown"), expanded=False):
                st.markdown(localized_markdown)

        st.markdown(f"### {ui_text(current_locale, 'visualization_heading')}")
        st.caption(ui_text(current_locale, 'visualization_caption'))
        _render_dt_rainbow_framework(current_locale)

        st.markdown(f"<a id='{localized_report_anchor('raw_previews')}'></a>", unsafe_allow_html=True)
        st.markdown(f"## {ui_text(current_locale, 'raw_previews_heading')}")
        st.caption(ui_text(current_locale, "raw_previews_help_caption"))
        with st.expander(ui_text(current_locale, "raw_previews_expander"), expanded=False):
            if prepared.response is None:
                st.info(ui_text(current_locale, "raw_previews_unavailable"))
            else:
                raw_preview_tables = build_raw_preview_tables(prepared.response, locale=current_locale)
                st.caption(ui_text(current_locale, "raw_previews_caption"))
                overview_rows = [
                    {
                        ui_text(current_locale, "raw_previews_table_index"): table.table_index,
                        ui_text(current_locale, "raw_previews_table_name"): table.title,
                        ui_text(current_locale, "raw_previews_shape"): f"{table.shape[0]} ? {table.shape[1]}",
                        ui_text(current_locale, "raw_previews_columns"): ", ".join(table.columns),
                    }
                    for table in raw_preview_tables
                ]
                st.table(overview_rows)
                for table in raw_preview_tables:
                    st.markdown(f"### {table.table_index}. {table.title}")
                    st.caption(f"{ui_text(current_locale, 'raw_previews_shape')}: {table.shape[0]} ? {table.shape[1]}")
                    st.caption(f"{ui_text(current_locale, 'raw_previews_columns')}: {', '.join(table.columns)}")
                    if table.sample_rows:
                        st.table(list(table.sample_rows))
                    else:
                        st.info(ui_text(current_locale, "raw_previews_no_sample_rows"))

        st.markdown(f"<a id='{localized_report_anchor('chart_help')}'></a>", unsafe_allow_html=True)
        st.markdown(f"## {ui_text(current_locale, 'chart_help_heading')}")
        st.caption(ui_text(current_locale, 'chart_help_caption'))
        st.caption(ui_text(current_locale, 'chart_help_surface_caption'))
        for title, body in streamlit_chart_help_sections(current_locale):
            st.markdown(f"### {title}")
            st.markdown(body)

        st.markdown(f"<a id='{localized_report_anchor('hkex_announcements')}'></a>", unsafe_allow_html=True)
        st.markdown(f"## {ui_text(current_locale, 'hkex_announcements_heading')}")
        st.caption(ui_text(current_locale, 'hkex_announcements_caption'))
        announcements = getattr(prepared, "announcements", None)
        if announcements is None:
            st.warning(ui_text(current_locale, 'hkex_announcements_unavailable'))
            announcement_rows: list[dict[str, object]] = []
        else:
            announcement_rows = [
                {
                    ui_text(current_locale, "hkex_announcements_table_announcement_date"): row.announcement_date.isoformat(),
                    ui_text(current_locale, "hkex_announcements_table_title"): row.title,
                    ui_text(current_locale, "hkex_announcements_table_source"): row.source,
                    ui_text(current_locale, "hkex_announcements_table_link"): row.link
                    or translate_text(current_locale, "report.data_not_available"),
                }
                for row in announcements.announcements
            ]
        announcement_columns = streamlit_hkex_announcements_columns(current_locale)
        st.metric(ui_text(current_locale, 'hkex_announcements_count'), len(announcement_rows))
        st.markdown(f"### {ui_text(current_locale, 'hkex_announcements_rows_label')}")
        st.caption(ui_text(current_locale, 'hkex_announcements_sorting_note'))
        if announcement_rows:
            import pandas as pd

            st.dataframe(pd.DataFrame(announcement_rows, columns=announcement_columns), use_container_width=True, hide_index=True)
        else:
            st.markdown(
                "| " + " | ".join(announcement_columns) + " |"
            )
            st.markdown(
                "| " + " | ".join(['---'] * len(announcement_columns)) + " |"
            )
        if announcements is not None and not announcement_rows:
            st.info(ui_text(current_locale, 'hkex_announcements_empty'))
        st.markdown(f"**{ui_text(current_locale, 'hkex_announcements_export_heading')}**")
        st.caption(ui_text(current_locale, 'hkex_announcements_export_note'))
        st.caption(
            f"{ui_text(current_locale, 'hkex_announcements_export_csv_label')} | "
            f"{ui_text(current_locale, 'hkex_announcements_export_excel_label')}"
        )

        with st.expander(ui_text(current_locale, "raw_markdown"), expanded=False):
            st.markdown(f"<a id='{localized_report_anchor('raw_markdown')}'></a>", unsafe_allow_html=True)
            st.code(localized_markdown, language="markdown")

    _render_fallback_warning(caught)

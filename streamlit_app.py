import asyncio
import os
from datetime import date
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.config import get_settings
from app.errors import ErrorCode, PlatformError
from app.services.ccass import get_ccass_service
from app.streamlit_ui import (
    STREAMLIT_ANNOUNCEMENT_PERIODS,
    STREAMLIT_HISTORY_RANGES,
    STREAMLIT_PERCENTAGE_BASES,
    STREAMLIT_SOURCE_MODES,
    build_download_artifacts,
    build_raw_preview_tables,
    copy_button_html,
    prepare_report,
    resolve_streamlit_query_input,
    streamlit_navigation_links,
)
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.collector import SnapshotStore


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


_load_streamlit_secrets()
settings = get_settings()
st.set_page_config(page_title="HK CCASS Shareholding Analysis Tool", page_icon="📊", layout="wide")
st.title("HK CCASS Shareholding Analysis Tool")
st.caption(
    "Low-frequency research tool. CCASS is settlement-layer nominee data, normally subject to T+2."
)
st.markdown(streamlit_navigation_links())
st.caption("Jump links follow the report headings rendered below.")

with st.sidebar:
    st.header("Options")
    input_type = st.radio("Input Type", ("Stock Code", "Webb-site Issue ID"), index=0)
    timeout_seconds = st.number_input(
        "Timeout",
        min_value=1.0,
        value=float(settings.request_timeout_seconds),
        step=1.0,
    )
    big_change_threshold = st.number_input(
        "Big change threshold (shares)",
        min_value=0,
        value=settings.big_changes_threshold_shares,
        step=100000,
    )
    announcement_period = st.selectbox("Announcement Period", STREAMLIT_ANNOUNCEMENT_PERIODS, index=0)
    source_mode = st.selectbox(
        "Source Mode",
        STREAMLIT_SOURCE_MODES,
        index=STREAMLIT_SOURCE_MODES.index(settings.data_source),
    )
    data_date = st.date_input("Data Date", value=date.today())
    history_range = st.selectbox("History Range", STREAMLIT_HISTORY_RANGES, index=0)
    top_n = st.slider("Top N", min_value=5, max_value=100, value=20, step=5)
    percentage_basis = st.selectbox("Percentage Basis", STREAMLIT_PERCENTAGE_BASES, index=0)
    show_rendered_markdown = st.checkbox("Show rendered Markdown", value=True)
    use_local_history = st.checkbox("Use local SQLite history for Changes", value=True)
    st.caption(
        f"Source mode: {source_mode} | Timeout: {timeout_seconds:g}s | Announcement period: {announcement_period} | Data date: {data_date.isoformat()} | History range: {history_range} | Percentage basis: {percentage_basis}"
    )
    st.divider()
    st.caption(f"Data source mode: {source_mode}")
    st.caption("HKEX SDW: manual verification only; no automated access.")

    with st.form("ccass-query"):
        if input_type == "Webb-site Issue ID":
            input_placeholder = "e.g. 3601"
            input_max_chars = 8
        else:
            input_placeholder = "e.g. 1592 → 01592"
            input_max_chars = 5

        raw_code = st.text_input(
            "Stock Code / Issue ID",
            placeholder=input_placeholder,
            max_chars=input_max_chars,
        )
        submitted = st.form_submit_button("Fetch", type="primary", use_container_width=True)

if submitted:
    progress_bar = st.progress(0, text="Starting")

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
        previous_loader = None
        if use_local_history and sqlite_path.is_file():
            store = SnapshotStore(sqlite_path)

            def load_previous(response):
                return store.previous_for(response.metadata.code, response)

            previous_loader = load_previous
        prepared = asyncio.run(
            prepare_report(
                resolved_code,
                holdings_limit=top_n,
                big_change_threshold=int(big_change_threshold),
                service=get_ccass_service(),
                previous_loader=previous_loader,
                progress=update_progress,
            )
        )
    except PlatformError as exc:
        progress_bar.empty()
        st.error(f"Validation error — {exc.message}")
    except Exception as exc:
        progress_bar.empty()
        st.error(f"UNEXPECTED_ERROR: {type(exc).__name__}")
    else:
        if prepared.fetch_error:
            st.error(prepared.fetch_error)
            st.info("The Fetch Summary and every required report section remain available below.")
        if show_rendered_markdown:
            st.markdown(prepared.markdown)

        st.markdown("## Raw Previews")
        with st.expander("Parsed source tables", expanded=False):
            if prepared.response is None:
                st.info("Raw previews are available after a successful fetch.")
            else:
                raw_preview_tables = build_raw_preview_tables(prepared.response)
                st.caption(
                    "Inspection view for parsed source tables already present in the fetched response."
                )
                overview_rows = [
                    {
                        "Table Index": table.table_index,
                        "Table Name": table.title,
                        "Shape": f"{table.shape[0]} × {table.shape[1]}",
                        "Columns": ", ".join(table.columns),
                    }
                    for table in raw_preview_tables
                ]
                st.table(overview_rows)
                for table in raw_preview_tables:
                    st.markdown(f"### {table.table_index}. {table.title}")
                    st.caption(f"Shape: {table.shape[0]} × {table.shape[1]}")
                    st.caption(f"Columns: {', '.join(table.columns)}")
                    if table.sample_rows:
                        st.table(list(table.sample_rows))
                    else:
                        st.info("No sample rows available.")

        copy_col, report_col = st.columns(2)
        with copy_col:
            st.markdown("**Copy for ChatGPT**")
            components.html(
                copy_button_html(
                    "Copy for ChatGPT",
                    prepared.chatgpt_payload,
                    element_id="copy-chatgpt",
                ),
                height=55,
            )
        with report_col:
            st.markdown("**Copy report**")
            components.html(
                copy_button_html("Copy report", prepared.markdown, element_id="copy-report"),
                height=55,
            )

        st.markdown("## Downloads")
        if prepared.response is None:
            st.info("Downloads are available after a successful fetch.")
        else:
            download_artifacts = build_download_artifacts(prepared.response)
            st.caption("Download the current report artifacts directly from the fetched response.")
            combined_col, workbook_col, report_download_col = st.columns(3)
            with combined_col:
                st.markdown("**Combined CSV**")
                st.download_button(
                    "Download combined CSV",
                    data=download_artifacts.combined_csv_bytes,
                    file_name=download_artifacts.combined_csv_filename,
                    mime="text/csv",
                    use_container_width=True,
                )
            with workbook_col:
                st.markdown("**Excel workbook**")
                st.download_button(
                    "Download Excel workbook",
                    data=download_artifacts.workbook_bytes,
                    file_name=download_artifacts.workbook_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            with report_download_col:
                st.markdown("**Report Markdown**")
                st.download_button(
                    "Download Markdown report",
                    data=prepared.markdown,
                    file_name=prepared.filename,
                    mime="text/markdown",
                    use_container_width=True,
                )

            with st.expander("CSV preview", expanded=False):
                st.caption("First 80 CSV lines")
                st.code(download_artifacts.combined_csv_preview, language="csv")

            with st.expander("Section-specific download controls", expanded=False):
                section_summary_col, section_holdings_col = st.columns(2)
                with section_summary_col:
                    st.markdown("**Raw Preview Summary CSV**")
                    st.download_button(
                        "Download Raw Preview Summary CSV",
                        data=download_artifacts.raw_preview_summary_bytes,
                        file_name=download_artifacts.raw_preview_summary_filename,
                        mime="text/csv",
                        use_container_width=True,
                    )
                with section_holdings_col:
                    st.markdown("**Raw Preview Holdings CSV**")
                    st.download_button(
                        "Download Raw Preview Holdings CSV",
                        data=download_artifacts.raw_preview_holdings_bytes,
                        file_name=download_artifacts.raw_preview_holdings_filename,
                        mime="text/csv",
                        use_container_width=True,
                    )

        with st.expander("Raw Markdown", expanded=False):
            st.code(prepared.markdown, language="markdown")

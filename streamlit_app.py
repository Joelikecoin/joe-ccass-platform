import asyncio
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.config import get_settings
from app.errors import PlatformError
from app.services.ccass import get_ccass_service
from app.streamlit_ui import copy_button_html, prepare_report
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
st.set_page_config(page_title="HK CCASS Shareholding Analysis Tool", page_icon="📊", layout="wide")
st.title("HK CCASS Shareholding Analysis Tool")
st.caption(
    "Low-frequency research tool. CCASS is settlement-layer nominee data, normally subject to T+2."
)

with st.sidebar:
    st.header("Options")
    holdings_limit = st.slider("Holdings limit", min_value=5, max_value=100, value=20, step=5)
    big_change_threshold = st.number_input(
        "Big change threshold (shares)",
        min_value=0,
        value=1_000_000,
        step=100_000,
    )
    show_rendered_markdown = st.checkbox("Show rendered Markdown", value=True)
    use_local_history = st.checkbox("Use local SQLite history for Changes", value=True)
    st.divider()
    settings = get_settings()
    st.caption(f"Data source mode: {settings.data_source}")
    st.caption("HKEX SDW: manual verification only; no automated access.")

with st.form("ccass-query"):
    raw_code = st.text_input("Stock code", placeholder="e.g. 1592 → 01592", max_chars=5)
    submitted = st.form_submit_button("Fetch", type="primary", use_container_width=True)

if submitted:
    progress_bar = st.progress(0, text="Starting")

    def update_progress(value: int, label: str) -> None:
        progress_bar.progress(value, text=label)

    try:
        sqlite_path = Path(os.getenv("CCASS_SQLITE_PATH", "data/ccass_snapshots.db"))
        previous_loader = None
        if use_local_history and sqlite_path.is_file():
            store = SnapshotStore(sqlite_path)

            def load_previous(response):
                return store.previous_for(response.metadata.code, response)

            previous_loader = load_previous
        prepared = asyncio.run(
            prepare_report(
                raw_code,
                holdings_limit=holdings_limit,
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

        copy_col, report_col, download_col = st.columns(3)
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
        with download_col:
            st.markdown("**Download**")
            st.download_button(
                "Download .md",
                data=prepared.markdown,
                file_name=prepared.filename,
                mime="text/markdown",
                use_container_width=True,
            )

        with st.expander("Raw Markdown", expanded=False):
            st.code(prepared.markdown, language="markdown")

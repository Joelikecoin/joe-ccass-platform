from __future__ import annotations

import asyncio
import html
import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from functools import lru_cache
from math import ceil
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, StreamingResponse

from app.config import get_settings
from app.errors import PlatformError
from app.live_product import (
    build_live_download_artifacts,
    build_live_preview_tables,
    build_live_product_from_response_with_surfaces,
    render_live_markdown,
)
from app.services.ccass import RepositorySnapshotBackend, get_ccass_service
from app.sources.registry import build_source_registry
from app.storage.history import NormalizedSnapshotRepository
from app.streamlit_ui import (
    build_download_artifacts,
    build_raw_preview_tables,
    nav_text,
    prepare_report,
    render_prepared_report,
    resolve_streamlit_query_input,
    ui_text,
)
from ccass_core.collector import SnapshotStore
from ccass_core.normalize import normalize_stock_code


APP_TITLE_EN = "Joe Visual Portal"
APP_TITLE_ZH = "Joe Visual Portal"
APP_SUBTITLE_EN = "Golden Joe reference portal for live market news and CCASS holdings."
APP_SUBTITLE_ZH = "Golden Joe 參考入口：即時市場資訊與 CCASS 持股。"
DEFAULT_CODE = "00700"


class _LocalSnapshotService:
    """Service adapter for the portal's explicit persisted-read mode."""

    def __init__(self, repository: NormalizedSnapshotRepository, max_age_seconds: int) -> None:
        self._backend = RepositorySnapshotBackend(repository, max_age_seconds=max_age_seconds)

    async def get_stock_data(self, code: str, holdings_limit: int = 15, requested_date=None):
        return await self._backend.get_holdings(code, limit=holdings_limit)


def _escape(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _i18n(en: str, zh: str, locale: str) -> str:
    current = zh if locale == "zh_HK" else en
    return (
        f'<span data-i18n-en="{_escape(en)}" data-i18n-zh="{_escape(zh)}">{_escape(current)}</span>'
    )


def _format_int(value: int | None) -> str:
    return "—" if value is None else f"{value:,}"


def _format_float(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def _format_percent(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:.{digits}f}%"


def _format_date(value: date | None) -> str:
    return "—" if value is None else value.isoformat()


def _format_datetime(value: datetime | None) -> str:
    return "—" if value is None else value.isoformat(sep=" ", timespec="seconds")


def _pill(text: str, tone: str = "neutral") -> str:
    return f'<span class="pill pill-{tone}">{_escape(text)}</span>'


def _metric_card(title_en: str, title_zh: str, value: str, note: str = "", tone: str = "primary") -> str:
    note_html = f'<div class="metric-note">{_escape(note)}</div>' if note else ""
    return (
        f'<div class="metric-card metric-{tone}">'
        f'<div class="metric-title">{_i18n(title_en, title_zh, "en")}</div>'
        f'<div class="metric-value">{_escape(value)}</div>'
        f"{note_html}"
        f"</div>"
    )


def _table(headers: list[str], rows: list[list[str]], *, class_name: str = "") -> str:
    head = "".join(f"<th>{_escape(header)}</th>" for header in headers)
    body_rows = []
    for row in rows:
        body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    empty_row = '<tr><td colspan="999" class="empty-cell">—</td></tr>'
    body_html = "".join(body_rows) if body_rows else empty_row
    return (
        f'<div class="table-wrap {class_name}">'
        f"<table>"
        f"<thead><tr>{head}</tr></thead>"
        f"<tbody>{body_html}</tbody>"
        f"</table>"
        f"</div>"
    )


def _kv_table(rows: list[tuple[str, str]]) -> str:
    html_rows = []
    for label, value in rows:
        html_rows.append(
            f"<tr><th>{_escape(label)}</th><td>{value}</td></tr>"
        )
    return f'<table class="kv-table"><tbody>{"".join(html_rows)}</tbody></table>'


def _sparkline(values: list[float], *, width: int = 420, height: int = 120) -> str:
    if not values:
        return '<div class="empty-state">—</div>'
    lo = min(values)
    hi = max(values)
    span = hi - lo or 1.0
    pad_x = 8
    pad_y = 10
    usable_w = width - 2 * pad_x
    usable_h = height - 2 * pad_y
    points: list[str] = []
    for index, value in enumerate(values):
        x = pad_x + usable_w * (index / max(1, len(values) - 1))
        y = pad_y + usable_h * (1 - ((value - lo) / span))
        points.append(f"{x:.1f},{y:.1f}")
    polyline = " ".join(points)
    return (
        f'<svg viewBox="0 0 {width} {height}" class="sparkline" aria-hidden="true">'
        f'<polyline points="{polyline}" />'
        f"</svg>"
    )


def _section_heading(section_id: str, title_en: str, title_zh: str, locale: str, *, kicker: str = "") -> str:
    kicker_html = f'<div class="kicker">{_escape(kicker)}</div>' if kicker else ""
    return (
        f'<section id="{_escape(section_id)}" class="panel">'
        f'{kicker_html}<h2>{_i18n(title_en, title_zh, locale)}</h2>'
    )


def _close_section() -> str:
    return "</section>"


@dataclass(slots=True)
class PortalBundle:
    requested_code: str
    resolved_code: str
    input_type: str
    source_mode: str
    top_n: int
    big_change_threshold: int
    use_local_history: bool
    live_product: Any | None
    prepared: Any | None
    live_markdown_en: str
    live_markdown_zh: str
    ccass_markdown_en: str
    ccass_markdown_zh: str
    live_artifacts: Any | None
    ccass_artifacts: Any | None
    previous_available: bool
    error_message: str | None = None
    timeout_seconds: float = 12.0
    announcement_period: str = "All"
    data_date: date = field(default_factory=date.today)
    history_range: str = "Latest"
    percentage_basis: str = "CCASS"


def _ensure_portal_defaults() -> None:
    os.environ.setdefault("HKEX_SDW_ENABLED", "true")
    os.environ.setdefault("DATA_SOURCE", "auto")
    get_settings.cache_clear()
    get_ccass_service.cache_clear()


@lru_cache(maxsize=1)
def _settings_sqlite_path() -> Path:
    return get_settings().ccass_sqlite_path


def _resolve_requested_code(raw_code: str, input_type: str) -> str:
    if input_type == "Webb-site Issue ID":
        sqlite_path = _settings_sqlite_path()
        if not sqlite_path.is_file():
            raise PlatformError(
                "NOT_FOUND",
                "No verified stock code is available for the requested Webb-site issue ID.",
                status_code=404,
            )
        repository = NormalizedSnapshotRepository(sqlite_path)
        return resolve_streamlit_query_input(raw_code, input_type, repository=repository)
    return resolve_streamlit_query_input(raw_code, input_type)


async def _build_bundle(
    *,
    raw_code: str,
    input_type: str,
    source_mode: str,
    top_n: int,
    big_change_threshold: int,
    use_local_history: bool,
    timeout_seconds: float = 12.0,
    announcement_period: str = "All",
    data_date: date | None = None,
    history_range: str = "Latest",
    percentage_basis: str = "CCASS",
) -> PortalBundle:
    _ensure_portal_defaults()
    # ``local_db`` is a portal read preference, not a Settings.data_source
    # value.  Keep the persisted-read intent at the service layer while
    # routing configuration through the supported automatic path.
    os.environ["DATA_SOURCE"] = "auto" if source_mode == "local_db" else source_mode
    os.environ["REQUEST_TIMEOUT_SECONDS"] = str(timeout_seconds)
    get_settings.cache_clear()
    get_ccass_service.cache_clear()

    resolved_code = (
        normalize_stock_code(raw_code)
        if source_mode == "local_db" and input_type == "Stock Code"
        else _resolve_requested_code(raw_code, input_type)
    )

    sqlite_path = _settings_sqlite_path()
    previous_loader = None
    previous_snapshot = None
    if use_local_history and sqlite_path.is_file():
        store = SnapshotStore(sqlite_path)

        def _load_previous(response):
            return store.previous_for(response.metadata.code, response)

        previous_loader = _load_previous

    report_service = get_ccass_service()
    if source_mode == "local_db":
        report_service = _LocalSnapshotService(
            NormalizedSnapshotRepository(sqlite_path),
            max_age_seconds=get_settings().holdings_lkg_max_age_seconds,
        )
    ccass_task = prepare_report(
        resolved_code,
        holdings_limit=top_n,
        big_change_threshold=big_change_threshold,
        service=report_service,
        locale="en",
        requested_date=data_date,
        previous_loader=previous_loader,
    )
    prepared = await ccass_task
    product_kwargs = {"code": resolved_code, "source_trace": prepared.source_trace}
    if source_mode == "local_db":
        product_kwargs["allow_external"] = False
        product_kwargs["source_mode"] = source_mode
    live_product = await build_live_product_from_response_with_surfaces(
        prepared.response, **product_kwargs
    )

    if previous_loader and prepared.response is not None:
        try:
            previous_snapshot = previous_loader(prepared.response)
        except Exception:
            previous_snapshot = None

    live_markdown_en = render_live_markdown(live_product, locale="en") if live_product else ""
    live_artifacts = build_live_download_artifacts(live_product) if live_product else None
    ccass_artifacts = build_download_artifacts(prepared.response) if prepared.response is not None else None

    return PortalBundle(
        requested_code=raw_code,
        resolved_code=resolved_code,
        input_type=input_type,
        source_mode=source_mode,
        top_n=top_n,
        big_change_threshold=big_change_threshold,
        use_local_history=use_local_history,
        live_product=live_product,
        prepared=prepared,
        live_markdown_en=live_markdown_en,
        live_markdown_zh="",
        ccass_markdown_en="",
        ccass_markdown_zh="",
        live_artifacts=live_artifacts,
        ccass_artifacts=ccass_artifacts,
        previous_available=previous_snapshot is not None,
        timeout_seconds=timeout_seconds,
        announcement_period=announcement_period,
        data_date=data_date or date.today(),
        history_range=history_range,
        percentage_basis=percentage_basis,
    )


def _bundle_markdown(bundle: PortalBundle, section: str, locale: str) -> str:
    if section == "live":
        if locale == "zh_HK":
            return render_live_markdown(bundle.live_product, locale=locale) if bundle.live_product else ""
        return bundle.live_markdown_en
    if section == "ccass":
        if bundle.prepared is None:
            return ""
        markdown, _ = render_prepared_report(bundle.prepared, locale=locale)
        return markdown
    raise PlatformError("NOT_FOUND", f"Unsupported markdown section: {section}", status_code=404)


def _live_summary_cards(bundle: PortalBundle) -> str:
    if bundle.live_product is None:
        return '<div class="empty-state">Live product unavailable.</div>'
    result = bundle.live_product
    company = result.company or {}
    latest = result.latest_price or {}
    diagnostics = result.diagnostics or []
    status = diagnostics[0].status if diagnostics else "UNKNOWN"
    fetched_at = _format_datetime(getattr(result, "fetched_at", None))
    rows = [
        _metric_card("Stock Code", "股票代號", result.code, tone="primary"),
        _metric_card("Company", "公司", str(company.get("company_name") or "—"), tone="secondary"),
        _metric_card("Latest Price", "最新價格", str(latest.get("price_display") or "—"), tone="accent"),
        _metric_card("Announcements", "公告", f"{len(result.announcements):,}", tone="muted"),
        _metric_card("Status", "狀態", status, note=f"Fetched {fetched_at}", tone="success"),
    ]
    return f'<div class="metric-grid">{"".join(rows)}</div>'


def _company_block(bundle: PortalBundle) -> str:
    result = bundle.live_product
    if result is None:
        return '<div class="empty-state">Company data unavailable.</div>'
    company = result.company or {}
    latest = result.latest_price or {}
    rows = [
        ("Stock Code", _escape(result.code)),
        ("Yahoo Symbol", _escape(result.symbol)),
        ("Company Name", _escape(company.get("company_name") or "—")),
        ("Short Name", _escape(company.get("short_name") or "—")),
        ("Exchange", _escape(company.get("exchange") or "—")),
        ("Sector", _escape(company.get("sector") or "—")),
        ("Industry", _escape(company.get("industry") or "—")),
        ("Currency", _escape(company.get("currency") or "—")),
        ("Fetched At", _escape(company.get("fetched_at") or "—")),
    ]
    latest_rows = [
        ("Price", _escape(latest.get("price_display") or "—")),
        ("Change", _escape(latest.get("change_display") or "—")),
        ("Market State", _escape(latest.get("market_state") or "—")),
        ("Market Time", _escape(latest.get("market_time") or "—")),
        ("Fallback Used", _escape("Yes" if latest.get("fallback_used") else "No")),
    ]
    return (
        '<div class="two-col">'
        f'<div class="subcard"><h3>Company / Metadata</h3>{_kv_table(rows)}</div>'
        f'<div class="subcard"><h3>Latest Price</h3>{_kv_table(latest_rows)}</div>'
        "</div>"
    )


def _price_history_block(bundle: PortalBundle) -> str:
    result = bundle.live_product
    if result is None:
        return '<div class="empty-state">Price history unavailable.</div>'
    values = [float(row.get("close") or 0) for row in result.price_history if row.get("close") is not None]
    rows = []
    for row in result.price_history[:20]:
        rows.append(
            [
                _escape(row.get("date") or "—"),
                _escape(row.get("open") or "—"),
                _escape(row.get("high") or "—"),
                _escape(row.get("low") or "—"),
                _escape(row.get("close") or "—"),
                _escape(row.get("volume") or "—"),
            ]
        )
    return (
        '<div class="subcard">'
        f"<div class=\"chart-header\"><h3>Price History</h3><div class=\"source-note\">{_escape('Yahoo Finance')}</div></div>"
        f'<div class="sparkline-shell">{_sparkline(values)}</div>'
        f'{_table(["Date", "Open", "High", "Low", "Close", "Volume"], rows, class_name="compact-table")}'
        "</div>"
    )


def _announcement_block(title_en: str, title_zh: str, rows: list[dict[str, object]], locale: str, *, empty_text: str) -> str:
    if not rows:
        return f'<div class="empty-state">{_escape(empty_text)}</div>'
    rendered_rows: list[list[str]] = []
    for row in rows[:12]:
        rendered_rows.append(
            [
                _escape(row.get("publish_time") or "—"),
                _escape(row.get("category") or "—"),
                _escape(row.get("title") or "—"),
                _escape(row.get("file_info") or "—"),
                f'<a href="{_escape(row.get("official_url") or "#")}" target="_blank" rel="noreferrer">{_escape(row.get("official_url") or "—")}</a>',
                _escape(row.get("event_tags") or "—"),
            ]
        )
    return (
        '<div class="subcard">'
        f'<h3>{_i18n(title_en, title_zh, locale)}</h3>'
        f'{_table(["Publish Time", "Category", "Title", "File", "Official URL", "Event Tags"], rendered_rows, class_name="compact-table")}'
        "</div>"
    )


def _ccass_summary(bundle: PortalBundle, locale: str) -> str:
    prepared = bundle.prepared
    if prepared is None or prepared.response is None:
        return '<div class="empty-state">CCASS data unavailable.</div>'
    response = prepared.response
    md = response.metadata
    summary = response.holdings_summary
    requested_date = getattr(md, "requested_date", None) or md.holdings_date or md.data_as_of
    acquisition_method = getattr(md, "acquisition_method", None) or getattr(md, "source_name", None) or "—"
    rows = [
        ("Code", _escape(md.code)),
        ("Issue ID", _escape(md.issue_id)),
        ("Requested Date", _escape(_format_date(requested_date))),
        ("Holdings Date", _escape(_format_date(md.holdings_date))),
        ("Fetched At", _escape(_format_datetime(md.fetched_at))),
        ("Source Name", _escape(md.source_name)),
        ("Acquisition", _escape(acquisition_method)),
        ("Cached", _escape("Yes" if md.cached else "No")),
    ]
    metrics = [
        _metric_card("Participants", "參與者", _format_int(summary.participant_count), tone="primary"),
        _metric_card("Top 5 % Issued", "前 5 持股佔已發行", _format_percent(summary.top5_pct_of_issued), tone="accent"),
        _metric_card("Top 10 % Issued", "前 10 持股佔已發行", _format_percent(summary.top10_pct_of_issued), tone="accent"),
        _metric_card("Top 5 % CCASS", "前 5 持股佔 CCASS", _format_percent(summary.top5_pct_of_ccass), tone="muted"),
        _metric_card("Top 10 % CCASS", "前 10 持股佔 CCASS", _format_percent(summary.top10_pct_of_ccass), tone="muted"),
    ]
    return (
        f'<div class="subcard"><h3>{_i18n("CCASS Metadata", "CCASS 元資料", locale)}</h3>{_kv_table(rows)}</div>'
        f'<div class="metric-grid">{"" .join(metrics)}</div>'
    )


def _holdings_table(bundle: PortalBundle) -> str:
    prepared = bundle.prepared
    if prepared is None or prepared.response is None:
        return '<div class="empty-state">Holdings unavailable.</div>'
    rows: list[list[str]] = []
    for row in prepared.response.holdings[: bundle.top_n]:
        rows.append(
            [
                _escape(row.rank),
                _escape(row.participant_id),
                _escape(row.participant),
                _escape(f"{row.shares:,}"),
                _escape(_format_percent(row.pct_of_issued, 4)),
                _escape(_format_percent(row.pct_of_ccass, 4)),
                _escape(_format_date(row.last_change)),
                _escape(row.participant_category or "—"),
            ]
        )
    headers = ["Rank", "Participant ID", "Participant", "Shares", "% Issued", "% CCASS", "Last Change", "Category"]
    return _table(headers, rows, class_name="holdings-table")


def _changes_block(bundle: PortalBundle, locale: str) -> str:
    prepared = bundle.prepared
    if prepared is None or prepared.analysis is None or prepared.response is None:
        return '<div class="empty-state">Changes unavailable.</div>'
    response_big_changes_obj = getattr(prepared.response, "big_changes", None)
    response_big_changes = getattr(response_big_changes_obj, "big_changes", []) or []
    analysis_big_changes = getattr(prepared.analysis, "big_changes", []) if prepared.analysis is not None else []
    big_changes_count = len(response_big_changes or analysis_big_changes)
    rows: list[list[str]] = []
    for change in prepared.analysis.changes[: bundle.top_n]:
        rows.append(
            [
                _escape(change.participant_id),
                _escape(change.participant),
                _escape(f"{change.previous_shares:,}"),
                _escape(f"{change.current_shares:,}"),
                _escape(f"{change.share_change:+,}"),
                _escape(_format_percent(change.previous_pct_of_issued, 4)),
                _escape(_format_percent(change.current_pct_of_issued, 4)),
                _escape(_format_percent(change.pct_point_change, 4)),
                _escape(change.status),
            ]
        )
    metrics = [
        _metric_card("Changed rows", "變動列數", _format_int(len(prepared.analysis.changes)), tone="primary"),
        _metric_card("Big changes", "大變動", _format_int(big_changes_count), tone="accent"),
        _metric_card("Previous snapshot", "上一份快照", "YES" if prepared.analysis.previous_available else "NO", tone="muted"),
    ]
    return (
        f'<div class="metric-grid">{"".join(metrics)}</div>'
        f'{_table(["Participant ID", "Participant", "Previous Shares", "Current Shares", "Change", "Prev % Issued", "Curr % Issued", "Pct Point Change", "Status"], rows, class_name="changes-table")}'
    )


def _big_changes_block(bundle: PortalBundle) -> str:
    prepared = bundle.prepared
    if prepared is None or prepared.response is None:
        return '<div class="empty-state">Big changes unavailable.</div>'
    response_big_changes_obj = getattr(prepared.response, "big_changes", None)
    response_big_changes = getattr(response_big_changes_obj, "big_changes", []) or []
    analysis_big_changes = getattr(prepared.analysis, "big_changes", []) if prepared.analysis is not None else []
    rows_source = response_big_changes or analysis_big_changes
    source_status = (
        getattr(response_big_changes_obj, "source_status", None)
        or ("local_derived" if getattr(prepared.analysis, "previous_available", False) else "unavailable")
    )
    authority_status = (
        getattr(response_big_changes_obj, "authority_status", None)
        or ("local_history_limited" if getattr(prepared.analysis, "previous_available", False) else "unavailable")
    )
    status_banner = (
        f'<div class="warning-box"><strong>Authority status:</strong> {_escape(authority_status.upper())} '
        f'· <strong>Source status:</strong> {_escape(source_status.upper())}</div>'
    )
    rows: list[list[str]] = []
    for change in rows_source[: bundle.top_n]:
        rows.append(
            [
                _escape(change.participant_id),
                _escape(change.participant),
                _escape(f"{change.shares_before:,}"),
                _escape(f"{change.shares_after:,}"),
                _escape(f"{change.shares_change:+,}"),
                _escape(change.status),
            ]
        )
    if not rows:
        return (
            status_banner
            + '<div class="empty-state">No big changes at the current threshold.</div>'
        )
    return (
        status_banner
        + _table(
        ["Participant ID", "Participant", "Previous Shares", "Current Shares", "Change", "Status"],
        rows,
        class_name="big-changes-table",
        )
    )


def _concentration_block(bundle: PortalBundle) -> str:
    prepared = bundle.prepared
    if prepared is None or prepared.analysis is None or prepared.response is None:
        return '<div class="empty-state">Concentration unavailable.</div>'
    concentration = prepared.analysis.concentration
    metrics = [
        _metric_card("Participant Count", "參與者數", _format_int(int(concentration.get("participant_count") or 0)), tone="primary"),
        _metric_card("Top 5 % Issued", "前 5 持股佔已發行", _format_percent(float(concentration.get("top5_pct_of_issued") or 0)), tone="accent"),
        _metric_card("Top 10 % Issued", "前 10 持股佔已發行", _format_percent(float(concentration.get("top10_pct_of_issued") or 0)), tone="accent"),
        _metric_card("Top 5 % CCASS", "前 5 持股佔 CCASS", _format_percent(float(concentration.get("top5_pct_of_ccass") or 0)), tone="muted"),
        _metric_card("Top 10 % CCASS", "前 10 持股佔 CCASS", _format_percent(float(concentration.get("top10_pct_of_ccass") or 0)), tone="muted"),
    ]
    top_rows = []
    for row in prepared.response.holdings[:10]:
        top_rows.append(
            [
                _escape(row.rank),
                _escape(row.participant_id),
                _escape(row.participant),
                _escape(f"{row.shares:,}"),
                _escape(_format_percent(row.pct_of_issued, 4)),
                _escape(_format_percent(row.pct_of_ccass, 4)),
            ]
        )
    return (
        f'<div class="metric-grid">{"".join(metrics)}</div>'
        f'{_table(["Rank", "Participant ID", "Participant", "Shares", "% Issued", "% CCASS"], top_rows, class_name="concentration-table")}'
    )


def _concentration_history_block(bundle: PortalBundle) -> str:
    if not bundle.previous_available or bundle.prepared is None or bundle.prepared.response is None:
        return '<div class="empty-state">Insufficient history for concentration comparison.</div>'
    response = bundle.prepared.response
    summary = response.holdings_summary
    rows = [
        ["Current", _escape(_format_date(response.metadata.holdings_date)), _escape(_format_percent(summary.top5_pct_of_issued)), _escape(_format_percent(summary.top10_pct_of_issued))],
    ]
    return _table(["Series", "Holdings Date", "Top 5 % Issued", "Top 10 % Issued"], rows, class_name="history-table")


def _raw_preview_block(bundle: PortalBundle, locale: str) -> str:
    prepared = bundle.prepared
    if prepared is None or prepared.response is None:
        return '<div class="empty-state">Raw previews unavailable.</div>'
    live_tables = build_live_preview_tables(bundle.live_product, locale=locale) if bundle.live_product else ()
    ccass_tables = build_raw_preview_tables(prepared.response, locale=locale)
    sections = []
    empty_preview = '<div class="empty-state">—</div>'
    for table in live_tables:
        title = _escape(f"{table.table_index}. {table.title}")
        shape = _escape(f"{table.shape[0]} × {table.shape[1]}")
        sample_html = _table(list(table.columns), [list(row.values()) for row in table.sample_rows], class_name="preview-table") if table.sample_rows else empty_preview
        sections.append(
            f'<details class="preview-details"><summary>{title}</summary>'
            f'<div class="preview-meta">{shape}</div>'
            f"{sample_html}"
            "</details>"
        )
    for table in ccass_tables:
        title = _escape(f"{table.table_index}. {table.title}")
        shape = _escape(f"{table.shape[0]} × {table.shape[1]}")
        sample_html = _table(list(table.columns), [list(row.values()) for row in table.sample_rows], class_name="preview-table") if table.sample_rows else empty_preview
        sections.append(
            f'<details class="preview-details"><summary>{title}</summary>'
            f'<div class="preview-meta">{shape}</div>'
            f"{sample_html}"
            "</details>"
        )
    return "".join(sections)


def _download_links(bundle: PortalBundle) -> str:
    if bundle.live_artifacts is None and bundle.ccass_artifacts is None:
        return '<div class="empty-state">Downloads appear after a stock is fetched.</div>'
    query = {
        "code": bundle.resolved_code,
        "input_type": bundle.input_type,
        "source_mode": bundle.source_mode,
        "timeout_seconds": bundle.timeout_seconds,
        "announcement_period": bundle.announcement_period,
        "data_date": bundle.data_date.isoformat(),
        "history_range": bundle.history_range,
        "top_n": bundle.top_n,
        "percentage_basis": bundle.percentage_basis,
        "big_change_threshold": bundle.big_change_threshold,
        "use_local_history": "true" if bundle.use_local_history else "false",
    }
    base = urlencode(query)
    links = [
        ("live", "csv", "Download Live CSV", "下載即時 CSV"),
        ("live", "xlsx", "Download Live Excel", "下載即時 Excel"),
        ("live", "json", "Download Live JSON", "下載即時 JSON"),
        ("live", "md", "Download Live Markdown", "下載即時 Markdown"),
        ("ccass", "csv", "Download All Data CSV", "下載所有數據 CSV"),
        ("ccass", "xlsx", "Download Excel", "下載 Excel"),
        ("ccass", "json", "Download CCASS JSON", "下載 CCASS JSON"),
        ("ccass", "md", "Download Markdown Report", "下載 Markdown 報告"),
        ("raw_previews", "json", "Download Raw Tables JSON", "下載原始表格 JSON"),
    ]
    if bundle.ccass_artifacts is not None:
        links.extend(
            [
                ("raw_previews", "summary_csv", "Download Raw Preview Summary CSV", "下載原始表格摘要 CSV"),
                ("raw_previews", "holdings_csv", "Download Raw Preview Holdings CSV", "下載原始表格持倉 CSV"),
            ]
        )
    if bundle.prepared is not None:
        links.extend(
            [
                ("holdings", "csv", "Download Holdings CSV", "下載持股 CSV"),
                ("changes", "csv", "Download Changes CSV", "下載變動 CSV"),
                ("big_changes", "csv", "Download Big Changes CSV", "下載大變動 CSV"),
                ("concentration", "csv", "Download Concentration CSV", "下載集中度 CSV"),
                ("announcements", "csv", "Download Announcements CSV", "下載公告 CSV"),
                ("price_history", "csv", "Download Price CSV", "下載價格 CSV"),
            ]
        )
    sqlite_path = get_settings().ccass_sqlite_path
    if sqlite_path.is_file():
        links.append(("ccass", "sqlite", "Download SQLite Backup", "下載 SQLite 備份"))
    items = []
    for section, kind, en, zh in links:
        href = f"/download/{section}/{kind}?{base}"
        items.append(
            f'<a class="download-btn" data-i18n-en="{_escape(en)}" data-i18n-zh="{_escape(zh)}" href="{_escape(href)}">{_escape(en)}</a>'
        )
    return "".join(items)


def _copy_blocks(bundle: PortalBundle) -> str:
    live_en = _escape(bundle.live_markdown_en)
    live_zh = _escape(bundle.live_markdown_zh)
    ccass_en = _escape(bundle.ccass_markdown_en)
    ccass_zh = _escape(bundle.ccass_markdown_zh)
    return (
        f'<textarea id="copy-live-en" class="copy-store" readonly>{live_en}</textarea>'
        f'<textarea id="copy-live-zh" class="copy-store" readonly>{live_zh}</textarea>'
        f'<textarea id="copy-ccass-en" class="copy-store" readonly>{ccass_en}</textarea>'
        f'<textarea id="copy-ccass-zh" class="copy-store" readonly>{ccass_zh}</textarea>'
    )


def _render_page(bundle: PortalBundle) -> str:
    locale = "en"
    title = APP_TITLE_EN
    subtitle = APP_SUBTITLE_EN
    status_text = "LIVE CCASS + bilingual portal"
    if bundle.error_message:
        status_text = bundle.error_message

    if bundle.live_product and bundle.prepared and bundle.prepared.response is not None:
        live_status = "READY"
    else:
        live_status = "PARTIAL"

    ccass_error_html = ""
    if bundle.prepared and bundle.prepared.fetch_error:
        ccass_error_html = f"<div class='error-box'>{_escape(bundle.prepared.fetch_error)}</div>"
    live_error_html = ""
    if bundle.live_product is None and bundle.error_message:
        live_error_html = f"<div class='error-box'>{_escape(bundle.error_message)}</div>"

    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(title)}</title>
  <style>
    :root {{
      --bg: #eef2f7;
      --panel: #ffffff;
      --panel-soft: #f6f8fc;
      --ink: #132238;
      --muted: #63708a;
      --line: rgba(18, 31, 54, 0.12);
      --brand: #16396b;
      --brand-2: #1d63a8;
      --accent: #18a0ff;
      --good: #1f8f5f;
      --warn: #c47a12;
      --shadow: 0 18px 48px rgba(17, 31, 56, 0.12);
      color-scheme: light;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, "Segoe UI", "Noto Sans TC", "PingFang TC", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(24, 160, 255, 0.10), transparent 32%),
        radial-gradient(circle at top right, rgba(22, 57, 107, 0.08), transparent 28%),
        var(--bg);
      color: var(--ink);
    }}
    a {{ color: inherit; }}
    .shell {{
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 20;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 1rem 1.5rem;
      background: rgba(255,255,255,0.88);
      backdrop-filter: blur(14px);
      border-bottom: 1px solid var(--line);
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.9rem;
    }}
    .brand-mark {{
      width: 2.8rem;
      height: 2.8rem;
      border-radius: 0.9rem;
      background: linear-gradient(135deg, var(--brand), var(--brand-2));
      color: white;
      display: grid;
      place-items: center;
      font-size: 1.1rem;
      font-weight: 800;
      box-shadow: var(--shadow);
    }}
    .brand-title {{
      font-size: 1.45rem;
      font-weight: 800;
      line-height: 1.1;
    }}
    .brand-subtitle {{
      font-size: 0.92rem;
      color: var(--muted);
      margin-top: 0.15rem;
    }}
    .top-right {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }}
    .layout {{
      width: min(1600px, 100%);
      margin: 0 auto;
      padding: 1.25rem;
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      gap: 1.25rem;
    }}
    .sidebar, .panel, .subcard, .hero, .metric-card {{
      background: rgba(255,255,255,0.88);
      border: 1px solid var(--line);
      border-radius: 1.25rem;
      box-shadow: var(--shadow);
    }}
    .sidebar {{
      position: sticky;
      top: 6rem;
      align-self: start;
      padding: 1rem;
    }}
    .sidebar h2 {{
      margin: 0 0 0.5rem 0;
      font-size: 1.1rem;
    }}
    .field {{
      display: grid;
      gap: 0.35rem;
      margin-bottom: 0.8rem;
    }}
    .field label {{
      font-size: 0.82rem;
      color: var(--muted);
      font-weight: 700;
    }}
    .field input, .field select {{
      width: 100%;
      padding: 0.82rem 0.9rem;
      border-radius: 0.85rem;
      border: 1px solid var(--line);
      background: white;
      color: var(--ink);
      outline: none;
      font-size: 0.98rem;
    }}
    .field input:focus, .field select:focus {{
      border-color: rgba(24, 160, 255, 0.7);
      box-shadow: 0 0 0 4px rgba(24, 160, 255, 0.12);
    }}
    .primary-btn, .download-btn, .lang-btn {{
      border: 0;
      border-radius: 0.95rem;
      padding: 0.78rem 1rem;
      font-weight: 800;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.35rem;
      transition: transform 0.15s ease, opacity 0.15s ease, background 0.15s ease;
    }}
    .primary-btn {{
      width: 100%;
      margin-top: 0.35rem;
      color: white;
      background: linear-gradient(135deg, var(--brand), var(--brand-2));
      box-shadow: 0 14px 28px rgba(29, 99, 168, 0.26);
    }}
    .download-btn {{
      color: white;
      background: linear-gradient(135deg, #14548f, #1f8ad1);
      min-width: 10rem;
    }}
    .lang-btn {{
      background: #ebf3ff;
      color: var(--brand);
      border: 1px solid rgba(22, 57, 107, 0.1);
      min-width: 4.2rem;
    }}
    .lang-btn.active {{
      background: linear-gradient(135deg, var(--brand), var(--brand-2));
      color: white;
    }}
    .primary-btn:hover, .download-btn:hover, .lang-btn:hover {{
      transform: translateY(-1px);
      opacity: 0.96;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      padding: 0.3rem 0.65rem;
      border-radius: 999px;
      border: 1px solid transparent;
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.02em;
    }}
    .pill-neutral {{ background: #edf2fb; color: #3d4d68; border-color: rgba(61, 77, 104, 0.12); }}
    .pill-primary {{ background: rgba(24, 160, 255, 0.13); color: #0f5f9c; }}
    .pill-secondary {{ background: rgba(31, 143, 95, 0.12); color: #126947; }}
    .pill-accent {{ background: rgba(22, 57, 107, 0.11); color: var(--brand); }}
    .pill-muted {{ background: #f1f4f8; color: #50617d; }}
    .pill-success {{ background: rgba(31, 143, 95, 0.15); color: #0d6a46; }}
    .hero {{
      padding: 1.25rem;
      margin-bottom: 1rem;
    }}
    .hero-grid, .metric-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 0.85rem;
    }}
    .metric-card {{
      padding: 0.9rem 1rem;
      background: linear-gradient(180deg, #fff, #f7fbff);
    }}
    .metric-title {{
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .metric-value {{
      margin-top: 0.35rem;
      font-size: 1.4rem;
      font-weight: 900;
      line-height: 1.15;
    }}
    .metric-note {{
      margin-top: 0.25rem;
      color: var(--muted);
      font-size: 0.79rem;
    }}
    .main {{
      min-width: 0;
    }}
    .section-nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.55rem;
      margin: 0 0 1rem 0;
    }}
    .section-nav a {{
      text-decoration: none;
      color: var(--brand);
      background: rgba(255,255,255,0.9);
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 0.55rem 0.9rem;
      font-weight: 750;
    }}
    .panel {{
      padding: 1rem;
      margin-bottom: 1rem;
      scroll-margin-top: 7rem;
    }}
    .panel h2 {{
      margin: 0 0 0.85rem 0;
      font-size: 1.18rem;
    }}
    .kicker {{
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 0.2rem;
    }}
    .subcard {{
      padding: 1rem;
      background: white;
      margin-bottom: 0.85rem;
    }}
    .subcard h3 {{
      margin: 0 0 0.75rem 0;
      font-size: 1rem;
    }}
    .two-col {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.85rem;
    }}
    .table-wrap {{
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 0.95rem;
      background: white;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
    }}
    th, td {{
      padding: 0.68rem 0.75rem;
      border-bottom: 1px solid rgba(18, 31, 54, 0.08);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f7f9fc;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #5a6b85;
    }}
    .compact-table th, .compact-table td {{
      padding: 0.55rem 0.65rem;
      font-size: 0.85rem;
    }}
    .empty-state {{
      padding: 1rem;
      color: var(--muted);
      background: #f8fbff;
      border: 1px dashed rgba(18, 31, 54, 0.18);
      border-radius: 0.95rem;
    }}
    .source-note {{
      color: var(--muted);
      font-size: 0.85rem;
      font-weight: 700;
    }}
    .sparkline-shell {{
      margin: 0.75rem 0 1rem 0;
      border: 1px solid var(--line);
      border-radius: 0.95rem;
      background: linear-gradient(180deg, #f9fbff, #ffffff);
      padding: 0.5rem;
    }}
    .sparkline {{
      width: 100%;
      height: 120px;
      display: block;
    }}
    .sparkline polyline {{
      fill: none;
      stroke: #1f8ad1;
      stroke-width: 2.8;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
    .preview-details {{
      border: 1px solid var(--line);
      border-radius: 0.95rem;
      padding: 0.7rem 0.85rem;
      background: white;
      margin-bottom: 0.75rem;
    }}
    .preview-details summary {{
      cursor: pointer;
      font-weight: 800;
    }}
    .preview-meta {{
      color: var(--muted);
      font-size: 0.82rem;
      margin: 0.45rem 0 0.7rem 0;
    }}
    .copy-store {{
      position: absolute;
      left: -9999px;
      width: 1px;
      height: 1px;
      opacity: 0;
    }}
    .copy-row {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.85rem;
    }}
    .copy-card {{
      background: white;
      border: 1px solid var(--line);
      border-radius: 1rem;
      padding: 1rem;
    }}
    .copy-card textarea {{
      width: 100%;
      min-height: 18rem;
      resize: vertical;
      border-radius: 0.8rem;
      border: 1px solid var(--line);
      padding: 0.8rem;
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      font-size: 0.81rem;
      background: #fbfdff;
      color: #24324a;
    }}
    .copy-actions {{
      display: flex;
      gap: 0.5rem;
      margin-bottom: 0.7rem;
      flex-wrap: wrap;
    }}
    .warning-box {{
      border-radius: 1rem;
      padding: 0.85rem 1rem;
      background: #fff6e8;
      border: 1px solid rgba(196, 122, 18, 0.2);
      color: #7a4a0e;
      margin-bottom: 0.85rem;
      white-space: pre-wrap;
    }}
    .error-box {{
      border-radius: 1rem;
      padding: 0.85rem 1rem;
      background: #fff0f0;
      border: 1px solid rgba(189, 52, 52, 0.18);
      color: #8c1d1d;
      margin-bottom: 0.85rem;
      white-space: pre-wrap;
    }}
    details.advanced {{
      border: 1px dashed rgba(18, 31, 54, 0.15);
      border-radius: 0.9rem;
      padding: 0.7rem 0.8rem;
      background: #f8fbff;
      margin-top: 0.6rem;
    }}
    details.advanced summary {{
      cursor: pointer;
      font-weight: 800;
      color: var(--brand);
    }}
    .section-footer {{
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-top: 0.8rem;
    }}
    @media (max-width: 1280px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}
      .sidebar {{
        position: static;
      }}
      .hero-grid, .metric-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .two-col, .copy-row {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 768px) {{
      .topbar {{
        padding: 0.9rem 1rem;
      }}
      .layout {{
        padding: 0.9rem;
      }}
      .hero-grid, .metric-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body data-locale="en">
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">J</div>
        <div>
          <div class="brand-title">{_i18n(APP_TITLE_EN, APP_TITLE_ZH, "en")}</div>
          <div class="brand-subtitle">{_i18n(APP_SUBTITLE_EN, APP_SUBTITLE_ZH, "en")}</div>
        </div>
      </div>
      <div class="top-right">
        {_pill(live_status, "success" if live_status == "READY" else "neutral")}
        <div class="lang-toggle">
          <button class="lang-btn active" data-locale-switch="zh_HK" type="button">繁中</button>
          <button class="lang-btn" data-locale-switch="en" type="button">EN</button>
        </div>
      </div>
    </header>
    <div class="layout">
      <aside class="sidebar">
        <h2>{_i18n("Search / Fetch", "搜尋／擷取", "en")}</h2>
        <form method="get" action="/">
          <div class="field">
            <label>{_i18n("Input type", "輸入類型", "en")}</label>
            <select name="input_type">
              <option value="Stock Code"{" selected" if bundle.input_type == "Stock Code" else ""}>{_i18n("Stock Code", "股票代號", "en")}</option>
              <option value="Webb-site Issue ID"{" selected" if bundle.input_type == "Webb-site Issue ID" else ""}>{_i18n("Webb-site Issue ID", "Webb-site Issue ID", "en")}</option>
            </select>
          </div>
          <div class="field">
            <label>{_i18n("Stock code / issue ID", "股票代號／Issue ID", "en")}</label>
            <input name="code" value="{_escape(bundle.requested_code)}" placeholder="00700" />
          </div>
          <input type="hidden" name="source_mode" value="auto" />
          <button class="primary-btn" type="submit">{_i18n("Fetch", "擷取", "en")}</button>
          <details class="advanced">
            <summary>{_i18n("Advanced settings", "進階設定", "en")}</summary>
            <div style="margin-top:0.75rem;">
              <div class="field">
                <label>{_i18n("Top N holdings", "顯示前 N 筆持股", "en")}</label>
                <input name="top_n" type="number" min="5" max="100" step="5" value="{bundle.top_n}" />
              </div>
              <div class="field">
                <label>{_i18n("Big change threshold", "大變動門檻", "en")}</label>
                <input name="big_change_threshold" type="number" min="0" step="100000" value="{bundle.big_change_threshold}" />
              </div>
              <div class="field">
                <label>
                  <input type="checkbox" name="use_local_history" value="true"{" checked" if bundle.use_local_history else ""} />
                  {_i18n("Use local history", "使用本機歷史", "en")}
                </label>
              </div>
            </div>
          </details>
        </form>
        <div style="margin-top:1rem;">
          <div class="kicker">{_i18n("Current selection", "目前選項", "en")}</div>
          <div style="display:flex; flex-wrap:wrap; gap:0.45rem;">
            {_pill(bundle.resolved_code, "primary")}
            {_pill(bundle.input_type, "neutral")}
          </div>
        </div>
      </aside>
      <main class="main">
        <section class="hero">
          <div class="metric-grid">
            {_metric_card("Resolved code", "已解析代號", bundle.resolved_code, note="Input accepted and normalized.", tone="primary")}
            {_metric_card("Live CCASS", "即時 CCASS", "YES" if bundle.prepared and bundle.prepared.response is not None else "NO", note="HKEX SDW browser acquisition enabled.", tone="success")}
            {_metric_card("Chinese HKEX titles", "HKEX 中文標題", "YES" if bundle.live_product and bundle.live_product.announcements else "NO", note="Official title search language set to Chinese.", tone="accent")}
            {_metric_card("Holdings rows", "持股列數", _format_int(len(bundle.prepared.response.holdings) if bundle.prepared and bundle.prepared.response else None), note="Top rows shown in the portal.", tone="muted")}
            {_metric_card("Previous history", "歷史比較", "YES" if bundle.previous_available else "NO", note="Local snapshot comparison when available.", tone="secondary")}
          </div>
        </section>

        <nav class="section-nav">
          <a href="#overview">{_escape(nav_text("en", "fetch_summary"))}</a>
          <a href="#live-market">Live Market &amp; News</a>
          <a href="#ccass-holdings">{_escape(nav_text("en", "holdings"))}</a>
          <a href="#changes">{_escape(nav_text("en", "changes"))}</a>
          <a href="#big-changes">{_escape(nav_text("en", "big_changes"))}</a>
          <a href="#concentration">{_escape(nav_text("en", "concentration"))}</a>
          <a href="#raw-previews">{_escape(nav_text("en", "raw_previews"))}</a>
          <a href="#downloads">{_escape(nav_text("en", "downloads"))}</a>
          <a href="#copy">{_escape(nav_text("en", "copy_for_chatgpt"))}</a>
        </nav>

        <section id="overview" class="panel">
          <div class="kicker">{_i18n("AI-ready overview", "AI 可讀摘要", "en")}</div>
          <h2>{_i18n("Fetch summary", "擷取摘要", "en")}</h2>
          <div class="metric-grid">
            {_metric_card("Portal", "入口", APP_TITLE_EN, tone="primary")}
            {_metric_card("CCASS source", "CCASS 來源", "HKEX SDW", tone="success")}
            {_metric_card("Acquisition", "擷取方式", "LIVE / Browser", tone="accent")}
            {_metric_card("Source language", "原始語言", "繁體中文" if bundle.live_product and bundle.live_product.announcements else "N/A", tone="muted")}
            {_metric_card("Updated", "更新時間", _format_datetime(bundle.live_product.fetched_at if bundle.live_product else None), tone="secondary")}
          </div>
          <div style="margin-top:0.9rem;">
            {_live_summary_cards(bundle)}
          </div>
          {live_error_html}
          {ccass_error_html}
        </section>

        <section id="live-market" class="panel">
          <div class="kicker">{_i18n("Live market data", "即時市場資料", "en")}</div>
          <h2>{_i18n("Live Market & News", "即時市場與公告", "en")}</h2>
          {_company_block(bundle)}
          <div class="subcard">
            {_price_history_block(bundle)}
          </div>
          <div class="two-col">
            {_announcement_block("HKEX Announcements", "HKEX 公告", bundle.live_product.announcements if bundle.live_product else [], "en", empty_text="No announcement rows available.")}
            {_announcement_block("Corporate Events", "公司事件", bundle.live_product.corporate_events if bundle.live_product else [], "en", empty_text="No corporate event rows available.")}
          </div>
          <div class="two-col">
            {_announcement_block("Share Capital Changes", "股本變動", bundle.live_product.share_capital_changes if bundle.live_product else [], "en", empty_text="No share capital change rows available.")}
            <div class="subcard">
              <h3>Officers / Managers</h3>
              {_table(["Name", "Title", "Age", "Fiscal Year", "Total Pay", "Exercised Value", "Unexercised Value", "Source"], [
                  [
                      _escape(row.get("name") or "—"),
                      _escape(row.get("title") or "—"),
                      _escape(row.get("age") or "—"),
                      _escape(row.get("fiscal_year") or "—"),
                      _escape(row.get("total_pay") or "—"),
                      _escape(row.get("exercised_value") or "—"),
                      _escape(row.get("unexercised_value") or "—"),
                      _escape(row.get("source") or "—"),
                  ] for row in (bundle.live_product.officers[:12] if bundle.live_product else [])
              ], class_name="compact-table")}
            </div>
          </div>
        </section>

        <section id="ccass-holdings" class="panel">
          <div class="kicker">{_i18n("CCASS / holdings", "CCASS／持股", "en")}</div>
          <h2>{_i18n("CCASS Holdings", "CCASS 持股", "en")}</h2>
          {_ccass_summary(bundle, "en")}
          <div style="margin-top:0.85rem;">
            {_holdings_table(bundle)}
          </div>
        </section>

        <section id="changes" class="panel">
          <div class="kicker">{_i18n("Historical comparison", "歷史比較", "en")}</div>
          <h2>{_i18n("Changes", "變動", "en")}</h2>
          {_changes_block(bundle, "en")}
        </section>

        <section id="big-changes" class="panel">
          <div class="kicker">{_i18n("Threshold filtered", "門檻過濾", "en")}</div>
          <h2>{_i18n("Big Changes", "大變動", "en")}</h2>
          {_big_changes_block(bundle)}
        </section>

        <section id="concentration" class="panel">
          <div class="kicker">{_i18n("Distribution view", "分布視圖", "en")}</div>
          <h2>{_i18n("Concentration", "集中度", "en")}</h2>
          {_concentration_block(bundle)}
        </section>

        <section class="panel">
          <div class="kicker">{_i18n("History comparison", "歷史比較", "en")}</div>
          <h2>{_i18n("Concentration History", "集中度歷史", "en")}</h2>
          {_concentration_history_block(bundle)}
        </section>

        <section id="raw-previews" class="panel">
          <div class="kicker">{_i18n("Structured source audit", "結構化來源檢視", "en")}</div>
          <h2>{_i18n("Raw Previews", "原始預覽", "en")}</h2>
          {_raw_preview_block(bundle, "en")}
        </section>

        <section id="downloads" class="panel">
          <div class="kicker">{_i18n("Export", "匯出", "en")}</div>
          <h2>{_i18n("Download This Stock", "下載此股票", "en")}</h2>
          <div class="section-footer">{_download_links(bundle)}</div>
        </section>

        <section id="copy" class="panel">
          <div class="kicker">{_i18n("Clipboard", "剪貼簿", "en")}</div>
          <h2>{_i18n("Copy for ChatGPT / Report", "複製給 ChatGPT／報告", "en")}</h2>
          <div class="copy-row">
            <div class="copy-card">
              <div class="copy-actions">
                <button class="primary-btn" type="button" data-copy-section="live" data-copy-en="copy-live-en" data-copy-zh="copy-live-zh">{_i18n("Copy live markdown", "複製即時 Markdown", "en")}</button>
              </div>
              <textarea id="copy-live-preview" readonly>{_escape(bundle.live_markdown_en)}</textarea>
            </div>
            <div class="copy-card">
              <div class="copy-actions">
                <button class="primary-btn" type="button" data-copy-section="ccass" data-copy-en="copy-ccass-en" data-copy-zh="copy-ccass-zh">{_i18n("Copy CCASS markdown", "複製 CCASS Markdown", "en")}</button>
              </div>
              <textarea id="copy-ccass-preview" readonly>{_escape(bundle.ccass_markdown_en)}</textarea>
            </div>
          </div>
        </section>
      </main>
    </div>
    {_copy_blocks(bundle)}
  </div>
  <script>
    const LOCALE_KEY = "joe-portal-locale";
    const currentQuery = {json.dumps({
        "code": bundle.resolved_code,
        "input_type": bundle.input_type,
        "source_mode": bundle.source_mode,
        "top_n": bundle.top_n,
        "big_change_threshold": bundle.big_change_threshold,
        "use_local_history": "true" if bundle.use_local_history else "false",
    })};

    function selectedLocale() {{
      return localStorage.getItem(LOCALE_KEY) || "en";
    }}

    function markdownUrl(section, locale) {{
      const params = new URLSearchParams(currentQuery);
      params.set("locale", locale);
      return `/download/${{section}}/md?${{params.toString()}}`;
    }}

    function copyStoreId(section, locale) {{
      return section === "live"
        ? (locale === "zh_HK" ? "copy-live-zh" : "copy-live-en")
        : (locale === "zh_HK" ? "copy-ccass-zh" : "copy-ccass-en");
    }}

    function previewId(section) {{
      return section === "live" ? "copy-live-preview" : "copy-ccass-preview";
    }}

    async function ensureMarkdown(section, locale) {{
      const store = document.getElementById(copyStoreId(section, locale));
      if (store && store.value) return store.value;
      const response = await fetch(markdownUrl(section, locale), {{ credentials: "same-origin" }});
      if (!response.ok) {{
        throw new Error(`Markdown fetch failed: ${{response.status}}`);
      }}
      const text = await response.text();
      if (store) {{
        store.value = text;
      }}
      return text;
    }}

    async function syncCopyPreview(section, locale) {{
      const preview = document.getElementById(previewId(section));
      if (!preview) return;
      if (locale !== "zh_HK") {{
        const store = document.getElementById(copyStoreId(section, locale));
        preview.value = store ? store.value : "";
        return;
      }}
      try {{
        preview.value = await ensureMarkdown(section, locale);
      }} catch (error) {{
        preview.value = "";
      }}
    }}

    function applyLocale(locale) {{
      document.body.dataset.locale = locale;
      document.querySelectorAll("[data-i18n-en][data-i18n-zh]").forEach((el) => {{
        el.textContent = locale === "zh_HK" ? el.dataset.i18nZh : el.dataset.i18nEn;
      }});
      document.querySelectorAll("[data-copy-en][data-copy-zh]").forEach((button) => {{
        button.dataset.locale = locale;
      }});
      document.querySelectorAll(".lang-btn").forEach((button) => {{
        button.classList.toggle("active", button.dataset.localeSwitch === locale);
      }});
      document.querySelectorAll("a.download-btn").forEach((link) => {{
        const url = new URL(link.getAttribute("href"), window.location.origin);
        url.searchParams.set("locale", locale);
        link.setAttribute("href", url.pathname + url.search);
      }});
      syncCopyPreview("live", locale);
      syncCopyPreview("ccass", locale);
      document.querySelectorAll("[data-locale]").forEach((node) => {{
        node.dataset.locale = locale;
      }});
    }}

    async function copyCurrent(button) {{
      const locale = selectedLocale();
      const section = button.dataset.copySection || "ccass";
      const id = copyStoreId(section, locale);
      const target = document.getElementById(id);
      if (!target) return;
      if (!target.value) {{
        try {{
          const text = await ensureMarkdown(section, locale);
          target.value = text;
        }} catch (error) {{
          return;
        }}
      }}
      try {{
        await navigator.clipboard.writeText(target.value);
      }} catch (error) {{
        target.focus();
        target.select();
        document.execCommand("copy");
      }}
    }}

    document.addEventListener("click", (event) => {{
      const localeButton = event.target.closest("[data-locale-switch]");
      if (localeButton) {{
        const locale = localeButton.dataset.localeSwitch;
        localStorage.setItem(LOCALE_KEY, locale);
        applyLocale(locale);
        return;
      }}
      const copyButton = event.target.closest("[data-copy-en][data-copy-zh]");
      if (copyButton) {{
        copyCurrent(copyButton);
      }}
    }});

    document.addEventListener("DOMContentLoaded", () => {{
      applyLocale(selectedLocale());
    }});
  </script>
</body>
</html>
"""


app = FastAPI(title=APP_TITLE_EN, version="1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "joe-visual-portal"}


@app.get("/", response_class=HTMLResponse)
async def portal(
    code: str = Query(default=""),
    input_type: str = Query(default="Stock Code"),
    source_mode: str = Query(default="auto"),
    timeout_seconds: float = Query(default=12.0, ge=1.0),
    announcement_period: str = Query(default="All"),
    data_date: date = Query(default=date.today()),
    history_range: str = Query(default="Latest"),
    top_n: int = Query(default=20, ge=5, le=100),
    percentage_basis: str = Query(default="CCASS"),
    big_change_threshold: int = Query(default=1_000_000, ge=0),
    use_local_history: bool = Query(default=True),
) -> HTMLResponse:
    if code.strip():
        try:
            bundle = await _build_bundle(
                raw_code=code,
                input_type=input_type,
                source_mode=source_mode,
                timeout_seconds=timeout_seconds,
                announcement_period=announcement_period,
                data_date=data_date,
                history_range=history_range,
                top_n=top_n,
                percentage_basis=percentage_basis,
                big_change_threshold=big_change_threshold,
                use_local_history=use_local_history,
            )
        except PlatformError as exc:
            bundle = PortalBundle(
                requested_code=code,
                resolved_code=code,
                input_type=input_type,
                source_mode=source_mode,
                timeout_seconds=timeout_seconds,
                announcement_period=announcement_period,
                data_date=data_date,
                history_range=history_range,
                top_n=top_n,
                percentage_basis=percentage_basis,
                big_change_threshold=big_change_threshold,
                use_local_history=use_local_history,
                live_product=None,
                prepared=None,
                live_markdown_en="",
                live_markdown_zh="",
                ccass_markdown_en="",
                ccass_markdown_zh="",
                live_artifacts=None,
                ccass_artifacts=None,
                previous_available=False,
                error_message=f"{exc.code}: {exc.message}",
            )
    else:
        bundle = PortalBundle(
            requested_code="",
            resolved_code="",
            input_type=input_type,
            source_mode=source_mode,
            timeout_seconds=timeout_seconds,
            announcement_period=announcement_period,
            data_date=data_date,
            history_range=history_range,
            top_n=top_n,
            percentage_basis=percentage_basis,
            big_change_threshold=big_change_threshold,
            use_local_history=use_local_history,
            live_product=None,
            prepared=None,
            live_markdown_en="",
            live_markdown_zh="",
            ccass_markdown_en="",
            ccass_markdown_zh="",
            live_artifacts=None,
            ccass_artifacts=None,
            previous_available=False,
        )
    html_page = _render_page(bundle)
    return HTMLResponse(html_page)


async def _stream_bytes(data: bytes, media_type: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([data]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/download/{section}/{kind}")
async def download(
    section: str,
    kind: str,
    locale: str = Query(default="en"),
    code: str = Query(default=DEFAULT_CODE),
    input_type: str = Query(default="Stock Code"),
    source_mode: str = Query(default="auto"),
    timeout_seconds: float = Query(default=12.0, ge=1.0),
    announcement_period: str = Query(default="All"),
    data_date: date = Query(default=date.today()),
    history_range: str = Query(default="Latest"),
    top_n: int = Query(default=20, ge=5, le=100),
    percentage_basis: str = Query(default="CCASS"),
    big_change_threshold: int = Query(default=1_000_000, ge=0),
    use_local_history: bool = Query(default=True),
) -> StreamingResponse:
    bundle = await _build_bundle(
        raw_code=code,
        input_type=input_type,
        source_mode=source_mode,
        timeout_seconds=timeout_seconds,
        announcement_period=announcement_period,
        data_date=data_date,
        history_range=history_range,
        top_n=top_n,
        percentage_basis=percentage_basis,
        big_change_threshold=big_change_threshold,
        use_local_history=use_local_history,
    )
    if section == "live":
        if bundle.live_artifacts is None:
            raise PlatformError("NOT_FOUND", "Live product artifacts are unavailable.", status_code=404)
        if kind == "csv":
            return await _stream_bytes(bundle.live_artifacts.combined_csv_bytes, "text/csv", bundle.live_artifacts.combined_csv_filename)
        if kind == "xlsx":
            return await _stream_bytes(
                bundle.live_artifacts.workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                bundle.live_artifacts.workbook_filename,
            )
        if kind == "json":
            return await _stream_bytes(bundle.live_artifacts.json_bytes, "application/json", bundle.live_artifacts.json_filename)
        if kind == "md":
            return await _stream_bytes(
                _bundle_markdown(bundle, "live", locale).encode("utf-8"),
                "text/markdown; charset=utf-8",
                f"{bundle.resolved_code}_live_markdown.md",
            )
    if section == "ccass":
        if bundle.ccass_artifacts is None or bundle.prepared is None:
            raise PlatformError("NOT_FOUND", "CCASS artifacts are unavailable.", status_code=404)
        if kind == "csv":
            return await _stream_bytes(bundle.ccass_artifacts.combined_csv_bytes, "text/csv", bundle.ccass_artifacts.combined_csv_filename)
        if kind == "xlsx":
            return await _stream_bytes(
                bundle.ccass_artifacts.workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                bundle.ccass_artifacts.workbook_filename,
            )
        if kind == "json":
            payload = bundle.prepared.response.model_dump_json(indent=2).encode("utf-8")
            return await _stream_bytes(
                payload,
                "application/json",
                f"{bundle.prepared.response.metadata.code}_ccass.json",
            )
        if kind == "sqlite":
            sqlite_path = get_settings().ccass_sqlite_path
            if not sqlite_path.is_file():
                raise PlatformError("NOT_FOUND", "SQLite backup is unavailable.", status_code=404)
            return await _stream_bytes(
                sqlite_path.read_bytes(),
                "application/x-sqlite3",
                sqlite_path.name,
            )
        if kind == "md":
            return await _stream_bytes(
                _bundle_markdown(bundle, "ccass", locale).encode("utf-8"),
                "text/markdown; charset=utf-8",
                bundle.prepared.filename,
            )
    if section == "raw_previews":
        if bundle.ccass_artifacts is None or bundle.prepared is None:
            raise PlatformError("NOT_FOUND", "Raw preview artifacts are unavailable.", status_code=404)
        if kind == "json":
            return await _stream_bytes(
                bundle.ccass_artifacts.raw_preview_json_bytes,
                "application/json",
                bundle.ccass_artifacts.raw_preview_json_filename,
            )
        if kind == "summary_csv":
            return await _stream_bytes(
                bundle.ccass_artifacts.raw_preview_summary_bytes,
                "text/csv",
                bundle.ccass_artifacts.raw_preview_summary_filename,
            )
        if kind == "holdings_csv":
            return await _stream_bytes(
                bundle.ccass_artifacts.raw_preview_holdings_bytes,
                "text/csv",
                bundle.ccass_artifacts.raw_preview_holdings_filename,
            )
    raise PlatformError("NOT_FOUND", f"Unsupported download kind: {section}/{kind}", status_code=404)

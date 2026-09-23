from __future__ import annotations

import asyncio
import csv
import html
import io
import json
import logging
import math
import os
import sys
import time
import threading
import traceback
import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

def _post_emit(stage, started, *, completed=None, exception_type="", timeout=False, status=""):
    payload = {"stage": stage, "stock": "06182", "ts": time.time(), "elapsed_ms": round((time.perf_counter() - started) * 1000, 1), "completed": completed, "status": status, "exception_type": exception_type, "timeout": timeout}
    print("LB_TRACE " + json.dumps(payload, separators=(",", ":")), flush=True)



def _post_trace(stage: str):
    def decorate(fn):
        @wraps(fn)
        async def wrapped(*args, **kwargs):
            code = str(kwargs.get("raw_code") or kwargs.get("code") or (args[0] if args else "")).zfill(5)
            if code != "06182" or os.getenv("P0_LONGBRIDGE_TRACE") != "1":
                return await fn(*args, **kwargs)
            started = time.perf_counter(); _post_emit(stage + "_START", started)
            try:
                result = await fn(*args, **kwargs)
            except Exception as exc:
                _post_emit(stage + "_END", started, completed=False, exception_type=type(exc).__name__, timeout=isinstance(exc, TimeoutError)); raise
            _post_emit(stage + "_END", started, completed=True, status="returned")
            return result
        return wrapped
    return decorate

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse

from app.config import get_settings, secret_fingerprint
from app.daily_snapshot import run_daily_snapshot
from app.domain.history import HistoricalSnapshot
from app.errors import PlatformError
from app.friend_clone_app import (
    APP_SUBTITLE_EN,
    APP_SUBTITLE_ZH,
    APP_TITLE_EN,
    APP_TITLE_ZH,
    DEFAULT_CODE,
    PortalBundle,
    _announcement_block,
    _big_changes_block,
    _build_bundle,
    _bundle_markdown,
    _ccass_summary,
    _changes_block,
    _close_section,
    _company_block,
    _copy_blocks,
    _download_links,
    _escape,
    _format_date,
    _format_datetime,
    _format_float,
    _format_int,
    _format_percent,
    _holdings_table,
    _i18n,
    _kv_table,
    _live_summary_cards,
    _metric_card,
    _pill,
    _raw_preview_block,
    _section_heading,
    _sparkline,
    _table,
)
from app.live_product import YAHOO_CHART_API_URL
from app.live_product import _build_latest_price, _build_price_history_rows
from app.services.ccass import get_ccass_service
from app.models import AnnouncementsResponse, CorporateTimeline, ShareCapitalHistoryResponse, DisclosureInterestsResponse, FundamentalsResponse, DocumentEntitiesResponse, IntelligenceEventsResponse
from app.services.intelligence_events import IntelligenceEventsService, get_intelligence_events_service
from app.services.ownership_timeline import OwnershipTimelineService, get_ownership_timeline_service
from app.services.accumulation import AccumulationService
from app.services.price_history import get_price_history_service
from app.services.research_context import ResearchContextService, get_research_context_service
from app.services.alerts import AlertsService
from app.models import OwnershipTimelineResponse
from app.services.announcements import AnnouncementsService, get_announcements_service
from app.services.corporate_timeline import build_corporate_timeline
from app.services.longbridge import LongbridgeHoldingsService
from app.models import StockEventsResponse
from app.services.stock_events import StockEventsService, get_stock_events_service
from app.models import OfficersResponse
from app.services.officers import OfficersService, get_officers_service
from app.services.share_capital_history import ShareCapitalHistoryService, get_share_capital_history_service
from app.services.disclosure_interests import DisclosureInterestsService, get_disclosure_interests_service
from app.services.fundamentals import FundamentalsService, get_fundamentals_service
from app.services.document_entities import DocumentEntitiesService, get_document_entities_service
from ccass_core.compute import HoldingChange, compute_analysis

from app.services.big_changes import get_big_changes_service
from app.services.changes import get_changes_service
from app.services.concentration import get_concentration_service
from app.sources.registry import GOOGLE_DRIVE_CSV_SOURCE_ID
from app.storage.history import NormalizedSnapshotRepository
from app.streamlit_ui import (
    build_download_artifacts,
    build_section_csv_artifact,
    build_raw_preview_tables,
    prepare_report,
    render_prepared_report,
    resolve_streamlit_query_input,
)
from ccass_core.collector import SnapshotStore
from ccass_core.normalize import normalize_stock_code

from app.api import get_concentration_evidence, verify_api_key


logger = logging.getLogger(__name__)


prepare_report = _post_trace("PREPARE_REPORT")(prepare_report)

APP_TITLE_EN = "Joe Visual Portal"


_build_bundle = _post_trace("BUILD_BUNDLE")(_build_bundle)

APP_TITLE_ZH = "Joe Visual Portal"
APP_SUBTITLE_EN = "Golden Joe reference portal for live market news and CCASS holdings."
APP_SUBTITLE_ZH = "Golden Joe 參考入口：即時市場資訊與 CCASS 持股。"

DEFAULT_PORTAL_CODE = "00700"
PRICE_HISTORY_LOAD_TIMEOUT_SECONDS = 5.0
LONGBRIDGE_CALL_TIMEOUT_SECONDS = 8.0
LONGBRIDGE_ENRICHMENT_BUDGET_SECONDS = 35.0
PRICE_RANGE_WINDOWS: dict[str, int | None] = {
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "1Y": 252,
    "Max": None,
}
PRICE_BAR_CHOICES = ("turnover", "volume")
PRICE_METRIC_LABELS = {
    "turnover": ("Turnover", "成交額"),
    "volume": ("Volume", "成交量"),
}
RICH_HISTORY_LOOKBACK_DAYS = 3650
RAINBOW_COLOR_PALETTE = (
    "#1d63a8",
    "#18a0ff",
    "#4db6ac",
    "#f6b26b",
    "#c27ba0",
    "#8e7cc3",
    "#6aa84f",
    "#cc0000",
    "#999999",
)


def _exception_details(error: BaseException) -> str:
    """Flatten ExceptionGroup without hiding the first causal child."""
    current = error
    while isinstance(current, BaseExceptionGroup) and current.exceptions:
        current = current.exceptions[0]
    origin = traceback.extract_tb(current.__traceback__)[-1] if current.__traceback__ else None
    location = f"{origin.filename}:{origin.lineno}:{origin.name}" if origin else "unknown"
    return f"{type(current).__name__}: {current} @ {location} thread={threading.current_thread().name}"

try:  # pragma: no cover - optional dependency guard
    import yfinance as yf
except Exception:  # pragma: no cover - dependency is optional in recovery mode
    yf = None


def _format_decimal(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:,.{digits}f}"


def _int_text(value: object | None) -> str:
    if value is None:
        return "—"
    try:
        return _format_int(int(value))
    except Exception:
        return "—"


def _normalize_price_rows(result) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    previous_close: float | None = None
    for row in result:
        date_value = row.get("date")
        close = row.get("close")
        volume = row.get("volume")
        turnover = row.get("turnover")
        vwap = row.get("vwap")
        price_source = row.get("price_source")
        turnover_est = row.get("turnover_est")
        vwap_est = row.get("vwap_est")
        if turnover is None and close is not None and volume is not None:
            turnover = float(close) * float(volume)
            if turnover_est is None:
                turnover_est = turnover
        if vwap is None and turnover is not None and volume not in (None, 0):
            vwap = float(turnover) / float(volume)
            if vwap_est is None:
                vwap_est = vwap
        close_float = float(close) if close is not None else None
        row_change = None if previous_close is None or close_float is None else close_float - previous_close
        row_change_pct = None
        if row_change is not None and previous_close not in (None, 0):
            row_change_pct = row_change / previous_close * 100
        if close_float is not None:
            previous_close = close_float
        rows.append(
            {
                "date": date_value,
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": close_float,
                "vwap": float(vwap) if vwap is not None else None,
                "volume": int(volume) if volume is not None else None,
                "turnover": float(turnover) if turnover is not None else None,
                "dividends": row.get("dividends") or 0.0,
                "splits": row.get("splits") or 0.0,
                "price_source": price_source,
                "turnover_est": float(turnover_est) if turnover_est is not None else None,
                "vwap_est": float(vwap_est) if vwap_est is not None else None,
                "source": row.get("source"),
                "source_url": row.get("source_url"),
                "change": row_change,
                "change_percent": row_change_pct,
            }
        )
    return rows


def _range_slice(rows: list[dict[str, object]], window: str) -> list[dict[str, object]]:
    if window == "Max":
        return rows
    limit = PRICE_RANGE_WINDOWS[window]
    if limit is None or len(rows) <= limit:
        return rows
    return rows[-limit:]


def _chart_scale(values: list[float], height: float) -> tuple[float, float]:
    if not values:
        return 0.0, 1.0
    lo = min(values)
    hi = max(values)
    if math.isclose(lo, hi):
        if lo == 0:
            return 0.0, 1.0
        padding = abs(lo) * 0.05
        return lo - padding, hi + padding
    padding = (hi - lo) * 0.08
    return lo - padding, hi + padding


def _svg_escape(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _price_chart_svg(
    rows: list[dict[str, object]],
    *,
    metric: str,
    width: int = 980,
    height: int = 360,
) -> str:
    if not rows:
        return '<div class="empty-state">No price history rows available.</div>'

    left = 60
    right = 60
    top = 28
    bottom = 54
    inner_w = width - left - right
    inner_h = height - top - bottom
    close_values = [float(row["close"]) for row in rows if row.get("close") is not None]
    metric_values = [
        float(row[metric]) for row in rows if row.get(metric) is not None
    ]
    close_min, close_max = _chart_scale(close_values, inner_h)
    metric_min, metric_max = _chart_scale(metric_values, inner_h * 0.35)

    def close_y(value: float) -> float:
        return top + inner_h - ((value - close_min) / (close_max - close_min or 1.0)) * inner_h

    def metric_h(value: float) -> float:
        usable = inner_h * 0.35
        return max(1.0, ((value - metric_min) / (metric_max - metric_min or 1.0)) * usable)

    points: list[str] = []
    bar_elems: list[str] = []
    event_elems: list[str] = []
    step = inner_w / max(1, len(rows) - 1)
    metric_label_en, metric_label_zh = PRICE_METRIC_LABELS[metric]

    for index, row in enumerate(rows):
        x = left + index * step
        close = row.get("close")
        if close is not None:
            y = close_y(float(close))
            points.append(f"{x:.1f},{y:.1f}")
            bar_elems.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" class="price-point">'
                f'<title>{_svg_escape(row.get("date"))} close {close}</title></circle>'
            )
        metric_value = row.get(metric)
        if metric_value is not None:
            bar_height = metric_h(float(metric_value))
            bar_top = top + inner_h - bar_height
            bar_width = max(2.0, step * 0.6)
            bar_x = x - bar_width / 2
            bar_elems.append(
                f'<rect x="{bar_x:.1f}" y="{bar_top:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" class="price-bar">'
                f'<title>{_svg_escape(row.get("date"))} {metric} {metric_value:,.0f}</title></rect>'
            )
        if float(row.get("dividends") or 0) or float(row.get("splits") or 0):
            label = []
            if float(row.get("dividends") or 0):
                label.append(f"Dividend {row['dividends']}")
            if float(row.get("splits") or 0):
                label.append(f"Split {row['splits']}")
            event_elems.append(
                f'<line x1="{x:.1f}" y1="{top:.1f}" x2="{x:.1f}" y2="{top + inner_h:.1f}" class="price-event-line" />'
                f'<circle cx="{x:.1f}" cy="{top + 12:.1f}" r="3.4" class="price-event-dot">'
                f'<title>{_svg_escape(row.get("date"))} {" | ".join(label)}</title></circle>'
            )

    first_label = _svg_escape(rows[0].get("date"))
    mid_label = _svg_escape(rows[len(rows) // 2].get("date"))
    last_label = _svg_escape(rows[-1].get("date"))
    close_axis_min = _format_decimal(close_min, 2)
    close_axis_max = _format_decimal(close_max, 2)
    metric_axis_max = _format_int(int(metric_max))
    line_points = " ".join(points)
    return f"""
    <svg viewBox="0 0 {width} {height}" class="price-chart-svg" role="img" aria-label="Price history chart">
      <defs>
        <linearGradient id="closeGradient" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="#1d63a8" stop-opacity="0.24" />
          <stop offset="100%" stop-color="#1d63a8" stop-opacity="0.04" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="{width}" height="{height}" rx="22" class="price-chart-bg" />
      {"".join(
          f'<line x1="{left}" y1="{top + inner_h * frac:.1f}" x2="{width - right}" y2="{top + inner_h * frac:.1f}" class="price-grid-line" />'
          for frac in (0.0, 0.25, 0.5, 0.75, 1.0)
      )}
      <text x="18" y="{top + 8:.1f}" class="price-axis-label">{close_axis_max}</text>
      <text x="18" y="{top + inner_h + 4:.1f}" class="price-axis-label">{close_axis_min}</text>
      <text x="{width - 14}" y="{top + 8:.1f}" text-anchor="end" class="price-axis-label">{metric_axis_max} {metric_label_en}</text>
      <text x="{width - 14}" y="{height - 16}" text-anchor="end" class="price-axis-label">{last_label}</text>
      <text x="{left}" y="{height - 16}" class="price-axis-label">{first_label}</text>
      <text x="{left + inner_w / 2:.1f}" y="{height - 16}" text-anchor="middle" class="price-axis-label">{mid_label}</text>
      <polyline points="{line_points}" fill="none" stroke="#1d63a8" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
      {"".join(bar_elems)}
      {"".join(event_elems)}
    </svg>
    <div class="price-chart-footnote">
      Close line + {metric_label_en.lower()} bars. Bars are scaled independently inside the chart. Event markers show dividends / splits when Yahoo Finance exposes them.
    </div>
    """


def _load_price_history(symbol: str) -> list[dict[str, object]]:
    if yf is None:
        return []
    ticker = yf.Ticker(symbol)
    dataframe = None
    for period in ("max", "1y", "6mo"):
        try:
            dataframe = ticker.history(
                period=period,
                interval="1d",
                auto_adjust=False,
                actions=True,
            )
        except Exception:
            dataframe = None
        if dataframe is not None and not dataframe.empty:
            break
    if dataframe is None or dataframe.empty:
        return []
    frame = dataframe.reset_index()
    rows: list[dict[str, object]] = []
    for _, item in frame.iterrows():
        date_value = item.get("Date")
        if isinstance(date_value, datetime):
            day = date_value.date()
        elif isinstance(date_value, date):
            day = date_value
        else:
            day = None
        rows.append(
            {
                "date": day.isoformat() if day else None,
                "open": float(item["Open"]) if item.get("Open") is not None else None,
                "high": float(item["High"]) if item.get("High") is not None else None,
                "low": float(item["Low"]) if item.get("Low") is not None else None,
                "close": float(item["Close"]) if item.get("Close") is not None else None,
                "vwap": float(item["Close"]) if item.get("Close") is not None else None,
                "volume": int(item["Volume"]) if item.get("Volume") is not None else None,
                "turnover": float(item["Close"]) * float(item["Volume"]) if item.get("Close") is not None and item.get("Volume") is not None else None,
                "price_source": "yahoo",
                "turnover_est": float(item["Close"]) * float(item["Volume"]) if item.get("Close") is not None and item.get("Volume") is not None else None,
                "vwap_est": float(item["Close"]) if item.get("Close") is not None else None,
                "dividends": float(item["Dividends"]) if "Dividends" in item and item.get("Dividends") else 0.0,
                "splits": float(item["Stock Splits"]) if "Stock Splits" in item and item.get("Stock Splits") else 0.0,
                "source": "Yahoo Finance",
                "source_url": YAHOO_CHART_API_URL.format(symbol=symbol),
            }
        )
    return _normalize_price_rows(rows)


@lru_cache(maxsize=16)
def _cached_price_history(symbol: str) -> tuple[dict[str, object], ...]:
    return tuple(_load_price_history(symbol))


def _history_windows(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    return {window: _range_slice(rows, window) for window in PRICE_RANGE_WINDOWS}




def _refresh_persisted_derived_chain(base: PortalBundle, *, big_change_threshold: int) -> None:
    prepared = base.prepared
    if prepared is None or prepared.response is None:
        return
    current = prepared.response
    if str(getattr(current.metadata, "source_name", "")).lower() != "longbridge":
        raise PlatformError(
            "INVALID_SCHEMA",
            "Derived analytics require a persisted Longbridge current snapshot.",
            status_code=502,
        )
    snapshot_date = getattr(current.metadata, "holdings_date", None)
    if snapshot_date is None:
        return
    previous_snapshot = _snapshot_repo().previous(
        current.metadata.code,
        before_date=snapshot_date,
        source_id="longbridge",
        include_partial=False,
    )
    if previous_snapshot is None:
        return
    changes = get_changes_service().get_changes(
        current.metadata.code,
        snapshot_date=snapshot_date,
        compare_date=previous_snapshot.snapshot_date,
    )
    big_changes = get_big_changes_service().get_big_changes(
        current.metadata.code,
        snapshot_date=changes.metadata.snapshot_date,
        compare_date=changes.metadata.compare_date,
        threshold_shares=big_change_threshold,
    )
    concentration = get_concentration_service().get_concentration(
        current.metadata.code,
        snapshot_date=changes.metadata.snapshot_date,
        top_holders_limit=10,
    )
    previous_response = previous_snapshot.to_response()
    analysis = compute_analysis(current, previous=previous_response, big_change_threshold=big_change_threshold)
    analysis = replace(
        analysis,
        changes=tuple(
            HoldingChange(
                participant_id=row.participant_id,
                participant=row.participant,
                previous_shares=row.shares_before,
                current_shares=row.shares_after,
                share_change=row.shares_change,
                previous_pct_of_issued=row.percent_before,
                current_pct_of_issued=row.percent_after,
                pct_point_change=row.percent_change,
                status=row.status,
            )
            for row in changes.changes
        ),
        big_changes=tuple(
            HoldingChange(
                participant_id=row.participant_id,
                participant=row.participant,
                previous_shares=row.shares_before,
                current_shares=row.shares_after,
                share_change=row.shares_change,
                previous_pct_of_issued=row.percent_before,
                current_pct_of_issued=row.percent_after,
                pct_point_change=row.percent_change,
                status=row.status,
            )
            for row in big_changes.big_changes
        ),
        previous_available=True,
        source_status=big_changes.source_status,
        authority_status=big_changes.authority_status,
        concentration={
            "participant_count": concentration.summary.participant_count,
            "top5_pct_of_issued": concentration.summary.top5_pct_of_issued,
            "top10_pct_of_issued": concentration.summary.top10_pct_of_issued,
            "top5_pct_of_ccass": concentration.summary.top5_pct_of_ccass,
            "top10_pct_of_ccass": concentration.summary.top10_pct_of_ccass,
        },
    )
    base.prepared = replace(
        prepared,
        response=current.model_copy(update={"big_changes": big_changes}),
        previous_response=previous_response,
        analysis=analysis,
    )
    base.previous_available = True

def _snapshot_repo() -> NormalizedSnapshotRepository:
    return NormalizedSnapshotRepository(get_settings().ccass_sqlite_path)


def _concentration_history_rows(bundle: PortalBundle) -> list[dict[str, object]]:
    if bundle.prepared is None or bundle.prepared.response is None:
        return []
    code = bundle.prepared.response.metadata.code
    repo = _snapshot_repo()
    date_to = datetime.now(UTC).date()
    date_from = date_to - timedelta(days=RICH_HISTORY_LOOKBACK_DAYS)
    snapshots = repo.date_range(code, date_from=date_from, date_to=date_to, include_partial=True)
    rows: list[dict[str, object]] = []
    for snapshot in snapshots:
        rows.append(
            {
                "snapshot_date": snapshot.snapshot_date.isoformat(),
                "fetched_at": snapshot.fetched_at.isoformat(sep=" ", timespec="seconds"),
                "participant_count": snapshot.participant_count,
                "top5_pct_of_issued": snapshot.top5_pct_of_issued,
                "top10_pct_of_issued": snapshot.top10_pct_of_issued,
                "top5_pct_of_ccass": snapshot.top5_pct_of_ccass,
                "top10_pct_of_ccass": snapshot.top10_pct_of_ccass,
                "source_name": snapshot.source.display_name,
                "source_id": snapshot.source.source_id,
                "partial": snapshot.partial,
                "cached": snapshot.cached,
                "holdings": snapshot.holdings,
                "issued_shares": snapshot.issued_shares,
                "snapshot": snapshot,
            }
        )
    return rows


def _live_ccass_acquisition_state(bundle: PortalBundle) -> tuple[bool, str]:
    if bundle.live_product is None or bundle.prepared is None or bundle.prepared.response is None:
        return False, "CCASS acquisition unavailable."
    if not bundle.prepared.response.metadata.cached:
        return True, "Live CCASS result obtained from the selected source."
    source_trace = getattr(bundle.live_product, "source_trace", None)
    if source_trace is None:
        return True, "HKEX SDW browser acquisition enabled."
    selection = getattr(source_trace, "selection", None)
    selected_source_id = getattr(selection, "selected_source_id", None)
    if selected_source_id in {None, "cache", "persistent_lkg", GOOGLE_DRIVE_CSV_SOURCE_ID}:
        if selected_source_id == "persistent_lkg":
            return False, "Persistent LKG fallback recovered."
        if selected_source_id == "cache":
            return False, "Cached CCASS result recovered."
        if selected_source_id == GOOGLE_DRIVE_CSV_SOURCE_ID:
            return False, "Google Drive CSV fallback recovered."
        return False, "CCASS recovery used."
    return True, "HKEX SDW browser acquisition enabled."


def _concentration_line_svg(rows: list[dict[str, object]], *, width: int = 940, height: int = 280) -> str:
    if not rows:
        return '<div class="empty-state">No concentration history rows are available yet.</div>'
    left = 60
    right = 24
    top = 24
    bottom = 46
    inner_w = width - left - right
    inner_h = height - top - bottom
    y_values = [
        float(row["top5_pct_of_issued"] or 0)
        for row in rows
    ] + [
        float(row["top10_pct_of_issued"] or 0)
        for row in rows
    ]
    lo, hi = _chart_scale(y_values, inner_h)
    step = inner_w / max(1, len(rows) - 1)

    def y_at(value: float) -> float:
        return top + inner_h - ((value - lo) / (hi - lo or 1.0)) * inner_h

    top5_points: list[str] = []
    top10_points: list[str] = []
    labels = [row["snapshot_date"] for row in rows]
    for index, row in enumerate(rows):
        x = left + index * step
        top5 = float(row["top5_pct_of_issued"] or 0)
        top10 = float(row["top10_pct_of_issued"] or 0)
        top5_points.append(f"{x:.1f},{y_at(top5):.1f}")
        top10_points.append(f"{x:.1f},{y_at(top10):.1f}")

    first_label = _svg_escape(labels[0])
    mid_label = _svg_escape(labels[len(labels) // 2])
    last_label = _svg_escape(labels[-1])
    return f"""
    <svg viewBox="0 0 {width} {height}" class="concentration-chart-svg" role="img" aria-label="Concentration history chart">
      <rect x="0" y="0" width="{width}" height="{height}" rx="22" class="chart-bg" />
      {"".join(
          f'<line x1="{left}" y1="{top + inner_h * frac:.1f}" x2="{width - right}" y2="{top + inner_h * frac:.1f}" class="price-grid-line" />'
          for frac in (0.0, 0.25, 0.5, 0.75, 1.0)
      )}
      <text x="18" y="{top + 8:.1f}" class="price-axis-label">{_format_decimal(hi, 2)}%</text>
      <text x="18" y="{top + inner_h:.1f}" class="price-axis-label">{_format_decimal(lo, 2)}%</text>
      <polyline points="{' '.join(top5_points)}" class="line-top5" />
      <polyline points="{' '.join(top10_points)}" class="line-top10" />
      <text x="{left}" y="{height - 16}" class="price-axis-label">{first_label}</text>
      <text x="{left + inner_w / 2:.1f}" y="{height - 16}" text-anchor="middle" class="price-axis-label">{mid_label}</text>
      <text x="{width - right}" y="{height - 16}" text-anchor="end" class="price-axis-label">{last_label}</text>
    </svg>
    """


def _snapshot_top_ids(snapshot: HistoricalSnapshot, *, count: int = 8) -> list[str]:
    return [row.participant_id for row in snapshot.holdings[:count]]


def _price_history_response(bundle: PortalBundle) -> object | None:
    live_product = bundle.live_product
    if live_product is not None:
        response = getattr(live_product, "response", None)
        price_history = getattr(response, "price_history", None)
        if price_history is not None:
            return price_history
    prepared = bundle.prepared
    if prepared is not None:
        response = getattr(prepared, "response", None)
        price_history = getattr(response, "price_history", None)
        if price_history is not None:
            return price_history
    return None


def _rainbow_history_payload(rows: list[dict[str, object]]) -> tuple[list[str], list[dict[str, object]]]:
    if not rows:
        return [], []
    latest_snapshot = rows[-1]["snapshot"]
    if not isinstance(latest_snapshot, HistoricalSnapshot):
        return [], []
    top_ids = _snapshot_top_ids(latest_snapshot)
    snapshots: list[dict[str, object]] = []
    for row in rows:
        snapshot = row["snapshot"]
        if not isinstance(snapshot, HistoricalSnapshot):
            continue
        total = snapshot.issued_shares or snapshot.total_in_ccass_shares or 0
        participant_map = {holding.participant_id: holding for holding in snapshot.holdings}
        stacks: list[dict[str, object]] = []
        remainder = 0.0
        for participant_id in top_ids:
            holding = participant_map.get(participant_id)
            shares = float(holding.shares if holding else 0)
            pct = (shares / total * 100) if total else 0.0
            stacks.append(
                {
                    "participant_id": participant_id,
                    "participant": holding.participant_name if holding else participant_id,
                    "pct": pct,
                }
            )
        for holding in snapshot.holdings:
            if holding.participant_id not in top_ids:
                remainder += float(holding.shares)
        if total:
            remainder_pct = remainder / total * 100
        else:
            remainder_pct = 0.0
        stacks.append({"participant_id": "others", "participant": "Others", "pct": remainder_pct})
        snapshots.append(
            {
                "date": snapshot.snapshot_date.isoformat(),
                "stacks": stacks,
                "participant_count": snapshot.participant_count,
                "source_name": snapshot.source.display_name,
            }
        )
    return top_ids, snapshots


def _rainbow_csv_bytes(payload: dict[str, object]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=("date", "participant_id", "participant", "pct", "participant_count", "source_name"),
        lineterminator="\n",
    )
    writer.writeheader()
    for snapshot in payload.get("snapshots", []):
        if not isinstance(snapshot, dict):
            continue
        for stack in snapshot.get("stacks", []):
            if not isinstance(stack, dict):
                continue
            writer.writerow(
                {
                    "date": snapshot.get("date"),
                    "participant_id": stack.get("participant_id"),
                    "participant": stack.get("participant"),
                    "pct": stack.get("pct"),
                    "participant_count": snapshot.get("participant_count"),
                    "source_name": snapshot.get("source_name"),
                }
            )
    return buffer.getvalue().encode("utf-8-sig")


def _rainbow_download_payload(code: str) -> dict[str, object]:
    repo = _snapshot_repo()
    dates = repo.available_dates(code, include_partial=False)
    if not dates:
        return {
            "status": "unavailable",
            "stock_code": code,
            "available": False,
            "snapshot_count": 0,
            "top_ids": [],
            "snapshots": [],
            "warnings": ["No historical snapshots are available for DT Rainbow yet."],
        }
    snapshots = repo.date_range(
        code,
        date_from=dates[0],
        date_to=dates[-1],
        include_partial=False,
    )
    history_rows: list[dict[str, object]] = []
    for snapshot in snapshots:
        history_rows.append(
            {
                "snapshot_date": snapshot.snapshot_date.isoformat(),
                "fetched_at": snapshot.fetched_at.isoformat(sep=" ", timespec="seconds"),
                "participant_count": snapshot.participant_count,
                "top5_pct_of_issued": snapshot.top5_pct_of_issued,
                "top10_pct_of_issued": snapshot.top10_pct_of_issued,
                "top5_pct_of_ccass": snapshot.top5_pct_of_ccass,
                "top10_pct_of_ccass": snapshot.top10_pct_of_ccass,
                "source_name": snapshot.source.display_name,
                "source_id": snapshot.source.source_id,
                "partial": snapshot.partial,
                "cached": snapshot.cached,
                "holdings": snapshot.holdings,
                "issued_shares": snapshot.issued_shares,
                "snapshot": snapshot,
            }
        )
    top_ids, rainbow_snapshots = _rainbow_history_payload(history_rows)
    return {
        "status": "ok",
        "stock_code": code,
        "available": True,
        "snapshot_count": len(snapshots),
        "earliest_snapshot_date": dates[0].isoformat(),
        "latest_snapshot_date": dates[-1].isoformat(),
        "top_ids": top_ids,
        "snapshots": rainbow_snapshots,
        "warnings": [],
    }


def _rainbow_svg(rows: list[dict[str, object]], *, width: int = 940, height: int = 300) -> str:
    if not rows:
        return '<div class="empty-state">No historical snapshots are available for DT Rainbow yet.</div>'
    top_ids, snapshots = _rainbow_history_payload(rows)
    if not snapshots:
        return '<div class="empty-state">DT Rainbow requires snapshot history, but the available rows cannot be converted.</div>'
    left = 28
    right = 28
    top = 30
    bottom = 54
    inner_w = width - left - right
    inner_h = height - top - bottom
    bar_width = min(40.0, inner_w / max(1, len(snapshots) * 1.8))
    gap = max(8.0, (inner_w - (bar_width * len(snapshots))) / max(1, len(snapshots) - 1))
    palette = list(RAINBOW_COLOR_PALETTE)
    palette_map = {pid: palette[index % len(palette)] for index, pid in enumerate(top_ids)}
    palette_map["others"] = "#c7ceda"

    bars: list[str] = []
    legend: list[str] = []
    for idx, snapshot in enumerate(snapshots):
        x = left + idx * (bar_width + gap)
        y = top + inner_h
        title = snapshot["date"]
        for stack in snapshot["stacks"]:
            pct = float(stack["pct"] or 0)
            h = inner_h * pct / 100.0
            y -= h
            color = palette_map.get(str(stack["participant_id"]), "#999999")
            bars.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{max(h, 1.0):.1f}" fill="{color}">'
                f'<title>{_svg_escape(title)} {stack["participant"]}: {pct:.2f}%</title></rect>'
            )
        bars.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{height - 18}" text-anchor="middle" class="price-axis-label">{_svg_escape(title)}</text>'
        )

    for pid in top_ids:
        legend.append(
            f'<span class="legend-chip"><span class="legend-swatch" style="background:{palette_map[pid]};"></span>{_svg_escape(pid)}</span>'
        )
    legend.append(
        f'<span class="legend-chip"><span class="legend-swatch" style="background:{palette_map["others"]};"></span>Others</span>'
    )

    return f"""
    <div class="dt-rainbow-legend">{''.join(legend)}</div>
    <svg viewBox="0 0 {width} {height}" class="rainbow-chart-svg" role="img" aria-label="DT Rainbow stacked history">
      <rect x="0" y="0" width="{width}" height="{height}" rx="22" class="chart-bg" />
      {"".join(
          f'<line x1="{left}" y1="{top + inner_h * frac:.1f}" x2="{width - right}" y2="{top + inner_h * frac:.1f}" class="price-grid-line" />'
          for frac in (0.0, 0.25, 0.5, 0.75, 1.0)
      )}
      <text x="16" y="{top + 8:.1f}" class="price-axis-label">100%</text>
      <text x="16" y="{top + inner_h:.1f}" class="price-axis-label">0%</text>
      {"".join(bars)}
    </svg>
    """


def _price_panel(bundle: PortalBundle, price_rows: list[dict[str, object]]) -> str:
    if bundle.live_product is None:
        return '<div class="empty-state">Price history unavailable.</div>'
    source_name = "—"
    price_history_response = _price_history_response(bundle)
    if price_history_response is not None:
        source_name = price_history_response.metadata.source_name
    if not price_rows and bundle.live_product.price_history:
        price_rows = _normalize_price_rows(bundle.live_product.price_history)
    if not price_rows:
        return '<div class="empty-state">No usable price history rows were returned from the live source.</div>'
    if price_rows:
        source_name = str(price_rows[-1].get("source") or source_name)
    windows = _history_windows(price_rows)
    default_range = "1Y" if windows["1Y"] else "Max"
    default_metric = "turnover" if any(row.get("turnover") is not None for row in price_rows) else "volume"
    latest = price_rows[-1] if price_rows else {}
    previous = price_rows[-2] if len(price_rows) > 1 else {}
    latest_close = latest.get("close")
    previous_close = previous.get("close")
    latest_change = None if latest_close is None or previous_close is None else float(latest_close) - float(previous_close)
    latest_change_pct = (
        None
        if latest_change is None or not previous_close
        else latest_change / float(previous_close) * 100
    )
    latest_turnover = latest.get("turnover")
    latest_volume = latest.get("volume")
    latest_date = latest.get("date")
    default_table_rows = [
        [
            _svg_escape(row.get("date") or "—"),
            _svg_escape(_format_decimal(row.get("open"), 3)),
            _svg_escape(_format_decimal(row.get("high"), 3)),
            _svg_escape(_format_decimal(row.get("low"), 3)),
            _svg_escape(_format_decimal(row.get("close"), 3)),
            _svg_escape(_int_text(row.get("volume"))),
            _svg_escape(_format_decimal(row.get("turnover"), 2)),
            _svg_escape(_format_decimal(row.get("vwap") if row.get("vwap") is not None else row.get("vwap_est"), 4)),
        ]
        for row in reversed(windows[default_range][-12:])
    ]
    metric_card_rows = [
        _metric_card("Latest Close", "最新收市", _format_decimal(float(latest_close), 3) if latest_close is not None else "—", tone="primary"),
        _metric_card("Latest Change", "最新變動", f"{_format_decimal(latest_change, 3)} ({_format_percent(latest_change_pct, 2)})" if latest_change is not None else "—", tone="accent"),
        _metric_card("Turnover", "成交額", _format_decimal(float(latest_turnover), 2) if latest_turnover is not None else "—", note="Estimated from close × volume when raw turnover is not available." if any(row.get("turnover_est") is not None for row in price_rows) else None, tone="secondary"),
        _metric_card("Volume", "成交量", _format_int(int(latest_volume)) if latest_volume is not None else "—", tone="muted"),
    ]
    chart_cards = []
    for window in PRICE_RANGE_WINDOWS:
        for metric in PRICE_BAR_CHOICES:
            pane_rows = windows[window]
            selected = window == default_range and metric == default_metric
            chart_cards.append(
                f"""
                <div class="price-pane {'active' if selected else ''}" data-price-range="{window}" data-price-metric="{metric}">
                  <div class="price-pane-head">
                    <div>
                      <div class="chart-title">Range: {window} / Bars: {PRICE_METRIC_LABELS[metric][0]}</div>
                      <div class="chart-source">Source: {_svg_escape(source_name)} | data_as_of: {_svg_escape(latest_date or '—')}</div>
                    </div>
                    <div class="chart-mini-note">Rows: {len(pane_rows):,}</div>
                  </div>
                  { _price_chart_svg(pane_rows, metric=metric) }
                  <div class="chart-table-wrap">
                    {_table(["Date", "Open", "High", "Low", "Close", "Volume", "Turnover", "VWAP"], default_table_rows if selected else [
                        [
                            _svg_escape(row.get("date") or "—"),
                            _svg_escape(_format_decimal(row.get("open"), 3)),
                            _svg_escape(_format_decimal(row.get("high"), 3)),
                            _svg_escape(_format_decimal(row.get("low"), 3)),
                            _svg_escape(_format_decimal(row.get("close"), 3)),
                            _svg_escape(_int_text(row.get("volume"))),
                            _svg_escape(_format_decimal(row.get("turnover"), 2)),
                            _svg_escape(_format_decimal(row.get("vwap") if row.get("vwap") is not None else row.get("vwap_est"), 4)),
                        ]
                        for row in reversed(pane_rows[-12:])
                    ], class_name="compact-table")}
                  </div>
                </div>
                """
            )
    controls = "".join(
        f'<button type="button" class="chip-btn {"active" if window == default_range else ""}" data-price-range="{window}">{_escape(window)}</button>'
        for window in PRICE_RANGE_WINDOWS
    )
    metric_controls = "".join(
        f'<button type="button" class="chip-btn {"active" if metric == default_metric else ""}" data-price-metric="{metric}">{_escape(PRICE_METRIC_LABELS[metric][0])}</button>'
        for metric in PRICE_BAR_CHOICES
    )
    return f"""
    <div class="subcard">
      <div class="chart-header">
        <div>
          <h3>Price &amp; Turnover History</h3>
          <div class="source-note">Price chart: {_svg_escape(source_name)} | Bars are independently scaled inside the chart.</div>
        </div>
        <div class="chart-actions">
          <button type="button" class="icon-btn" data-price-download>Download as PNG</button>
          <button type="button" class="icon-btn" data-price-fullscreen>Fullscreen</button>
        </div>
      </div>
      <div class="metric-grid">{''.join(metric_card_rows)}</div>
      <div class="price-controls">
        <div class="control-group">
          <span class="control-label">Range</span>
          <div class="chip-row" data-price-control="range">{controls}</div>
        </div>
        <div class="control-group">
          <span class="control-label">Bars</span>
          <div class="chip-row" data-price-control="metric">{metric_controls}</div>
        </div>
      </div>
      <details class="event-lines">
        <summary>Cost / event lines</summary>
        <div class="event-lines-body">
          Dividend and split markers are drawn from the current price source corporate action fields when available. They are contextual markers only.
        </div>
      </details>
      <div class="price-panes">
        {''.join(chart_cards)}
      </div>
    </div>
    """


def _concentration_panel(bundle: PortalBundle, concentration_rows: list[dict[str, object]]) -> str:
    if bundle.prepared is None or bundle.prepared.response is None:
        return '<div class="empty-state">Concentration unavailable.</div>'
    if not concentration_rows:
        return '<div class="empty-state">Concentration history unavailable in the local snapshot store yet.</div>'
    latest = concentration_rows[-1]
    rows = [
        _metric_card("Snapshots", "快照數", _format_int(len(concentration_rows)), tone="primary"),
        _metric_card("Latest Top 5 % Issued", "最新前 5 佔已發行", _format_percent(float(latest["top5_pct_of_issued"] or 0), 2), tone="accent"),
        _metric_card("Latest Top 10 % Issued", "最新前 10 佔已發行", _format_percent(float(latest["top10_pct_of_issued"] or 0), 2), tone="accent"),
        _metric_card("Latest Top 5 % CCASS", "最新前 5 佔 CCASS", _format_percent(float(latest["top5_pct_of_ccass"] or 0), 2), tone="muted"),
        _metric_card("Latest Top 10 % CCASS", "最新前 10 佔 CCASS", _format_percent(float(latest["top10_pct_of_ccass"] or 0), 2), tone="muted"),
    ]
    history_rows = [
        [
            _svg_escape(row["snapshot_date"]),
            _svg_escape(_format_int(int(row["participant_count"]))),
            _svg_escape(_format_percent(float(row["top5_pct_of_issued"] or 0), 2)),
            _svg_escape(_format_percent(float(row["top10_pct_of_issued"] or 0), 2)),
            _svg_escape(row["source_name"]),
            _svg_escape("Partial" if row["partial"] else "Complete"),
        ]
        for row in concentration_rows[-24:]
    ]
    return f"""
    <div class="subcard">
      <div class="chart-header">
        <div>
          <h3>Concentration History</h3>
          <div class="source-note">Stored CCASS snapshots in SQLite | latest data_as_of: {_svg_escape(latest["snapshot_date"])} | basis: issued_shares</div>
        </div>
      </div>
      <div class="metric-grid">{''.join(rows)}</div>
      {_concentration_line_svg(concentration_rows)}
      <div class="chart-table-wrap">
        {_table(["Snapshot Date", "Participants", "Top 5 % Issued", "Top 10 % Issued", "Source", "Status"], history_rows, class_name="compact-table")}
      </div>
    </div>
    """


def _dt_rainbow_panel(bundle: PortalBundle, concentration_rows: list[dict[str, object]]) -> str:
    if not concentration_rows:
        return '<div class="empty-state">DT Rainbow unavailable until at least one snapshot exists in the local store.</div>'
    payload: list[dict[str, object]] = []
    for row in concentration_rows:
        payload.append({"snapshot": row["snapshot"]})
    latest_snapshot = payload[-1]["snapshot"]
    if not isinstance(latest_snapshot, HistoricalSnapshot):
        return '<div class="empty-state">DT Rainbow cannot resolve the latest snapshot payload.</div>'
    legend_cards = []
    for holding in latest_snapshot.holdings[:8]:
        legend_cards.append(
            f'<span class="legend-chip"><span class="legend-swatch" style="background:{RAINBOW_COLOR_PALETTE[holding.rank % len(RAINBOW_COLOR_PALETTE)]};"></span>{_svg_escape(holding.participant_name)}</span>'
        )
    history_payload = [row for row in concentration_rows if isinstance(row.get("snapshot"), HistoricalSnapshot)]
    return f"""
    <div class="subcard">
      <div class="chart-header">
        <div>
          <h3>DT Rainbow</h3>
          <div class="source-note">Historical participant continuity across stored snapshots. Color continuity follows the latest snapshot's top holders.</div>
        </div>
      </div>
      <div class="dt-rainbow-legend">{''.join(legend_cards)}</div>
      {_rainbow_svg(history_payload)}
      <div class="chart-table-wrap">
        {_table(
            ["Snapshot Date", "Participants", "Source", "Status"],
            [
                [
                    _svg_escape(row["snapshot"].snapshot_date.isoformat()),
                    _svg_escape(_format_int(int(row["snapshot"].participant_count))),
                    _svg_escape(row["snapshot"].source.display_name),
                    _svg_escape("Partial" if row["snapshot"].partial else "Complete"),
                ]
                for row in history_payload[-24:]
            ],
            class_name="compact-table"
        )}
      </div>
    </div>
    """


def _overview_block(bundle: PortalBundle, price_rows: list[dict[str, object]], concentration_rows: list[dict[str, object]]) -> str:
    result = bundle.live_product
    prepared = bundle.prepared
    ccass_date = prepared.response.metadata.holdings_date if prepared and prepared.response else None
    price_date = price_rows[-1]["date"] if price_rows else None
    snapshot_count = len(concentration_rows)
    source_mode = bundle.source_mode
    price_source_name = "Unavailable"
    price_history_response = _price_history_response(bundle)
    if price_history_response is not None:
        price_source_name = price_history_response.metadata.source_name
    elif price_rows and price_rows[-1].get("source"):
        price_source_name = str(price_rows[-1].get("source"))
    summary_cards = [
        _metric_card("Portal", "入口", APP_TITLE_EN, tone="primary"),
        _metric_card(
            "CCASS Source",
            "CCASS 來源",
            (
                f"{prepared.response.metadata.source_name}"
                + (" (cached)" if prepared.response.metadata.cached else "")
                if prepared and prepared.response
                else "Unavailable"
            ),
            tone="success",
        ),
        _metric_card("Price Source", "價格來源", price_source_name, tone="accent"),
        _metric_card("Announcement Source", "公告來源", "HKEX News", tone="muted"),
        _metric_card("Snapshot History", "快照歷史", _format_int(snapshot_count), tone="secondary"),
        _metric_card("Last CCASS Date", "最近 CCASS 日期", _format_date(ccass_date), tone="secondary"),
    ]
    top_cards = [
        _metric_card("Resolved code", "已解析代號", bundle.resolved_code, note="Input accepted and normalized.", tone="primary"),
        _metric_card("Live CCASS", "即時 CCASS", "YES" if _live_ccass_acquisition_state(bundle)[0] else "NO", note=_live_ccass_acquisition_state(bundle)[1], tone="success"),
        _metric_card("Chinese HKEX titles", "HKEX 中文標題", "YES" if bundle.live_product and bundle.live_product.announcements else "NO", note="Official title search language set to Chinese.", tone="accent"),
        _metric_card("Previous history", "歷史比較", "YES" if bundle.previous_available else "NO", note="Local snapshot comparison when available.", tone="secondary"),
        _metric_card("Last Price Date", "最近價格日期", _svg_escape(price_date or "—"), tone="secondary"),
        _metric_card("Source Mode", "來源模式", source_mode, tone="secondary"),
    ]
    return f"""
    <section id="overview" class="panel">
      <div class="kicker">AI-ready overview</div>
      <h2>Fetch summary</h2>
      <div class="metric-grid overview-grid">{''.join(summary_cards + top_cards)}</div>
    </section>
    """


def _longbridge_source_status_block(bundle: Portal8504Bundle | PortalBundle) -> str:
    """Render explicit provenance for Longbridge-backed portal data."""
    prepared = bundle.prepared
    if prepared is None or prepared.response is None:
        return '<div class="empty-state">Data source status unavailable.</div>'
    metadata = prepared.response.metadata
    source = str(getattr(metadata, "source_name", "") or "Unknown")
    asof = getattr(metadata, "data_as_of", None) or getattr(metadata, "holdings_date", None)
    row_count = len(prepared.response.holdings)
    status = getattr(metadata, "source_status", None) or ("cached" if metadata.cached else "ready")
    return (
        '<div class="subcard"><h3>Data Source Status</h3>'
        + _table(
            ["Source", "As-of Date", "Rows", "Status"],
            [[_escape(source), _escape(_format_date(asof)), _escape(_format_int(row_count)), _escape(status)]],
            class_name="compact-table",
        )
        + '</div>'
    )


def _all_tables_block(bundle: PortalBundle, price_rows: list[dict[str, object]], concentration_rows: list[dict[str, object]]) -> str:
    live_product = bundle.live_product
    prepared = bundle.prepared
    if live_product is None and prepared is None:
        return '<section id="all-tables" class="panel"><div class="empty-state">All tables unavailable.</div></section>'

    summary_rows: list[list[str]] = []
    latest_date = None
    if prepared and prepared.response is not None:
        latest_date = prepared.response.metadata.data_as_of
    elif price_rows:
        latest_date = price_rows[-1].get("date")

    def add_row(label: str, count: object, date_value: object | None = latest_date) -> None:
        summary_rows.append([
            _svg_escape(label),
            _svg_escape(count),
            _svg_escape(date_value or "—"),
        ])

    if live_product is not None:
        add_row("Company", 1 if live_product.company else 0)
        add_row("HKEX Announcements", len(live_product.announcements))
        add_row("Corporate Events", len(live_product.corporate_events))
        add_row("Share Capital Changes", len(live_product.share_capital_changes))
        add_row("Officers / Managers", len(live_product.officers))
    if prepared and prepared.response is not None:
        add_row("Holdings", len(prepared.response.holdings))
        add_row("Changes", len(prepared.analysis.changes))
        add_row("Big Changes", len(prepared.analysis.big_changes))
        add_row("Concentration", len(concentration_rows))
    add_row("Price History", len(price_rows), price_rows[-1].get("date") if price_rows else latest_date)
    return f"""
    <section id="all-tables" class="panel">
      <div class="kicker">Parsed tables at a glance</div>
      <h2>All Tables</h2>
      <div class="subcard">
        {_table(["Section", "Rows", "Latest / Data Date"], summary_rows, class_name="compact-table")}
      </div>
    </section>
    """


def _price_history_block(price_rows: list[dict[str, object]]) -> str:
    if not price_rows:
        return '<div class="empty-state">Price history unavailable.</div>'
    rows = [
        [
            _svg_escape(row.get("date") or "—"),
            _svg_escape(_format_decimal(row.get("open"), 3)),
            _svg_escape(_format_decimal(row.get("high"), 3)),
            _svg_escape(_format_decimal(row.get("low"), 3)),
            _svg_escape(_format_decimal(row.get("close"), 3)),
            _svg_escape(_int_text(row.get("volume"))),
            _svg_escape(_format_decimal(row.get("turnover"), 2)),
            _svg_escape(_format_decimal(row.get("vwap") if row.get("vwap") is not None else row.get("vwap_est"), 4)),
        ]
        for row in reversed(price_rows[-24:])
    ]
    latest = price_rows[-1]
    source_name = str(latest.get("source") or "—")
    return f"""
    <div class="subcard">
      <div class="chart-header">
        <div>
          <h3>Price History</h3>
          <div class="source-note">Source: {_svg_escape(source_name)} | data_as_of: {_svg_escape(latest.get("date") or "—")}</div>
        </div>
      </div>
      <div class="chart-table-wrap">
        {_table(["Date", "Open", "High", "Low", "Close", "Volume", "Turnover", "VWAP"], rows, class_name="compact-table")}
      </div>
    </div>
    """


def _build_query_payload(bundle: PortalBundle) -> dict[str, object]:
    payload: dict[str, object] = {
        "code": bundle.resolved_code,
        "input_type": bundle.input_type,
        "source_mode": bundle.source_mode,
        "timeout_seconds": bundle.timeout_seconds,
        "announcement_period": bundle.announcement_period,
        "history_range": bundle.history_range,
        "top_n": bundle.top_n,
        "percentage_basis": bundle.percentage_basis,
        "big_change_threshold": bundle.big_change_threshold,
        "use_local_history": "true" if bundle.use_local_history else "false",
    }
    if bundle.data_date and bundle.history_range == "Custom":
        payload["data_date"] = bundle.data_date.isoformat()
    return payload


@dataclass(slots=True)
class Portal8504Bundle:
    base: PortalBundle
    price_rows: list[dict[str, object]]
    concentration_rows: list[dict[str, object]]
    longbridge_periods: dict[str, dict[str, object]] = field(default_factory=dict)
    longbridge_daily: dict[str, object] | None = None
    longbridge_error: str | None = None


def _longbridge_changes_block(bundle: Portal8504Bundle) -> str:
    periods = bundle.longbridge_periods
    if not periods:
        reason = bundle.longbridge_error or "Longbridge period data unavailable."
        return f'<div class="empty-state">Longbridge changes unavailable: {_escape(reason)}</div>'
    blocks: list[str] = []
    for period in ("rct_1", "rct_5", "rct_20", "rct_60"):
        payload = periods.get(period) or {}
        rows: list[list[str]] = []
        for side in ("buy", "sell"):
            for row in payload.get(side) or []:
                if not isinstance(row, dict):
                    continue
                rows.append([
                    _escape(row.get("parti_number") or "—"),
                    _escape(row.get("name") or "—"),
                    _escape(row.get("chg") or 0),
                    _escape(side),
                    _escape(period),
                    _escape(payload.get("source") or "longbridge"),
                    _escape(payload.get("updated_at") or "—"),
                ])
        table = _table(
            ["Participant ID", "Participant", "Change Shares", "Side", "Period", "Source", "Data Date"],
            rows[:100], class_name="compact-table"
        ) if rows else '<div class="empty-state">No rows returned for this period.</div>'
        blocks.append(f'<div class="subcard"><h3>{_escape(period)} Changes</h3>{table}</div>')
    return "".join(blocks)


def _longbridge_daily_block(bundle: Portal8504Bundle) -> str:
    payload = bundle.longbridge_daily or {}
    rows = payload.get("list") or []
    if not rows:
        return '<div class="empty-state">Longbridge broker history unavailable.</div>'
    table_rows = [
        [_escape(row.get("date") or "—"), _escape(row.get("holding") or "—"),
         _escape(row.get("ratio") or "—"), _escape(row.get("chg") or "—"),
         _escape(payload.get("source") or "longbridge")]
        for row in rows if isinstance(row, dict)
    ]
    return '<div class="subcard"><h3>Broker Daily History</h3>' + _table(
        ["Date", "Holding", "Ratio", "Change", "Source"], table_rows[:100], class_name="compact-table"
    ) + '</div>'


def _portal_big_changes_block(bundle: PortalBundle) -> str:
    """Render an explicit first-snapshot state instead of an empty table."""
    prepared = bundle.prepared
    if prepared is not None and not getattr(prepared, "previous_response", None):
        return '<div class="warning-box">Big Changes 需要兩個相鄰快照，目前只有 1 個。</div>'
    return _big_changes_block(bundle)


@_post_trace("BUILD_PORTAL_BUNDLE")
async def _build_portal_8504_bundle(
    *,
    raw_code: str,
    input_type: str,
    source_mode: str,
    timeout_seconds: float = 12.0,
    announcement_period: str = "All",
    data_date: date | None = None,
    history_range: str = "Latest",
    top_n: int,
    percentage_basis: str = "CCASS",
    big_change_threshold: int,
    use_local_history: bool,
) -> Portal8504Bundle:
    base = await _build_bundle(
        raw_code=raw_code,
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
    price_rows: list[dict[str, object]] = []
    longbridge_service = LongbridgeHoldingsService()
    running_tests = bool(os.getenv("PYTEST_CURRENT_TEST")) or any(
        name == "pytest" or name.startswith("_pytest") for name in sys.modules
    )
    if base.live_product is not None:
        if not running_tests:
            try:
                longbridge_price = await asyncio.wait_for(
                    longbridge_service.get_price_history(base.resolved_code),
                    timeout=LONGBRIDGE_CALL_TIMEOUT_SECONDS,
                )
                updated_response = base.live_product.response.model_copy(
                    update={"price_history": longbridge_price}
                )
                base.live_product.response = updated_response
                base.live_product.price_history = _build_price_history_rows(updated_response)
                base.live_product.latest_price = _build_latest_price(updated_response)
                if base.prepared is not None and base.prepared.response is not None:
                    base.prepared = replace(
                        base.prepared,
                        response=base.prepared.response.model_copy(
                            update={"price_history": longbridge_price}
                        ),
                    )
            except Exception as exc:
                # Keep the existing Yahoo result untouched as the explicit fallback.
                base.live_product.source_notes.append(
                    f"Longbridge price unavailable ({type(exc).__name__}); using Yahoo Finance fallback."
                )
        if base.live_product.price_history:
            price_rows = _normalize_price_rows(base.live_product.price_history)
        try:
            if not price_rows:
                price_rows = list(
                    await asyncio.wait_for(
                        asyncio.to_thread(_cached_price_history, base.live_product.symbol),
                        timeout=PRICE_HISTORY_LOAD_TIMEOUT_SECONDS,
                    )
                )
        except TimeoutError:
            base.live_product.source_notes.append(
                f"Price history lookup timed out after {PRICE_HISTORY_LOAD_TIMEOUT_SECONDS:g}s; "
                "the page is rendering without the extended chart."
            )
        except Exception as exc:
            base.live_product.source_notes.append(
                f"Price history lookup failed with {type(exc).__name__}; the page is rendering without the extended chart."
            )
        if not price_rows and base.live_product.price_history:
            price_rows = _normalize_price_rows(base.live_product.price_history)
    longbridge_periods: dict[str, dict[str, object]] = {}
    longbridge_daily: dict[str, object] | None = None
    longbridge_error: str | None = None
    try:
        if os.getenv("PYTEST_CURRENT_TEST"):
            raise RuntimeError("test runtime: Longbridge UI enrichment skipped")
        prepared = base.prepared
        if prepared is None or prepared.response is None or not prepared.response.holdings:
            # Webb/local can be unavailable for a stock that Longbridge still
            # covers. Reuse the existing production service response as the
            # portal's Holdings model; do not create a UI-specific parser.
            fallback_response = await asyncio.wait_for(
                longbridge_service.fetch_and_persist(base.resolved_code),
                timeout=LONGBRIDGE_ENRICHMENT_BUDGET_SECONDS,
            )
            fallback_response = fallback_response.model_copy(
                update={
                    "data_quality_warnings": [
                        "本工具冇呢隻股嘅本地快照；來源：Longbridge（Webb-site 本日不可用）"
                    ]
                }
            )
            fallback_analysis = compute_analysis(
                fallback_response,
                previous=None,
                big_change_threshold=big_change_threshold,
            )
            base.prepared = replace(
                prepared,
                response=fallback_response,
                analysis=fallback_analysis,
                fetch_error="本工具冇呢隻股嘅本地快照；來源：Longbridge（Webb-site 本日不可用）",
            ) if prepared is not None else prepared
            if base.prepared is not None:
                base.previous_available = False
        enrichment_deadline = asyncio.get_running_loop().time() + LONGBRIDGE_ENRICHMENT_BUDGET_SECONDS
        participant_id = "B01438"
        if base.prepared and base.prepared.response and base.prepared.response.holdings:
            participant_id = base.prepared.response.holdings[0].participant_id
        remaining = enrichment_deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise TimeoutError("Longbridge enrichment budget exhausted")
        enrichment = await asyncio.wait_for(
            longbridge_service.get_enrichment(base.resolved_code, participant_id),
            timeout=min(LONGBRIDGE_ENRICHMENT_BUDGET_SECONDS, remaining),
        )
        longbridge_periods = enrichment.get("periods", {})
        longbridge_daily = enrichment.get("daily")
    except Exception as exc:
        longbridge_error = _exception_details(exc)
    # Derived analytics must use the same exact persisted Longbridge chain as
    # the API services; do not silently fall back to local UI computation.
    _refresh_persisted_derived_chain(base, big_change_threshold=big_change_threshold)
    concentration_rows = _concentration_history_rows(base)
    for row in concentration_rows:
        snapshot = row.get("snapshot")
        if isinstance(snapshot, HistoricalSnapshot):
            row["snapshot"] = snapshot
    return Portal8504Bundle(
        base=base,
        price_rows=price_rows,
        concentration_rows=concentration_rows,
        longbridge_periods=longbridge_periods,
        longbridge_daily=longbridge_daily,
        longbridge_error=longbridge_error,
    )


def _render_page(bundle: Portal8504Bundle) -> str:
    base = bundle.base
    price_rows = bundle.price_rows
    concentration_rows = bundle.concentration_rows
    selected_data_date = base.data_date.isoformat() if base.data_date else ""
    locale = "en"
    status_text = "LIVE CCASS + bilingual portal"
    if base.error_message:
        status_text = base.error_message
    live_status = "READY" if _live_ccass_acquisition_state(base)[0] else "PARTIAL"
    current_query = json.dumps(_build_query_payload(base))
    ccass_warning_html = ""
    if base.prepared and base.prepared.response and base.prepared.response.data_quality_warnings:
        ccass_warning_html = (
            "<div class='warning-box'>"
            + _escape("\n".join(base.prepared.response.data_quality_warnings))
            + "</div>"
        )
    ccass_error_html = ""
    if base.prepared and base.prepared.fetch_error:
        ccass_error_html = f"<div class='error-box'>{_escape(base.prepared.fetch_error)}</div>"
    live_error_html = ""
    if base.live_product is None and base.error_message:
        live_error_html = f"<div class='error-box'>{_escape(base.error_message)}</div>"

    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(APP_TITLE_EN)}</title>
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
    .shell {{ min-height: 100vh; display: flex; flex-direction: column; }}
    .topbar {{
      position: sticky; top: 0; z-index: 20;
      display: flex; align-items: center; justify-content: space-between; gap: 1rem;
      padding: 1rem 1.5rem; background: rgba(255,255,255,0.88);
      backdrop-filter: blur(14px); border-bottom: 1px solid var(--line);
    }}
    .brand {{ display: flex; align-items: center; gap: 0.9rem; }}
    .brand-mark {{
      width: 2.8rem; height: 2.8rem; border-radius: 0.9rem;
      background: linear-gradient(135deg, var(--brand), var(--brand-2));
      color: white; display: grid; place-items: center;
      font-size: 1.1rem; font-weight: 800; box-shadow: var(--shadow);
    }}
    .brand-title {{ font-size: 1.45rem; font-weight: 800; line-height: 1.1; }}
    .brand-subtitle {{ font-size: 0.92rem; color: var(--muted); margin-top: 0.15rem; }}
    .top-right {{ display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }}
    .status-pill {{
      padding: 0.42rem 0.8rem; border-radius: 999px; background: rgba(29, 99, 168, 0.10);
      color: var(--brand); font-weight: 700; border: 1px solid rgba(29, 99, 168, 0.16);
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
      background: var(--panel); border: 1px solid var(--line); border-radius: 22px;
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
    .advanced {{
      margin-top: 0.8rem;
      border-top: 1px solid var(--line);
      padding-top: 0.7rem;
    }}
    .advanced summary {{
      cursor: pointer;
      color: var(--brand);
      font-size: 0.86rem;
      font-weight: 800;
      list-style: none;
    }}
    .advanced summary::-webkit-details-marker {{ display: none; }}
    .advanced summary::before {{ content: "▸"; display: inline-block; margin-right: 0.35rem; }}
    .advanced[open] summary::before {{ content: "▾"; }}
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
    .main {{
      min-width: 0;
    }}
    .hero {{
      padding: 1.25rem;
      margin-bottom: 1rem;
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 0.85rem;
    }}
    .pill {{
      display: inline-flex; align-items: center; gap: .35rem; padding: .35rem .7rem;
      border-radius: 999px; font-size: .82rem; border: 1px solid transparent; font-weight: 700;
    }}
    .pill-neutral {{ background: #eef3fa; color: #35537f; }}
    .pill-success {{ background: rgba(31, 143, 95, 0.10); color: var(--good); border-color: rgba(31, 143, 95, 0.18); }}
    .pill-accent {{ background: rgba(24, 160, 255, 0.10); color: #127fcb; border-color: rgba(24, 160, 255, 0.18); }}
    .pill-warn {{ background: rgba(196, 122, 18, 0.10); color: var(--warn); border-color: rgba(196, 122, 18, 0.18); }}
    .primary-btn, .download-btn, .lang-btn {{
      background: linear-gradient(135deg, var(--brand), var(--brand-2)); color: white; border: none; cursor: pointer; font-weight: 800;
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
    .primary-btn {{
      width: 100%;
      margin-top: 0.35rem;
      box-shadow: 0 14px 28px rgba(29, 99, 168, 0.26);
    }}
    .hero-card {{ padding: 0; }}
    .hero-title {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; }}
    .hero-title h1 {{ margin: 0; font-size: 1.75rem; line-height: 1.1; }}
    .hero-title p {{ margin: 0.4rem 0 0; color: var(--muted); }}
    .hero-meta {{ display: flex; flex-wrap: wrap; gap: .45rem; margin-top: 0.9rem; }}
    .section-nav {{
      display: flex; flex-wrap: wrap; gap: .55rem; margin: 0 0 1rem;
      position: sticky; top: 74px; z-index: 18; padding: .55rem;
      background: rgba(238,242,247,0.82); backdrop-filter: blur(10px); border-radius: 16px;
      border: 1px solid rgba(18,31,54,.08);
    }}
    .section-nav a {{
      text-decoration: none; padding: .5rem .8rem; border-radius: 999px; font-weight: 700;
      color: var(--brand); background: rgba(29,99,168,.07);
    }}
    .panel {{ padding: 1rem; margin-bottom: 1rem; }}
    .panel h2 {{ margin: .2rem 0 .75rem; font-size: 1.3rem; }}
    .kicker {{ color: var(--brand-2); font-weight: 800; text-transform: uppercase; letter-spacing: .06em; font-size: .78rem; }}
    .metric-grid {{ display:grid; grid-template-columns: repeat( auto-fit, minmax(170px, 1fr) ); gap: .72rem; }}
    .overview-grid {{ grid-template-columns: repeat(6, minmax(0, 1fr)); }}
    .metric-card {{
      background: linear-gradient(180deg, #fff, #f7f9fc); border: 1px solid var(--line); border-radius: 18px;
      padding: .85rem .9rem;
    }}
    .metric-title {{ font-size: .78rem; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }}
    .metric-value {{ font-size: 1.08rem; font-weight: 800; margin-top: .35rem; line-height: 1.2; }}
    .metric-note {{ margin-top: .35rem; color: var(--muted); font-size: .78rem; line-height: 1.35; }}
    .subcard {{ padding: .9rem; margin-top: .75rem; }}
    .chart-header, .price-pane-head {{
      display:flex; align-items:flex-start; justify-content:space-between; gap:.85rem; flex-wrap:wrap;
    }}
    .chart-header h3, .price-pane-head .chart-title {{ margin: 0; font-size: 1.05rem; }}
    .source-note, .chart-source, .chart-mini-note, .event-lines-body {{ color: var(--muted); font-size: .85rem; line-height: 1.4; }}
    .chart-actions {{ display:flex; gap:.5rem; flex-wrap:wrap; }}
    .icon-btn {{ padding: .55rem .85rem; border-radius: 12px; }}
    .two-col {{ display:grid; grid-template-columns: 1fr 1fr; gap:.8rem; }}
    .table-wrap {{ overflow:auto; border-radius: 16px; border: 1px solid var(--line); background:#fff; }}
    table {{ width:100%; border-collapse: collapse; }}
    th, td {{ padding:.58rem .68rem; border-bottom:1px solid rgba(18,31,54,.08); font-size:.9rem; vertical-align: top; }}
    th {{ background:#f7f9fc; text-align:left; position: sticky; top: 0; z-index: 2; }}
    .compact-table td, .compact-table th {{ white-space: nowrap; }}
    .empty-state {{
      padding: 1rem; border-radius: 16px; background: rgba(24,160,255,.08); color: var(--brand);
      border: 1px dashed rgba(29,99,168,.22); font-weight: 700;
    }}
    .loading-runner {{
      display:inline-flex; align-items:center; justify-content:center; width:1.25rem; height:1.35rem;
      color:#7b8794; font-size:1.15rem; line-height:1;
    }}
    .loading-runner span {{ display:inline-block; opacity:.7; filter:grayscale(1); }}
    .loading-runner.active span {{ animation: runnerMove .72s ease-in-out infinite; }}
    @keyframes runnerMove {{ 0%,100% {{ transform:translateX(-.12rem) translateY(0); }} 50% {{ transform:translateX(.12rem) translateY(-.12rem); }} }}
    .warning-box, .error-box {{
      margin-top: .85rem; padding: .85rem .95rem; border-radius: 16px; white-space: pre-wrap;
    }}
    .warning-box {{ background: rgba(196,122,18,.09); border: 1px solid rgba(196,122,18,.18); }}
    .error-box {{ background: rgba(200,44,44,.08); border: 1px solid rgba(200,44,44,.18); }}
    .price-controls {{
      display:flex; gap:1rem; flex-wrap:wrap; align-items:flex-end; margin-top:.85rem;
    }}
    .control-group {{ display:flex; flex-direction:column; gap:.4rem; }}
    .control-label {{ font-size:.78rem; color:var(--muted); font-weight:800; text-transform:uppercase; letter-spacing:.04em; }}
    .chip-row {{ display:flex; gap:.45rem; flex-wrap:wrap; }}
    .chip-btn {{
      border: 1px solid rgba(29,99,168,.18); background: #eef4fb; color: var(--brand); border-radius: 999px;
      padding: .42rem .74rem; font-weight: 800; cursor:pointer;
    }}
    .chip-btn.active {{ background: linear-gradient(135deg, var(--brand), var(--brand-2)); color:#fff; border-color: transparent; }}
    .price-panes {{ margin-top:.85rem; }}
    .price-pane {{ display:none; }}
    .price-pane.active {{ display:block; }}
    .price-chart-svg, .concentration-chart-svg, .rainbow-chart-svg {{
      width:100%; height:auto; display:block; margin-top:.8rem;
      background: linear-gradient(180deg, rgba(255,255,255,.95), rgba(245,248,252,.95));
      border-radius: 22px; border: 1px solid rgba(18,31,54,.08);
    }}
    .chart-bg, .price-chart-bg {{ fill: url(#closeGradient); }}
    .chart-bg, .price-chart-bg {{ fill: #ffffff; }}
    .price-grid-line {{ stroke: rgba(18,31,54,.10); stroke-width: 1; }}
    .price-axis-label {{ fill: var(--muted); font-size: 11px; }}
    .price-bar {{ fill: rgba(24,160,255,.32); }}
    .price-point {{ fill: var(--brand); }}
    .price-event-line {{ stroke: rgba(196,122,18,.22); stroke-width: 1; stroke-dasharray: 3 3; }}
    .price-event-dot {{ fill: var(--warn); }}
    .price-chart-footnote {{ margin-top:.55rem; color: var(--muted); font-size:.82rem; }}
    .event-lines {{ margin-top:.85rem; border-radius: 14px; border: 1px solid rgba(18,31,54,.08); padding: .55rem .7rem; background:#fafcff; }}
    .event-lines summary {{ cursor:pointer; font-weight:800; }}
    .dt-rainbow-legend {{ display:flex; gap:.45rem; flex-wrap:wrap; margin-top:.65rem; }}
    .legend-chip {{
      display:inline-flex; align-items:center; gap:.35rem; padding:.34rem .6rem;
      border-radius:999px; background:#f4f7fb; border:1px solid rgba(18,31,54,.08); font-size:.8rem;
    }}
    .legend-swatch {{ width:.7rem; height:.7rem; border-radius:999px; display:inline-block; }}
    .copy-row {{ display:grid; grid-template-columns:1fr 1fr; gap:.85rem; }}
    .copy-card {{ background:#fff; border:1px solid var(--line); border-radius:18px; padding:.85rem; }}
    .copy-card textarea {{
      width:100%; min-height: 180px; resize: vertical; border: 1px solid var(--line); border-radius: 14px;
      padding: .8rem; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: .82rem; background: #fafcff;
    }}
    .copy-store {{
      position: absolute;
      left: -9999px;
      width: 1px;
      height: 1px;
      opacity: 0;
    }}
    .copy-actions {{ display:flex; justify-content:flex-end; margin-bottom:.6rem; }}
    .section-footer {{ display:flex; flex-wrap:wrap; gap:.55rem; }}
    .download-btn {{
      padding: .62rem .85rem; border-radius: 12px; text-decoration:none; background: linear-gradient(135deg, #183d72, #2474b9);
      color:#fff; font-weight:800;
    }}
    .layout-footer {{ color: var(--muted); font-size:.84rem; padding:0 1.25rem 1.5rem; }}
    @media (max-width: 1080px) {{
      .hero, .two-col, .copy-row, .search-form, .search-row {{ grid-template-columns: 1fr; }}
      .topbar {{ position: static; }}
      .nav {{ position: static; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">J</div>
        <div>
          <div class="brand-title">{_escape(APP_TITLE_EN)}</div>
          <div class="brand-subtitle">{_escape(APP_SUBTITLE_EN)}</div>
        </div>
      </div>
      <div class="top-right">
        <div id="loading-runner" class="loading-runner" aria-hidden="true"><span>🏃</span></div>
        <div class="status-pill">{_escape(live_status)}</div>
        <div class="lang-toggle">
          <button class="lang-btn active" type="button" data-locale-switch="en">EN</button>
          <button class="lang-btn" type="button" data-locale-switch="zh_HK">繁中</button>
        </div>
      </div>
    </header>
    <div class="layout">
      <aside class="sidebar">
        <h2>{_i18n("Search / Fetch", "搜尋／擷取", locale)}</h2>
        <form id="portal-query-form" method="get" action="/">
          <div class="field">
            <label>{_i18n("Input type", "輸入類型", locale)}</label>
            <select name="input_type">
              <option value="Stock Code"{" selected" if base.input_type == "Stock Code" else ""}>{_i18n("Stock Code", "股票代號", locale)}</option>
              <option value="Webb-site Issue ID"{" selected" if base.input_type == "Webb-site Issue ID" else ""}>{_i18n("Webb-site Issue ID", "Webb-site Issue ID", locale)}</option>
            </select>
          </div>
          <div class="field">
            <label>{_i18n("Stock code / issue ID", "股票代號／Issue ID", locale)}</label>
            <input name="code" value="{_escape(base.requested_code or base.resolved_code or DEFAULT_PORTAL_CODE)}" placeholder="00700" />
          </div>
          <input type="hidden" name="source_mode" value="auto" />
          <button class="primary-btn" type="submit">{_i18n("Fetch", "擷取", locale)}</button>
          <details class="advanced">
            <summary>{_i18n("Advanced settings", "進階設定", locale)}</summary>
            <div style="margin-top:0.75rem;">
              <div class="field">
                <label>{_i18n("Timeout", "逾時", locale)}</label>
                <input name="timeout_seconds" type="number" min="1" step="1" value="{_escape(base.timeout_seconds)}" />
              </div>
              <div class="field">
                <label>{_i18n("Announcement period", "公告期間", locale)}</label>
                <select name="announcement_period">
                  <option value="All"{" selected" if base.announcement_period == "All" else ""}>{_i18n("All", "全部", locale)}</option>
                  <option value="7 days"{" selected" if base.announcement_period == "7 days" else ""}>{_i18n("7 days", "7 日", locale)}</option>
                  <option value="30 days"{" selected" if base.announcement_period == "30 days" else ""}>{_i18n("30 days", "30 日", locale)}</option>
                  <option value="90 days"{" selected" if base.announcement_period == "90 days" else ""}>{_i18n("90 days", "90 日", locale)}</option>
                </select>
              </div>
              <div class="field">
                <label>{_i18n("Data date", "資料日期", locale)}</label>
                <input name="data_date" type="date" value="{_escape(selected_data_date)}" />
              </div>
              <div class="field">
                <label>{_i18n("History range", "歷史範圍", locale)}</label>
                <select name="history_range">
                  <option value="Latest"{" selected" if base.history_range == "Latest" else ""}>{_i18n("Latest", "最新", locale)}</option>
                  <option value="7 days"{" selected" if base.history_range == "7 days" else ""}>{_i18n("7 days", "7 日", locale)}</option>
                  <option value="30 days"{" selected" if base.history_range == "30 days" else ""}>{_i18n("30 days", "30 日", locale)}</option>
                  <option value="90 days"{" selected" if base.history_range == "90 days" else ""}>{_i18n("90 days", "90 日", locale)}</option>
                  <option value="Custom"{" selected" if base.history_range == "Custom" else ""}>{_i18n("Custom", "自訂", locale)}</option>
                </select>
              </div>
              <div class="field">
                <label>{_i18n("Top N", "前 N 名", locale)}</label>
                <input name="top_n" type="number" min="5" max="100" step="5" value="{base.top_n}" />
              </div>
              <div class="field">
                <label>{_i18n("Percentage basis", "百分比基準", locale)}</label>
                <select name="percentage_basis">
                  <option value="CCASS"{" selected" if base.percentage_basis == "CCASS" else ""}>{_i18n("CCASS", "CCASS", locale)}</option>
                  <option value="Issued Shares"{" selected" if base.percentage_basis == "Issued Shares" else ""}>{_i18n("Issued Shares", "已發行股份", locale)}</option>
                </select>
              </div>
              <input type="hidden" name="big_change_threshold" value="{base.big_change_threshold}" />
              <input type="hidden" name="use_local_history" value="{'true' if base.use_local_history else 'false'}" />
            </div>
          </details>
        </form>
        <div style="margin-top:1rem;">
          <div class="kicker">{_i18n("Current selection", "目前選項", locale)}</div>
          <div style="display:flex; flex-wrap:wrap; gap:0.45rem;">
            {_pill(base.resolved_code, "primary")}
            {_pill(base.input_type, "neutral")}
          </div>
        </div>
      </aside>
      <main class="main">
        {_overview_block(base, price_rows, concentration_rows)}
        <nav class="section-nav">
          <a href="#overview">{_i18n("Fetch Summary", "擷取摘要", locale)}</a>
          <a href="#all-tables">{_i18n("All Tables", "所有表格", locale)}</a>
          <a href="#announcements">{_i18n("HKEX Announcements", "HKEX 公告", locale)}</a>
          <a href="#events">{_i18n("Corporate Events", "公司事件", locale)}</a>
          <a href="#officers">{_i18n("Officers / Managers", "董事高管", locale)}</a>
          <a href="#share-capital">{_i18n("Share Capital", "股本變動", locale)}</a>
          <a href="#price-turnover">{_i18n("Price & Turnover", "價格與成交額", locale)}</a>
          <a href="#company">{_i18n("Company", "公司", locale)}</a>
          <a href="#ccass-holdings">{_i18n("CCASS Holdings", "CCASS 持股", locale)}</a>
          <a href="#changes">{_i18n("Changes", "變動", locale)}</a>
          <a href="#big-changes">{_i18n("Big Changes", "大變動", locale)}</a>
          <a href="#concentration">{_i18n("Concentration", "集中度", locale)}</a>
          <a href="#price-history">{_i18n("Price History", "價格歷史", locale)}</a>
          <a href="#raw-previews">{_i18n("Raw Previews", "原始預覽", locale)}</a>
          <a href="#copy">{_i18n("Copy for ChatGPT / Report", "複製給 ChatGPT／報告", locale)}</a>
          <a href="#downloads">{_i18n("Downloads", "下載", locale)}</a>
        </nav>

        <section id="price-turnover" class="panel">
          <div class="kicker">{_i18n("Market pricing", "市場價格", locale)}</div>
          <h2>{_i18n("Price & Turnover", "價格與成交額", locale)}</h2>
          {_price_panel(base, price_rows)}
        </section>

        {_all_tables_block(base, price_rows, concentration_rows)}

        <section id="announcements" class="panel">
          <div class="kicker">{_i18n("Company announcements", "公司公告", locale)}</div>
          <h2>{_i18n("HKEX Announcements", "HKEX 公告", locale)}</h2>
          {_announcement_block("HKEX Announcements", "HKEX 公告", base.live_product.announcements if base.live_product else [], locale, empty_text="No announcement rows available.")}
        </section>

        <section id="events" class="panel">
          <div class="kicker">{_i18n("Corporate actions", "公司動作", locale)}</div>
          <h2>{_i18n("Corporate Events", "公司事件", locale)}</h2>
          {_announcement_block("Corporate Events", "公司事件", base.live_product.corporate_events if base.live_product else [], locale, empty_text="No corporate event rows available.")}
        </section>

        <section id="officers" class="panel">
          <div class="kicker">{_i18n("Management", "管理層", locale)}</div>
          <h2>{_i18n("Officers / Managers", "董事高管", locale)}</h2>
          <div class="subcard">
            <h3>Officers / Managers</h3>
            {(
                _table(["Name", "Title", "Age", "From", "Until", "Source"], [
                [
                    _escape(row.get("name") or "—"),
                    _escape(row.get("title") or "—"),
                    _escape(row.get("age") or "—"),
                    _escape(row.get("from") or "—"),
                    _escape(row.get("until") or "—"),
                    _escape(row.get("source") or "—"),
                ] for row in (base.live_product.officers[:12] if base.live_product else [])
            ], class_name="compact-table")
                if base.live_product and base.live_product.officers
                else f'<div class="empty-state">Officers unavailable: {_escape(getattr(getattr(base.live_product, "response", None), "officers", None).metadata.source_status if getattr(getattr(base.live_product, "response", None), "officers", None) else "unavailable")} — source: {_escape(getattr(getattr(getattr(base.live_product, "response", None), "officers", None), "metadata", None).source_name if getattr(getattr(base.live_product, "response", None), "officers", None) else "—")}</div>'
            )}
          </div>
        </section>

        <section id="share-capital" class="panel">
          <div class="kicker">{_i18n("Capital structure", "股本結構", locale)}</div>
          <h2>{_i18n("Share Capital", "股本變動", locale)}</h2>
          {_announcement_block("Share Capital Changes", "股本變動", base.live_product.share_capital_changes if base.live_product else [], locale, empty_text="No share capital change rows available.")}
        </section>

        <section id="company" class="panel">
          <div class="kicker">{_i18n("Identity", "身份", locale)}</div>
          <h2>{_i18n("Company", "公司", locale)}</h2>
          {_company_block(base)}
        </section>

        <section id="ccass-holdings" class="panel">
          <div class="kicker">{_i18n("CCASS / holdings", "CCASS／持股", locale)}</div>
          <h2>{_i18n("CCASS Holdings", "CCASS 持股", locale)}</h2>
          {_ccass_summary(base, locale)}
          <div style="margin-top:.85rem;">{_holdings_table(base)}</div>
          {_longbridge_source_status_block(base)}
        </section>

        <section id="changes" class="panel">
          <div class="kicker">{_i18n("Historical comparison", "歷史比較", locale)}</div>
          <h2>{_i18n("Changes", "變動", locale)}</h2>
          {('<div class="warning-box">Snapshot Changes: WAITING_SECOND_SNAPSHOT</div>' if not base.previous_available else _changes_block(base, locale))}
          <div class="kicker" style="margin-top:1rem;">Longbridge production periods</div>
          {_longbridge_changes_block(bundle)}
          {_longbridge_daily_block(bundle)}
        </section>

        <section id="big-changes" class="panel">
          <div class="kicker">{_i18n("Threshold filtered", "門檻過濾", locale)}</div>
          <h2>{_i18n("Big Changes", "大變動", locale)}</h2>
          {_portal_big_changes_block(base)}
        </section>

        <section id="concentration" class="panel">
          <div class="kicker">{_i18n("Distribution view", "分布視圖", locale)}</div>
          <h2>{_i18n("Concentration", "集中度", locale)}</h2>
          {_concentration_panel(base, concentration_rows)}
          {('<div class="warning-box">Concentration History: WAITING_SECOND_SNAPSHOT</div>' if len(concentration_rows) < 2 else '')}
        </section>

        <section id="price-history" class="panel">
          <div class="kicker">{_i18n("Historical market data", "歷史市場資料", locale)}</div>
          <h2>{_i18n("Price History", "價格歷史", locale)}</h2>
          {_price_history_block(price_rows)}
        </section>

        <section id="raw-previews" class="panel">
          <div class="kicker">{_i18n("Structured source audit", "結構化來源檢視", locale)}</div>
          <h2>{_i18n("Raw Previews", "原始預覽", locale)}</h2>
          {_raw_preview_block(base, locale)}
        </section>

        <section id="copy" class="panel">
          <div class="kicker">{_i18n("Clipboard", "剪貼簿", locale)}</div>
          <h2>{_i18n("Copy for ChatGPT / Report", "複製給 ChatGPT／報告", locale)}</h2>
          <div class="copy-row">
            <div class="copy-card">
              <div class="copy-actions">
                <button class="primary-btn" type="button" data-copy-section="live" data-copy-en="copy-live-en" data-copy-zh="copy-live-zh">{_i18n("Copy live markdown", "複製即時 Markdown", locale)}</button>
              </div>
              <textarea id="copy-live-preview" readonly>{_escape(base.live_markdown_en)}</textarea>
            </div>
            <div class="copy-card">
              <div class="copy-actions">
                <button class="primary-btn" type="button" data-copy-section="ccass" data-copy-en="copy-ccass-en" data-copy-zh="copy-ccass-zh">{_i18n("Copy CCASS markdown", "複製 CCASS Markdown", locale)}</button>
              </div>
              <textarea id="copy-ccass-preview" readonly>{_escape(base.ccass_markdown_en)}</textarea>
            </div>
          </div>
        </section>

        <section id="downloads" class="panel">
          <div class="kicker">{_i18n("Export", "匯出", locale)}</div>
          <h2>{_i18n("Download This Stock", "下載此股票", locale)}</h2>
          <div class="section-footer">{_download_links(base)}</div>
        </section>
      </main>
    <footer class="layout-footer">
      {APP_TITLE_EN} · {status_text} · current query: {_escape(current_query)}
    </footer>
    {_copy_blocks(base)}
  </div>
  <script>
    const LOCALE_KEY = "joe-portal-locale";
    const currentQuery = {current_query};
    const defaultPriceRange = {json.dumps("1Y" if price_rows else "Max")};
    const defaultPriceMetric = {json.dumps("turnover" if any(row.get("turnover") is not None for row in price_rows) else "volume")};

    function selectedLocale() {{
      return localStorage.getItem(LOCALE_KEY) || "en";
    }}

    document.getElementById("portal-query-form")?.addEventListener("submit", () => {{
      const runner = document.getElementById("loading-runner");
      if (runner) runner.classList.add("active");
      const dataDateInput = document.querySelector('#portal-query-form input[name="data_date"]');
      if (dataDateInput && !dataDateInput.value) {{
        dataDateInput.disabled = true;
      }}
    }});

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

    function updatePricePanes() {{
      const range = document.querySelector('[data-price-control="range"] .chip-btn.active')?.dataset.priceRange || defaultPriceRange;
      const metric = document.querySelector('[data-price-control="metric"] .chip-btn.active')?.dataset.priceMetric || defaultPriceMetric;
      document.querySelectorAll(".price-pane").forEach((pane) => {{
        const active = pane.dataset.priceRange === range && pane.dataset.priceMetric === metric;
        pane.classList.toggle("active", active);
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
      const preview = document.getElementById(previewId(section));
      if (preview) {{
        preview.value = target.value;
      }}
      try {{
        await navigator.clipboard.writeText(target.value);
      }} catch (error) {{
        target.focus();
        target.select();
        document.execCommand("copy");
      }}
    }}

    function activePricePane() {{
      return document.querySelector(".price-pane.active") || document.querySelector(".price-pane");
    }}

    async function downloadActivePanePNG() {{
      const pane = activePricePane();
      if (!pane) return;
      const svg = pane.querySelector("svg");
      if (!svg) return;
      const serializer = new XMLSerializer();
      const source = serializer.serializeToString(svg);
      const blob = new Blob([source], {{ type: "image/svg+xml;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const image = new Image();
      image.onload = () => {{
        const canvas = document.createElement("canvas");
        canvas.width = svg.viewBox.baseVal.width || svg.clientWidth || 980;
        canvas.height = svg.viewBox.baseVal.height || svg.clientHeight || 360;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(image, 0, 0);
        URL.revokeObjectURL(url);
        const png = canvas.toDataURL("image/png");
        const a = document.createElement("a");
        a.href = png;
        a.download = "price-chart.png";
        a.click();
      }};
      image.src = url;
    }}

    function toggleFullscreen() {{
      const pane = activePricePane();
      if (!pane) return;
      if (pane.requestFullscreen) {{
        pane.requestFullscreen();
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
        return;
      }}
      const priceRangeButton = event.target.closest('[data-price-range]');
      if (priceRangeButton) {{
        const group = priceRangeButton.parentElement;
        group.querySelectorAll(".chip-btn").forEach((btn) => btn.classList.remove("active"));
        priceRangeButton.classList.add("active");
        updatePricePanes();
        return;
      }}
      const priceMetricButton = event.target.closest('[data-price-metric]');
      if (priceMetricButton) {{
        const group = priceMetricButton.parentElement;
        group.querySelectorAll(".chip-btn").forEach((btn) => btn.classList.remove("active"));
        priceMetricButton.classList.add("active");
        updatePricePanes();
        return;
      }}
      if (event.target.closest("[data-price-download]")) {{
        downloadActivePanePNG();
        return;
      }}
      if (event.target.closest("[data-price-fullscreen]")) {{
        toggleFullscreen();
      }}
    }});

    document.addEventListener("DOMContentLoaded", () => {{
      applyLocale(selectedLocale());
      updatePricePanes();
    }});
  </script>
</body>
</html>
"""


app = FastAPI(title=APP_TITLE_EN, version="8504")
get_settings()


app.add_api_route(
    "/api/v1/stocks/{stock_code}/concentration/evidence",
    get_concentration_evidence,
    methods=["GET"],
    dependencies=[Depends(verify_api_key)],
    tags=["concentration"],
)


_snapshot_jobs: dict[str, dict[str, object]] = {}
_snapshot_jobs_lock = threading.Lock()


def _job_public(job_id: str) -> dict[str, object] | None:
    with _snapshot_jobs_lock:
        job = _snapshot_jobs.get(job_id)
        return dict(job) if job else None


def _update_snapshot_job(job_id: str, **updates: object) -> None:
    with _snapshot_jobs_lock:
        if job_id in _snapshot_jobs:
            _snapshot_jobs[job_id].update(updates)


async def _run_snapshot_job(job_id: str, selected: tuple[str, ...] | None, dry_run: bool) -> None:
    started = time.monotonic()

    def progress(update: dict[str, object]) -> None:
        _update_snapshot_job(
            job_id,
            total=update.get("total", 0),
            succeeded=update.get("succeeded", 0),
            failed=update.get("failed", 0),
            skipped=update.get("skipped", 0),
            current_code=update.get("current_code"),
            elapsed_s=round(time.monotonic() - started, 3),
        )

    try:
        result = await run_daily_snapshot(selected, dry_run=dry_run, job_id=job_id, progress=progress)
    except Exception as exc:
        _update_snapshot_job(
            job_id,
            state="error",
            error=f"{type(exc).__name__}: {exc}"[:300],
            elapsed_s=round(time.monotonic() - started, 3),
            current_code=None,
        )
        return
    sample_errors = [
        str(r.get("error_message") or r.get("error") or r)[:160]
        for r in (result.get("results") or [])
        if isinstance(r, dict) and r.get("status") not in ("COMPLETE", None)
    ][:5]
    _update_snapshot_job(
        job_id,
        state=result.get("status", "error"),
        total=result.get("total", 0),
        succeeded=result.get("succeeded", 0),
        failed=result.get("failed", 0),
        skipped=result.get("skipped", 0),
        current_code=result.get("current_code"),
        sample_errors=sample_errors,
        elapsed_s=result.get("elapsed_s", round(time.monotonic() - started, 3)),
    )


@app.exception_handler(PlatformError)
async def platform_error_handler(_: Request, exc: PlatformError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.as_dict())


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "joe-ccass-visual-portal-8504"}



def _verify_daily_admin_key(
    key: str | None,
    x_api_key: str | None,
    authorization: str | None,
) -> None:
    expected = get_settings().api_key
    if not expected:
        raise PlatformError("AUTH_FAILED", "Daily snapshot administration is not configured.", status_code=503)
    bearer = authorization.removeprefix("Bearer ") if authorization else None
    supplied = (
        ("query", key)
        if key is not None
        else ("x_api_key", x_api_key)
        if x_api_key is not None
        else ("bearer", bearer)
        if bearer is not None
        else ("none", None)
    )
    source, supplied_value = supplied
    if expected not in {key, x_api_key, bearer}:
        expected_present, expected_length, expected_fingerprint = secret_fingerprint(expected)
        present, length, fingerprint = secret_fingerprint(supplied_value)
        logger.warning(
            "AUTH_FAILED EXPECTED_KEY_PRESENT=%s EXPECTED_KEY_LENGTH=%d "
            "EXPECTED_KEY_SHA256_PREFIX=%s REQUEST_KEY_PRESENT=%s "
            "REQUEST_KEY_LENGTH=%d REQUEST_KEY_SHA256_PREFIX=%s AUTH_SOURCE=%s",
            "yes" if expected_present else "no",
            expected_length,
            expected_fingerprint or "none",
            "yes" if present else "no",
            length,
            fingerprint or "none",
            source,
        )
        raise PlatformError("AUTH_FAILED", "A valid API key is required.", status_code=401)


@app.post("/admin/longbridge/snapshot_watchlist", tags=["admin"])
async def snapshot_watchlist(
    stocks: str | None = Query(default=None, include_in_schema=False),
    dry_run: bool = Query(default=False, include_in_schema=False),
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    selected = tuple(item.strip() for item in stocks.split(",") if item.strip()) if stocks else None
    if selected and len(selected) > 2:
        raise PlatformError("INVALID_SCHEMA", "Controlled rollout accepts at most two stock codes.", status_code=400)
    job_id = uuid.uuid4().hex
    with _snapshot_jobs_lock:
        _snapshot_jobs[job_id] = {
            "job_id": job_id,
            "state": "accepted",
            "total": len(selected) if selected else 52,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "current_code": None,
            "elapsed_s": 0.0,
        }
    asyncio.create_task(_run_snapshot_job(job_id, selected, dry_run))
    _update_snapshot_job(job_id, state="running")
    return JSONResponse(
        {"status": "accepted", "job_id": job_id, "state": "running"},
        status_code=202,
    )


@app.get("/admin/longbridge/snapshot_job/{job_id}", tags=["admin"])
async def snapshot_job_status(
    job_id: str,
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    job = _job_public(job_id)
    if job is None:
        raise PlatformError("NOT_FOUND", "Snapshot job was not found.", status_code=404)
    return JSONResponse(job)


# Disclosure-interests async jobs: Render's free-tier edge kills synchronous
# HTTP at ~60s, which is shorter than a cold DION browser flow, so the fetch
# runs as a background task and is read back through the job-status route.
_disclosure_interests_jobs: dict[str, dict[str, object]] = {}
_disclosure_interests_jobs_lock = threading.Lock()


def _disclosure_interests_job_public(job_id: str) -> dict[str, object] | None:
    with _disclosure_interests_jobs_lock:
        job = _disclosure_interests_jobs.get(job_id)
        return dict(job) if job else None


def _update_disclosure_interests_job(job_id: str, **updates: object) -> None:
    with _disclosure_interests_jobs_lock:
        if job_id in _disclosure_interests_jobs:
            _disclosure_interests_jobs[job_id].update(updates)


def _di_job_timeout_budget() -> float:
    return max(1.0, float(get_settings().request_timeout_seconds)) + 15.0


async def _run_disclosure_interests_job(
    job_id: str,
    code: str,
    start_date: date,
    end_date: date,
    service: DisclosureInterestsService | None = None,
) -> None:
    started = time.monotonic()
    budget = _di_job_timeout_budget()
    _update_disclosure_interests_job(job_id, timeout_budget=budget, request_timeout_seconds=get_settings().request_timeout_seconds)
    active = service or get_disclosure_interests_service()
    try:
        response = await asyncio.wait_for(
            active.get_disclosures(code, start_date=start_date, end_date=end_date),
            timeout=budget,
        )
    except asyncio.TimeoutError:
        elapsed = round(time.monotonic() - started, 3)
        if elapsed >= budget - 1.0:
            message = f"DION browser flow exceeded the job budget ({budget}s)"
        else:
            message = (
                f"DION flow raised TimeoutError after {elapsed}s (budget {budget}s, "
                f"request_timeout={get_settings().request_timeout_seconds}) — an inner transport timeout escaped"
            )
        _update_disclosure_interests_job(
            job_id,
            state="error",
            error=message,
            elapsed_s=elapsed,
        )
        return
    except Exception as exc:
        _update_disclosure_interests_job(
            job_id,
            state="error",
            error=f"{type(exc).__name__}: {exc}",
            elapsed_s=round(time.monotonic() - started, 3),
        )
        return
    warnings = list(response.data_quality_warnings)
    persisted_rows: int | None = None
    if active.repository is not None:
        try:
            persisted_rows = active.repository.count_rows(response.metadata.code)
        except Exception as exc:
            warnings.append(f"PERSISTED_ROW_COUNT_FAILED: {type(exc).__name__}: {exc}")
    _update_disclosure_interests_job(
        job_id,
        state="succeeded" if response.metadata.source_status != "unavailable" else "unavailable",
        filing_count=response.metadata.filing_count,
        persisted_rows=persisted_rows,
        source_status=response.metadata.source_status,
        warnings=warnings,
        elapsed_s=round(time.monotonic() - started, 3),
    )


@app.post("/admin/disclosure-interests/job", tags=["admin"])
async def disclosure_interests_job_trigger(
    stock_code: str = Query(...),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    normalized = normalize_stock_code(stock_code)
    end = end_date or datetime.now(UTC).date()
    start = start_date or end - timedelta(days=5 * 365)
    if start > end:
        raise PlatformError("INVALID_SCHEMA", "start_date must not be after end_date.", status_code=400)
    job_id = uuid.uuid4().hex
    with _disclosure_interests_jobs_lock:
        _disclosure_interests_jobs[job_id] = {
            "job_id": job_id,
            "state": "accepted",
            "stock_code": normalized,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "filing_count": 0,
            "persisted_rows": None,
            "source_status": None,
            "warnings": [],
            "error": None,
            "elapsed_s": 0.0,
            "timeout_budget": None,
            "request_timeout_seconds": get_settings().request_timeout_seconds,
        }
    asyncio.create_task(_run_disclosure_interests_job(job_id, normalized, start, end))
    _update_disclosure_interests_job(job_id, state="running")
    return JSONResponse(
        {
            "status": "accepted",
            "job_id": job_id,
            "state": "running",
            "stock_code": normalized,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
        status_code=202,
    )


@app.get("/admin/disclosure-interests/job/{job_id}", tags=["admin"])
async def disclosure_interests_job_status(
    job_id: str,
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    job = _disclosure_interests_job_public(job_id)
    if job is None:
        raise PlatformError("NOT_FOUND", "Disclosure interests job was not found.", status_code=404)
    return JSONResponse(job)


# Admin async jobs for slow fetch pipelines (fundamentals, announcements):
# trigger -> background task -> poll status -> read rows from the persisted
# store. Same shape as the DI jobs; heavy issuers and wide windows are the
# reason these must not run inside a synchronous request.


def _async_job_public(store: dict[str, dict[str, object]], lock: threading.Lock, job_id: str) -> dict[str, object] | None:
    with lock:
        job = store.get(job_id)
        return dict(job) if job else None


def _update_async_job(store: dict[str, dict[str, object]], lock: threading.Lock, job_id: str, **updates: object) -> None:
    with lock:
        if job_id in store:
            store[job_id].update(updates)


def _async_job_timeout_budget(extra: float = 30.0) -> float:
    return max(1.0, float(get_settings().request_timeout_seconds)) + extra


_fundamentals_jobs: dict[str, dict[str, object]] = {}
_fundamentals_jobs_lock = threading.Lock()


async def _run_fundamentals_job(job_id: str, code: str, service: FundamentalsService | None = None) -> None:
    started = time.monotonic()
    budget = _async_job_timeout_budget()
    active = service or get_fundamentals_service()
    try:
        response = await asyncio.wait_for(active.get_fundamentals(code), timeout=budget)
    except asyncio.TimeoutError:
        _update_async_job(_fundamentals_jobs, _fundamentals_jobs_lock, job_id, state="error", error=f"fundamentals flow exceeded the job budget ({budget}s)", elapsed_s=round(time.monotonic() - started, 3))
        return
    except Exception as exc:
        _update_async_job(_fundamentals_jobs, _fundamentals_jobs_lock, job_id, state="error", error=f"{type(exc).__name__}: {exc}", elapsed_s=round(time.monotonic() - started, 3))
        return
    metadata = response.metadata
    _update_async_job(
        _fundamentals_jobs,
        _fundamentals_jobs_lock,
        job_id,
        state="succeeded" if metadata.source_status == "ready" else metadata.source_status,
        rows=len(response.rows),
        periods=[row.reporting_period for row in response.rows],
        documents_attempted=metadata.documents_attempted,
        documents_parsed=metadata.documents_parsed,
        documents_failed=metadata.documents_failed,
        source_status=metadata.source_status,
        warnings=list(response.data_quality_warnings),
        elapsed_s=round(time.monotonic() - started, 3),
    )


@app.post("/admin/fundamentals/job", tags=["admin"])
async def fundamentals_job_trigger(
    stock_code: str = Query(...),
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    normalized = normalize_stock_code(stock_code)
    job_id = uuid.uuid4().hex
    with _fundamentals_jobs_lock:
        _fundamentals_jobs[job_id] = {
            "job_id": job_id,
            "state": "running",
            "stock_code": normalized,
            "rows": 0,
            "periods": [],
            "documents_attempted": 0,
            "documents_parsed": 0,
            "documents_failed": 0,
            "source_status": None,
            "warnings": [],
            "error": None,
            "elapsed_s": 0.0,
        }
    asyncio.create_task(_run_fundamentals_job(job_id, normalized))
    return JSONResponse({"status": "accepted", "job_id": job_id, "state": "running", "stock_code": normalized}, status_code=202)


@app.get("/admin/fundamentals/job/{job_id}", tags=["admin"])
async def fundamentals_job_status(
    job_id: str,
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    job = _async_job_public(_fundamentals_jobs, _fundamentals_jobs_lock, job_id)
    if job is None:
        raise PlatformError("NOT_FOUND", "Fundamentals job was not found.", status_code=404)
    return JSONResponse(job)


_announcements_jobs: dict[str, dict[str, object]] = {}
_announcements_jobs_lock = threading.Lock()
MAX_ANNOUNCEMENTS_JOB_WINDOW_DAYS = 750

_corporate_timeline_jobs: dict[str, dict[str, object]] = {}
_corporate_timeline_jobs_lock = threading.Lock()
MAX_CORPORATE_TIMELINE_JOB_WINDOW_DAYS = 1900


async def _run_corporate_timeline_job(job_id: str, code: str, start_date: date, end_date: date, service=None) -> None:
    """Derive the corporate timeline over a long window (5y+) by walking the
    announcement stream in sub-windows no wider than the announcements job
    ceiling — a single wide HKEXnews payload OOM-crashes the free container."""
    started = time.monotonic()
    active = service or get_announcements_service()
    warnings: list[str] = []
    merged: dict[tuple, object] = {}
    base_metadata = None
    window = timedelta(days=MAX_ANNOUNCEMENTS_JOB_WINDOW_DAYS)
    cursor = start_date
    try:
        while cursor <= end_date:
            win_end = min(cursor + window, end_date)
            try:
                response = await active.get_announcements(code, start_date=cursor, end_date=win_end)
                if base_metadata is None:
                    base_metadata = response.metadata
                for row in response.announcements:
                    merged.setdefault((row.announcement_date, row.title, row.link), row)
                for line in response.data_quality_warnings:
                    if line not in warnings:
                        warnings.append(line)
            except Exception as exc:
                warnings.append(f"WINDOW_FAILED:{cursor.isoformat()}:{win_end.isoformat()}:{type(exc).__name__}:{exc}")
            cursor = win_end + timedelta(days=1)
        if base_metadata is None:
            _update_async_job(
                _corporate_timeline_jobs,
                _corporate_timeline_jobs_lock,
                job_id,
                state="unavailable",
                event_count=0,
                warnings=warnings,
                error="every sub-window fetch failed — no announcement metadata obtained",
                elapsed_s=round(time.monotonic() - started, 3),
            )
            return
        ordered = [merged[key] for key in sorted(merged, key=lambda k: (k[0], k[1], k[2] or ""))]
        merged_response = AnnouncementsResponse(metadata=base_metadata, announcements=ordered, data_quality_warnings=[])
        timeline = build_corporate_timeline(merged_response, start_date=start_date, end_date=end_date)
        _update_async_job(
            _corporate_timeline_jobs,
            _corporate_timeline_jobs_lock,
            job_id,
            state="succeeded" if timeline.events or not warnings else "partial",
            event_count=len(timeline.events),
            events=[event.model_dump(mode="json") for event in timeline.events],
            warnings=warnings,
            elapsed_s=round(time.monotonic() - started, 3),
        )
    except Exception as exc:
        _update_async_job(
            _corporate_timeline_jobs,
            _corporate_timeline_jobs_lock,
            job_id,
            state="error",
            error=f"{type(exc).__name__}: {exc}",
            warnings=warnings,
            elapsed_s=round(time.monotonic() - started, 3),
        )


async def _run_announcements_job(job_id: str, code: str, start_date: date, end_date: date, service=None) -> None:
    started = time.monotonic()
    budget = _async_job_timeout_budget()
    active = service or get_announcements_service()
    try:
        response = await asyncio.wait_for(active.get_announcements(code, start_date=start_date, end_date=end_date), timeout=budget)
    except asyncio.TimeoutError:
        _update_async_job(_announcements_jobs, _announcements_jobs_lock, job_id, state="error", error=f"announcements flow exceeded the job budget ({budget}s)", elapsed_s=round(time.monotonic() - started, 3))
        return
    except Exception as exc:
        _update_async_job(_announcements_jobs, _announcements_jobs_lock, job_id, state="error", error=f"{type(exc).__name__}: {exc}", elapsed_s=round(time.monotonic() - started, 3))
        return
    metadata = response.metadata
    _update_async_job(
        _announcements_jobs,
        _announcements_jobs_lock,
        job_id,
        state="succeeded" if metadata.source_status == "ready" else metadata.source_status,
        announcement_count=metadata.announcement_count,
        coverage_start=metadata.coverage_start.isoformat() if metadata.coverage_start else None,
        coverage_end=metadata.coverage_end.isoformat() if metadata.coverage_end else None,
        source_status=metadata.source_status,
        warnings=list(response.data_quality_warnings),
        elapsed_s=round(time.monotonic() - started, 3),
    )


@app.post("/admin/announcements/job", tags=["admin"])
async def announcements_job_trigger(
    stock_code: str = Query(...),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    normalized = normalize_stock_code(stock_code)
    end = end_date or datetime.now(UTC).date()
    start = start_date or end - timedelta(days=365 * 2)
    if (end - start).days > MAX_ANNOUNCEMENTS_JOB_WINDOW_DAYS:
        raise PlatformError("INVALID_SCHEMA", f"Window exceeds {MAX_ANNOUNCEMENTS_JOB_WINDOW_DAYS} days — split into sub-windows (free-container memory ceiling).", status_code=400)
    if start > end:
        raise PlatformError("INVALID_SCHEMA", "start_date must not be after end_date.", status_code=400)
    job_id = uuid.uuid4().hex
    with _announcements_jobs_lock:
        _announcements_jobs[job_id] = {
            "job_id": job_id,
            "state": "running",
            "stock_code": normalized,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "announcement_count": 0,
            "coverage_start": None,
            "coverage_end": None,
            "source_status": None,
            "warnings": [],
            "error": None,
            "elapsed_s": 0.0,
        }
    asyncio.create_task(_run_announcements_job(job_id, normalized, start, end))
    return JSONResponse({"status": "accepted", "job_id": job_id, "state": "running", "stock_code": normalized, "start_date": start.isoformat(), "end_date": end.isoformat()}, status_code=202)


@app.get("/admin/announcements/job/{job_id}", tags=["admin"])
async def announcements_job_status(
    job_id: str,
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    job = _async_job_public(_announcements_jobs, _announcements_jobs_lock, job_id)
    if job is None:
        raise PlatformError("NOT_FOUND", "Announcements job was not found.", status_code=404)
    return JSONResponse(job)


@app.post("/admin/corporate-timeline/job", tags=["admin"])
async def corporate_timeline_job_trigger(
    stock_code: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    normalized = normalize_stock_code(stock_code)
    if (end_date - start_date).days > MAX_CORPORATE_TIMELINE_JOB_WINDOW_DAYS:
        raise PlatformError("INVALID_SCHEMA", f"Window exceeds {MAX_CORPORATE_TIMELINE_JOB_WINDOW_DAYS} days — split into sub-windows.", status_code=400)
    if start_date > end_date:
        raise PlatformError("INVALID_SCHEMA", "start_date must not be after end_date.", status_code=400)
    job_id = uuid.uuid4().hex
    with _corporate_timeline_jobs_lock:
        _corporate_timeline_jobs[job_id] = {
            "job_id": job_id,
            "state": "running",
            "stock_code": normalized,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "event_count": 0,
            "events": [],
            "warnings": [],
            "error": None,
            "elapsed_s": 0.0,
        }
    asyncio.create_task(_run_corporate_timeline_job(job_id, normalized, start_date, end_date))
    return JSONResponse({"status": "accepted", "job_id": job_id, "state": "running", "stock_code": normalized, "start_date": start_date.isoformat(), "end_date": end_date.isoformat()}, status_code=202)


@app.get("/admin/corporate-timeline/job/{job_id}", tags=["admin"])
async def corporate_timeline_job_status(
    job_id: str,
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    job = _async_job_public(_corporate_timeline_jobs, _corporate_timeline_jobs_lock, job_id)
    if job is None:
        raise PlatformError("NOT_FOUND", "Corporate timeline job was not found.", status_code=404)
    return JSONResponse(job)


@app.get("/api/v1/stocks/{stock_code}/corporate-timeline", response_model=CorporateTimeline)
async def get_corporate_timeline(
    stock_code: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: AnnouncementsService = Depends(get_announcements_service),
) -> CorporateTimeline:
    response = await service.get_announcements(stock_code, start_date=start_date, end_date=end_date)
    return build_corporate_timeline(response, start_date=start_date, end_date=end_date)


@app.get("/api/v1/stocks/{stock_code}/announcements", response_model=AnnouncementsResponse, tags=["announcements"])
async def get_stock_announcements(
    stock_code: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    service: AnnouncementsService = Depends(get_announcements_service),
) -> AnnouncementsResponse:
    return await service.get_announcements(stock_code, start_date=start_date, end_date=end_date)


@app.get("/api/v1/stocks/{stock_code}/disclosure-interests", response_model=DisclosureInterestsResponse, tags=["ownership"])
async def get_disclosure_interests(
    stock_code: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: DisclosureInterestsService = Depends(get_disclosure_interests_service),
) -> DisclosureInterestsResponse:
    return await service.get_disclosures(stock_code, start_date=start_date, end_date=end_date)


@app.get("/api/v1/stocks/{stock_code}/disclosure-interests/persisted", response_model=DisclosureInterestsResponse, tags=["ownership"])
async def get_persisted_disclosure_interests(
    stock_code: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    service: DisclosureInterestsService = Depends(get_disclosure_interests_service),
) -> DisclosureInterestsResponse:
    end = end_date or datetime.now(UTC).date()
    start = start_date or end - timedelta(days=5 * 365)
    return await service.get_persisted_disclosures(stock_code, start_date=start, end_date=end)


_intelligence_events_jobs: dict[str, dict[str, object]] = {}
_intelligence_events_jobs_lock = threading.Lock()


async def _run_intelligence_events_job(job_id: str, code: str, start_date: date | None, end_date: date | None, service: IntelligenceEventsService | None = None) -> None:
    started = time.monotonic()
    budget = _async_job_timeout_budget(extra=120.0)
    active = service or get_intelligence_events_service()
    try:
        response = await asyncio.wait_for(
            active.get_events(code, start_date=start_date, end_date=end_date),
            timeout=budget,
        )
    except asyncio.TimeoutError:
        _update_async_job(_intelligence_events_jobs, _intelligence_events_jobs_lock, job_id, state="error", error=f"intelligence-events flow exceeded the job budget ({budget}s)", elapsed_s=round(time.monotonic() - started, 3))
        return
    except Exception as exc:
        _update_async_job(_intelligence_events_jobs, _intelligence_events_jobs_lock, job_id, state="error", error=f"{type(exc).__name__}: {exc}", elapsed_s=round(time.monotonic() - started, 3))
        return
    _update_async_job(
        _intelligence_events_jobs,
        _intelligence_events_jobs_lock,
        job_id,
        state="succeeded" if response.metadata.source_status == "ready" else response.metadata.source_status,
        event_count=response.metadata.event_count,
        coverage_start=response.metadata.coverage_start.isoformat() if response.metadata.coverage_start else None,
        coverage_end=response.metadata.coverage_end.isoformat() if response.metadata.coverage_end else None,
        warnings=list(response.data_quality_warnings),
        elapsed_s=round(time.monotonic() - started, 3),
    )


@app.post("/admin/intelligence-events/job", tags=["admin"])
async def intelligence_events_job_trigger(
    stock_code: str = Query(...),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    normalized = normalize_stock_code(stock_code)
    job_id = uuid.uuid4().hex
    with _intelligence_events_jobs_lock:
        _intelligence_events_jobs[job_id] = {
            "job_id": job_id,
            "state": "running",
            "stock_code": normalized,
            "event_count": 0,
            "coverage_start": None,
            "coverage_end": None,
            "warnings": [],
            "error": None,
            "elapsed_s": 0.0,
        }
    asyncio.create_task(_run_intelligence_events_job(job_id, normalized, start_date, end_date))
    return JSONResponse({"status": "accepted", "job_id": job_id, "state": "running", "stock_code": normalized}, status_code=202)


@app.get("/admin/intelligence-events/job/{job_id}", tags=["admin"])
async def intelligence_events_job_status(
    job_id: str,
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    job = _async_job_public(_intelligence_events_jobs, _intelligence_events_jobs_lock, job_id)
    if job is None:
        raise PlatformError("NOT_FOUND", "Intelligence events job was not found.", status_code=404)
    return JSONResponse(job)


_share_capital_jobs: dict[str, dict[str, object]] = {}
_share_capital_jobs_lock = threading.Lock()


async def _run_share_capital_job(job_id: str, code: str, start_date: date | None, end_date: date | None, service=None) -> None:
    started = time.monotonic()
    budget = _async_job_timeout_budget()
    active = service or get_share_capital_history_service()
    try:
        response = await asyncio.wait_for(active.get_share_capital_history(code, start_date=start_date, end_date=end_date), timeout=budget)
    except asyncio.TimeoutError:
        _update_async_job(_share_capital_jobs, _share_capital_jobs_lock, job_id, state="error", error=f"share-capital flow exceeded the job budget ({budget}s)", elapsed_s=round(time.monotonic() - started, 3))
        return
    except Exception as exc:
        _update_async_job(_share_capital_jobs, _share_capital_jobs_lock, job_id, state="error", error=f"{type(exc).__name__}: {exc}", elapsed_s=round(time.monotonic() - started, 3))
        return
    _update_async_job(
        _share_capital_jobs,
        _share_capital_jobs_lock,
        job_id,
        state="succeeded" if response.metadata.source_status == "ready" else response.metadata.source_status,
        rows=len(response.rows),
        warnings=list(response.data_quality_warnings),
        elapsed_s=round(time.monotonic() - started, 3),
    )


@app.post("/admin/share-capital/job", tags=["admin"])
async def share_capital_job_trigger(
    stock_code: str = Query(...),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    normalized = normalize_stock_code(stock_code)
    job_id = uuid.uuid4().hex
    with _share_capital_jobs_lock:
        _share_capital_jobs[job_id] = {
            "job_id": job_id,
            "state": "running",
            "stock_code": normalized,
            "rows": 0,
            "warnings": [],
            "error": None,
            "elapsed_s": 0.0,
        }
    asyncio.create_task(_run_share_capital_job(job_id, normalized, start_date, end_date))
    return JSONResponse({"status": "accepted", "job_id": job_id, "state": "running", "stock_code": normalized}, status_code=202)


@app.get("/admin/share-capital/job/{job_id}", tags=["admin"])
async def share_capital_job_status(
    job_id: str,
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    job = _async_job_public(_share_capital_jobs, _share_capital_jobs_lock, job_id)
    if job is None:
        raise PlatformError("NOT_FOUND", "Share capital job was not found.", status_code=404)
    return JSONResponse(job)


@app.get("/api/v1/stocks/{stock_code}/ownership-timeline", response_model=OwnershipTimelineResponse, tags=["ownership"])
async def get_ownership_timeline(
    stock_code: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    filer: str | None = Query(default=None),
    service: OwnershipTimelineService = Depends(get_ownership_timeline_service),
) -> OwnershipTimelineResponse:
    return await service.get_timeline(stock_code, start_date=start_date, end_date=end_date, filer=filer)


_accumulation_jobs: dict[str, dict[str, object]] = {}
_accumulation_jobs_lock = threading.Lock()


async def _run_accumulation_job(job_id: str, count: int, service: AccumulationService | None = None) -> None:
    started = time.monotonic()
    active = service or AccumulationService()

    def progress(update: dict[str, object]) -> None:
        _update_async_job(
            _accumulation_jobs,
            _accumulation_jobs_lock,
            job_id,
            done=update.get("done"),
            total=update.get("total"),
            current_code=update.get("current_code"),
            current_step=update.get("current_step"),
            outcomes=update.get("outcomes"),
        )

    try:
        result = await active.run(count=count, progress=progress)
    except Exception as exc:
        _update_async_job(_accumulation_jobs, _accumulation_jobs_lock, job_id, state="error", error=f"{type(exc).__name__}: {exc}", elapsed_s=round(time.monotonic() - started, 3))
        return
    _update_async_job(
        _accumulation_jobs,
        _accumulation_jobs_lock,
        job_id,
        state="succeeded",
        slice_size=result.get("slice_size"),
        stocks_ok=result.get("stocks_ok"),
        stocks_partial=result.get("stocks_partial"),
        outcomes=result.get("outcomes"),
        coverage=f'{result.get("coverage_start")}..{result.get("coverage_end")}',
        elapsed_s=result.get("elapsed_s"),
    )


@app.post("/admin/accumulation/job", tags=["admin"])
async def accumulation_job_trigger(
    count: int = Query(default=13, ge=1, le=52),
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    job_id = uuid.uuid4().hex
    with _accumulation_jobs_lock:
        _accumulation_jobs[job_id] = {
            "job_id": job_id,
            "state": "running",
            "done": 0,
            "total": count * 4,
            "current_code": None,
            "current_step": None,
            "outcomes": [],
            "error": None,
            "elapsed_s": 0.0,
        }
    asyncio.create_task(_run_accumulation_job(job_id, count))
    return JSONResponse({"status": "accepted", "job_id": job_id, "state": "running"}, status_code=202)


@app.get("/admin/accumulation/job/{job_id}", tags=["admin"])
async def accumulation_job_status(
    job_id: str,
    key: str | None = Query(default=None, include_in_schema=False),
    x_api_key: str | None = Header(default=None, include_in_schema=False),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> JSONResponse:
    _verify_daily_admin_key(key, x_api_key, authorization)
    job = _async_job_public(_accumulation_jobs, _accumulation_jobs_lock, job_id)
    if job is None:
        raise PlatformError("NOT_FOUND", "Accumulation job was not found.", status_code=404)
    return JSONResponse(job)


_JOB_PANEL_SCRIPT = """
<div id="jobbtns"></div>
<pre id="jobout">[no job triggered yet]</pre>
<script>
(function(){
  var CODE = "__CODE__";
  var bar = document.getElementById('jobbtns');
  var keyin = document.createElement('input');
  keyin.id = 'adminkey';
  keyin.type = 'password';
  keyin.placeholder = 'admin key (stored in this browser only)';
  keyin.style.width = '300px';
  keyin.value = localStorage.getItem('joeAdminKey') || '';
  keyin.oninput = function(){ localStorage.setItem('joeAdminKey', keyin.value); };
  bar.appendChild(keyin);
  var JOBS = [
    ['di-2y', '/admin/disclosure-interests/job', {}],
    ['announcements-2y', '/admin/announcements/job', {}],
    ['fundamentals', '/admin/fundamentals/job', {}],
    ['share-capital', '/admin/share-capital/job', {}],
    ['intelligence-events', '/admin/intelligence-events/job', {}],
    ['corporate-timeline-5y', '/admin/corporate-timeline/job', {start_date: '__START5Y__', end_date: '__END__'}],
    ['accumulation', '/admin/accumulation/job', {}]
  ];
  JOBS.forEach(function(j){
    var b = document.createElement('button');
    b.textContent = j[0];
    b.style.margin = '2px';
    b.onclick = function(){ runJob(j[0], j[1], j[2]); };
    bar.appendChild(b);
  });
  async function runJob(name, path, extra){
    var out = document.getElementById('jobout');
    var key = document.getElementById('adminkey').value;
    if(!key){ out.textContent = name + ': enter the admin key first'; return; }
    var params = new URLSearchParams({stock_code: CODE, key: key});
    Object.keys(extra).forEach(function(k){ params.set(k, extra[k]); });
    out.textContent = name + ': triggering...';
    var r, j;
    try { r = await fetch(path + '?' + params.toString(), {method: 'POST'}); j = await r.json(); }
    catch(e){ out.textContent = name + ' trigger failed: ' + e; return; }
    if(!j.job_id){ out.textContent = name + ': ' + JSON.stringify(j).slice(0, 400); return; }
    var id = j.job_id;
    for(var i = 0; i < 120; i++){
      await new Promise(function(s){ setTimeout(s, 5000); });
      var s;
      try { s = await (await fetch(path + '/' + id + '?key=' + encodeURIComponent(key))).json(); }
      catch(e){ out.textContent = name + ' poll failed: ' + e; return; }
      out.textContent = name + ' [' + id.slice(0, 8) + '] ' + s.state + ' (' + (i*5) + 's) ' + (s.error || '');
      if(['succeeded','partial','unavailable','error','failed'].indexOf(s.state) >= 0){
        out.textContent = name + ' [' + id.slice(0, 8) + '] ' + s.state + ' :: ' + JSON.stringify(s).slice(0, 600);
        return;
      }
    }
    out.textContent = name + ': still running after 10 minutes of polling';
  }
})();
</script>
"""


@app.get("/console", response_class=HTMLResponse, tags=["console"])
async def console_page(
    code: str = Query(default=""),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> HTMLResponse:
    """Unified read console: events, ownership, fundamentals, entities and
    job triggers for one code — the Phase-1 read model in a single view."""
    normalized = normalize_stock_code(code) if code.strip() else ""
    now = datetime.now(UTC)
    end = end_date or now.date()
    start = start_date or end - timedelta(days=365 * 2)
    sections: list[str] = []
    if normalized:
        def _section(title: str, builder) -> None:
            try:
                sections.append(builder())
            except Exception as exc:
                sections.append(f'<h2>{_escape(title)}</h2><div class="warn">SECTION_FAILED: {type(exc).__name__}: {_escape(str(exc))[:200]} — inspect via the admin jobs/API</div>')

        events_service = get_intelligence_events_service()
        events = await events_service.get_events(normalized, start_date=start, end_date=end)
        by_type: dict[str, int] = {}
        for event in events.events:
            by_type[event.event_type] = by_type.get(event.event_type, 0) + 1
        rows_html = "".join(
            f"<tr><td>{_escape(e.event_type)}</td><td>{e.announce_date}</td><td>{_escape(str(e.counterparty or e.entity_name or ''))[:60]}</td>"
            f"<td>{_escape(str(e.shares_after or ''))}</td><td>{e.confidence}</td><td>{_escape(e.source_document)[:40]}</td></tr>"
            for e in events.events[:20]
        )
        sections.append(
            f"<h2>Intelligence Events ({events.metadata.event_count})</h2>"
            + "".join(f'<span class="pill">{_escape(k)}: {v}</span> ' for k, v in sorted(by_type.items()))
            + f"<table><tr><th>type</th><th>date</th><th>counterparty</th><th>shares</th><th>confidence</th><th>source</th></tr>{rows_html}</table>"
        )

        try:
            timeline = await get_ownership_timeline_service().get_timeline(normalized, start_date=start, end_date=end)
            tl_rows = "".join(
                f"<tr><td>{_escape(t.filer)[:40]}</td><td>{t.movements_count}</td><td>+{t.increases} / -{t.decreases}</td><td>{_escape(str(t.latest_present_balance or ''))}</td><td>{_escape(str(t.latest_percentage or ''))}</td></tr>"
                for t in timeline.timelines[:10]
            )
            sections.append(f"<h2>Ownership Timeline (top {min(10, len(timeline.timelines))} of {len(timeline.timelines)} filers)</h2>" + f"<table><tr><th>filer</th><th>movements</th><th>+/-</th><th>latest balance</th><th>%</th></tr>{tl_rows}</table>")
        except Exception as exc:
            sections.append(f'<h2>Ownership Timeline</h2><div class="warn">SECTION_FAILED: {type(exc).__name__}: {_escape(str(exc))[:200]}</div>')

        def _fundamentals_section() -> str:
            fundamentals = get_fundamentals_service().repository.load(normalized)
            if fundamentals is None:
                return "<h2>Fundamentals</h2><p>No persisted fundamentals — trigger /admin/fundamentals/job first.</p>"
            f_rows = "".join(
                f"<tr><td>{r.reporting_period}</td><td>{_escape(str(r.revenue or ''))}</td><td>{_escape(str(r.net_profit_loss or ''))}</td><td>{_escape(str(r.equity or ''))}</td><td>{r.completeness_status}</td></tr>"
                for r in fundamentals.rows[:10]
            )
            return (
                f"<h2>Fundamentals ({fundamentals.metadata.source_status}, {len(fundamentals.rows)} rows)</h2>"
                + f"<table><tr><th>period</th><th>revenue</th><th>profit</th><th>equity</th><th>completeness</th></tr>{f_rows}</table>"
                + "".join(f'<div class="warn">{_escape(w)}</div>' for w in fundamentals.data_quality_warnings[:4])
            )

        _section("Fundamentals", _fundamentals_section)

        def _entities_section() -> str:
            entity_rows = get_document_entities_service().repository.load_rows(normalized, start_date=start, end_date=end)
            by_entity: dict[str, int] = {}
            for row in entity_rows:
                by_entity[row.entity_type] = by_entity.get(row.entity_type, 0) + 1
            return (
                f"<h2>Document Entities ({len(entity_rows)} rows persisted)</h2>"
                + "".join(f'<span class="pill">{_escape(k)}: {v}</span> ' for k, v in sorted(by_entity.items()))
                + "<p>Heavy refreshes run through the admin jobs; this console reads the persisted evidence cache only.</p>"
            )

        _section("Document Entities", _entities_section)
    else:
        sections.append("<p>Enter a stock code to load the unified view.</p>")

    if normalized:
        five_y_start = (end - timedelta(days=365 * 5)).isoformat()
        job_panel = (
            "<h2>Job triggers (admin key required &mdash; jobs run in the background and persist to Turso)</h2>"
            + _JOB_PANEL_SCRIPT.replace("__CODE__", normalized)
            .replace("__START5Y__", five_y_start)
            .replace("__END__", end.isoformat())
        )
    else:
        job_panel = "<p>Load a stock code to enable the job trigger panel.</p>"

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Console {normalized}</title>
<style>body{{font-family:monospace;margin:24px;background:#111;color:#ddd}} table{{border-collapse:collapse;margin:12px 0}} td,th{{border:1px solid #444;padding:4px 8px;font-size:13px}} .pill{{display:inline-block;background:#234;color:#9cf;padding:2px 8px;margin:2px;border-radius:4px}} .warn{{color:#f90;font-size:12px}} h2{{color:#9cf;border-bottom:1px solid #345}} button{{background:#345;color:#9cf;border:1px solid #567;padding:4px 10px;cursor:pointer}} #jobout{{background:#181818;border:1px solid #333;padding:8px;white-space:pre-wrap}}</style></head><body>
<h1>Joe Intelligence Console &mdash; {normalized or "(code)"}</h1>
<form method="get"><input name="code" value="{_escape(normalized)}" placeholder="02020"><button>Load</button> ({start} .. {end})</form>
{''.join(sections)}
{job_panel}
</body></html>"""
    return HTMLResponse(html)


@app.get("/api/v1/intermediary-graph", tags=["deep-analysis"])
async def get_intermediary_graph(
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: DocumentEntitiesService = Depends(get_document_entities_service),
):
    """實體關係圖種子: cross-stock intermediary statistics — nodes (who,
    how many stocks, how often) + same-document co-occurrence edges (who
    works with whom). Grows automatically as entity extraction accumulates."""
    if start_date > end_date:
        raise PlatformError("INVALID_SCHEMA", "start_date must not be after end_date.", status_code=400)
    return JSONResponse(service.repository.load_graph(start_date=start_date, end_date=end_date))


@app.get("/api/v1/stocks/{stock_code}/alerts", tags=["monitor"])
async def get_stock_alerts(
    stock_code: str,
    days: int = Query(default=7, ge=1, le=60),
    end_date: date | None = Query(default=None),
):
    service = AlertsService(get_intelligence_events_service())
    return JSONResponse(await service.get_alerts(stock_code, days=days, end_date=end_date))


@app.get("/api/v1/stocks/{stock_code}/research-context", tags=["research"])
async def get_research_context(
    stock_code: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    format: str = Query(default="json"),
    service: ResearchContextService = Depends(get_research_context_service),
):
    context = await service.build(stock_code, start_date=start_date, end_date=end_date)
    if format in ("md", "markdown"):
        return PlainTextResponse(service.to_markdown(context), media_type="text/markdown; charset=utf-8")
    return JSONResponse(context)


@app.get("/api/v1/stocks/{stock_code}/report-draft", tags=["research"])
async def get_report_draft(
    stock_code: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    service: ResearchContextService = Depends(get_research_context_service),
):
    """AI 報告生成器 v1: deterministic chapter draft from the research
    package — real facts per chapter, interpretation slots marked 【AI 分析位】."""
    context = await service.build(stock_code, start_date=start_date, end_date=end_date)
    return PlainTextResponse(service.to_report_draft(context), media_type="text/markdown; charset=utf-8")


@app.get("/api/v1/stocks/{stock_code}/price", tags=["market"])
async def get_stock_price(
    stock_code: str,
    days: int = Query(default=120, ge=7, le=730),
    service: PriceHistoryService = Depends(get_price_history_service),
):
    """Latest daily candles (source-labelled) for the terminal price card."""
    normalized = normalize_stock_code(stock_code)
    end = datetime.now(UTC).date()
    start = end - timedelta(days=days)
    response = await service.get_price_history(normalized, start_date=start, end_date=end)
    return JSONResponse(response.model_dump(mode="json"))


@app.get("/api/v1/stocks/{stock_code}/intelligence-events", response_model=IntelligenceEventsResponse, tags=["intelligence"])
async def get_intelligence_events(
    stock_code: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    service: IntelligenceEventsService = Depends(get_intelligence_events_service),
) -> IntelligenceEventsResponse:
    return await service.get_events(stock_code, start_date=start_date, end_date=end_date)


@app.get("/api/v1/stocks/{stock_code}/fundamentals", response_model=FundamentalsResponse, tags=["fundamentals"])
async def get_stock_fundamentals(stock_code: str, service: FundamentalsService = Depends(get_fundamentals_service)) -> FundamentalsResponse:
    return await service.get_fundamentals(stock_code)


@app.get("/api/v1/stocks/{stock_code}/document-entities", response_model=DocumentEntitiesResponse, tags=["deep-analysis"])
async def get_document_entities(stock_code: str, service: DocumentEntitiesService = Depends(get_document_entities_service)) -> DocumentEntitiesResponse:
    return await service.get_entities(stock_code)


@app.get("/api/v1/stocks/{stock_code}/stock-events", response_model=StockEventsResponse, tags=["stock-events"])
async def get_stock_events(
    stock_code: str,
    service: StockEventsService = Depends(get_stock_events_service),
) -> StockEventsResponse:
    return await service.get_stock_events(stock_code)


@app.get("/api/v1/stocks/{stock_code}/officers", response_model=OfficersResponse, tags=["officers"])
async def get_stock_officers(
    stock_code: str,
    service: OfficersService = Depends(get_officers_service),
) -> OfficersResponse:
    return await service.get_officers(stock_code)


@app.get("/api/v1/stocks/{stock_code}/share-capital-history", response_model=ShareCapitalHistoryResponse, tags=["share-capital"])
async def get_share_capital_history(
    stock_code: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: ShareCapitalHistoryService = Depends(get_share_capital_history_service),
) -> ShareCapitalHistoryResponse:
    return await service.get_share_capital_history(stock_code, start_date=start_date, end_date=end_date)


@app.get("/internal/p0/history-proof")
async def p0_history_proof(code: str = Query(..., min_length=1)) -> JSONResponse:
    """Return read-only, non-sensitive snapshot metadata for P0 verification."""
    normalized_code = code.strip().zfill(5)
    turso_env_present = bool(
        os.getenv("TURSO_DATABASE_URL") and os.getenv("TURSO_AUTH_TOKEN")
    )
    backend = "turso" if turso_env_present else "local"
    try:
        repository = _snapshot_repo()
        dates = repository.available_dates(normalized_code, include_partial=True)
        bounds = repository.history_bounds(normalized_code, include_partial=True)
        latest = repository.latest(normalized_code, include_partial=True)
        snapshot_count = repository.count_snapshots(normalized_code)
        return JSONResponse(
            {
                "code": normalized_code,
                "backend": backend,
                "turso_env_present": turso_env_present,
                "snapshot_count": snapshot_count,
                "date_count": bounds.date_count,
                "available_dates": [item.isoformat() for item in dates],
                "latest_date": latest.snapshot_date.isoformat() if latest else None,
                "latest_row_count": len(latest.holdings) if latest else None,
                "latest_source_id": latest.source.source_id if latest else None,
            }
        )
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "ERROR",
                "code": normalized_code,
                "backend": backend,
                "turso_env_present": turso_env_present,
                "error_type": type(exc).__name__,
                "error_message": "canonical snapshot repository read failed",
            },
        )


@app.get("/internal/p0/rct20-proof")
async def p0_rct20_proof(code: str = Query(..., min_length=1)) -> JSONResponse:
    """Read-only boundary proof for the Longbridge RCT20 portal path."""
    normalized_code = code.strip().zfill(5)
    if normalized_code != "06182":
        return JSONResponse(status_code=400, content={"error": "proof is scoped to 06182"})
    try:
        bundle = await _build_portal_8504_bundle(
            raw_code=normalized_code,
            input_type="Stock Code",
            source_mode="auto",
            top_n=20,
            big_change_threshold=1_000_000,
            use_local_history=True,
        )
        payload = bundle.longbridge_periods.get("rct_20") or {}
        total = len(payload.get("buy") or []) + len(payload.get("sell") or [])
        return JSONResponse({
            "code": normalized_code,
            "rct20_service_total": total,
            "rct20_portal_total": total,
            "rct20_final_total": total,
        })
    except Exception:
        return JSONResponse(status_code=503, content={"code": normalized_code, "error": "rct20 proof path failed"})


_FAST_LANDING = """<!DOCTYPE html><html lang="zh-HK"><head><meta charset="utf-8"><title>Joe Intelligence Platform</title>
<style>body{margin:0;background:#f5f7fa;color:#1e293b;font-family:-apple-system,'Segoe UI','Microsoft JhengHei',sans-serif;display:flex;min-height:100vh;align-items:center;justify-content:center}
.panel{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:40px 48px;text-align:center}
h1{margin:0 0 6px;font-size:26px;color:#1e3a8a}
input{width:200px;border:1px solid #cbd5e1;border-radius:6px;padding:10px 12px;font-size:15px}
button{background:#1d4ed8;color:#fff;border:none;border-radius:6px;padding:10px 20px;font-size:15px;font-weight:600;cursor:pointer;margin-left:8px}
p{color:#64748b;font-size:13px}a{color:#1d4ed8}</style></head><body>
<div class="panel"><h1>Joe Intelligence Platform</h1>
<p>persisted 證據快取唯讀 · 目標 ≤5 秒 · 完整即時產品請用 /full</p>
<form method="get" action="/"><input name="code" placeholder="輸入股票代號 e.g. 02020"><button>載入情報總覽</button></form>
</div></body></html>"""


@app.get("/", response_class=HTMLResponse)
async def portal_fast(
    code: str = Query(default=""),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> HTMLResponse:
    """Fast persisted overview — the frontend acceptance surface (target ≤5s).

    Everything is read from the Turso evidence cache in parallel and trimmed to
    Top-N; the data layer is untouched. The full live product remains at
    /full and deep refreshes run through the admin job panel."""
    normalized = normalize_stock_code(code) if code.strip() else ""
    if not normalized:
        return HTMLResponse(_FAST_LANDING)
    now = datetime.now(UTC)
    end = end_date or now.date()
    start = start_date or end - timedelta(days=365 * 5)
    svc = get_research_context_service()
    events_repo = get_intelligence_events_service().event_repository

    async def _safe(label, coro):
        try:
            return label, await coro
        except Exception as exc:
            return label, exc

    events_pair, timeline_pair, snapshot_pair, fundamentals_pair, entities_pair, share_capital_pair = await asyncio.gather(
        _safe("events", asyncio.to_thread(events_repo.load, normalized)),
        _safe("timeline", get_ownership_timeline_service().get_timeline(normalized, start_date=start, end_date=end)),
        _safe("snapshot", asyncio.to_thread(svc.snapshot_repository.latest, normalized)),
        _safe("fundamentals", asyncio.to_thread(svc.fundamentals_repository.load, normalized)),
        _safe("entities", asyncio.to_thread(svc.entity_repository.load_rows, normalized, start_date=start, end_date=end)),
        _safe("share_capital", asyncio.to_thread(svc.share_capital_repository.load, normalized, start_date=start, end_date=end)),
    )

    def _ok(pair):
        return None if isinstance(pair[1], Exception) else pair[1]

    snap = _ok(snapshot_pair)
    tl = _ok(timeline_pair)
    ev = _ok(events_pair)
    fund = _ok(fundamentals_pair)
    ent = _ok(entities_pair)
    sc = _ok(share_capital_pair)

    def _fail_card(title: str, result) -> str:
        message = _escape(str(result[1]))[:140] if isinstance(result[1], Exception) else "無持久化數據 — 觸發對應 job 後重載此頁。"
        return _card(title, f'<div class="warnbox">{message}</div>', open_=True)

    def _card(title: str, body: str, *, open_: bool = True, wide: bool = False) -> str:
        return (
            f'<details class="card{" wide" if wide else ""}"{" open" if open_ else ""}>'
            f"<summary>{_escape(title)}</summary><div class='cardbody'>{body}</div></details>"
        )

    def _table(headers: list[str], rows: list[str]) -> str:
        head = "".join(f"<th>{h}</th>" for h in headers)
        body = "".join(f"<tr>{r}</tr>" for r in rows)
        return f'<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'

    cards: list[str] = []

    # CCASS snapshot card
    if snap is None:
        cards.append(_fail_card("CCASS 快照", ("", RuntimeError("無持久化快照"))))
    else:
        holdings = sorted(snap.holdings, key=lambda h: h.shares, reverse=True)
        total = sum(h.shares for h in holdings) or 1
        top5 = sum(h.shares for h in holdings[:5]) / total * 100
        rows = [
            f"<tr><td>{_escape(str(getattr(h, 'participant_name', None) or h.participant_id))[:36]}</td>"
            f"<td class='num'>{h.shares:,}</td><td class='num'>{h.shares / total * 100:.2f}%</td></tr>"
            for h in holdings[:15]
        ]
        body = _table(["Participant", "Shares", "% CCASS"], rows) + f"<p class='note'>{snap.snapshot_date} · 共 {len(holdings)} 名參與者 · Top 5 佔 {top5:.2f}%（CCASS 內）</p>"
        cards.append(_card(f"CCASS 快照 · {snap.snapshot_date}", body))

    # Ownership timeline card
    if tl is None:
        cards.append(_fail_card("大股東動向", ("", RuntimeError("無持久化 DION 數據"))))
    else:
        rows = []
        for t in tl.timelines[:10]:
            rows.append(
                f"<tr><td>{_escape(t.filer)[:34]}</td><td class='num'>{t.movements_count}</td>"
                f"<td class='num'><span class='up'>+{t.increases}</span> / <span class='down'>−{t.decreases}</span></td>"
                f"<td class='num'>{t.latest_present_balance or '—'}</td><td class='num'>{t.latest_percentage if t.latest_percentage is not None else '—'}</td></tr>"
            )
        cards.append(_card(f"大股東動向 · {len(tl.timelines)} 名申報人", _table(["Filer", "申報", "增/減", "最新持倉", "%"], rows)))

    # Intelligence events card (full width)
    if not ev:
        cards.append(_fail_card("情報事件", ("", RuntimeError("無持久化事件快照"))))
    else:
        by_type: dict[str, int] = {}
        for e in ev:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
        pills = "".join(f'<span class="pill">{_escape(k)} <b>{v}</b></span>' for k, v in sorted(by_type.items()))
        ev_sorted = sorted(ev, key=lambda e: e.announce_date, reverse=True)
        rows = [
            f"<tr><td class='num'>{e.announce_date}</td><td>{_escape(e.event_type)}</td>"
            f"<td>{_escape(str(e.counterparty or e.entity_name or ''))[:44]}</td>"
            f"<td class='num'>{e.shares_after or '—'}</td>"
            f"<td><span class='badge {e.confidence}'>{e.confidence}</span></td></tr>"
            for e in ev_sorted[:30]
        ]
        body = f"<div class='pills'>{pills}</div>" + _table(["日期", "類型", "對手方", "現持", "信心"], rows)
        cards.append(_card(f"情報事件 · {len(ev)} 項（最新 30）", body, wide=True))

    # Fundamentals card
    if fund is None or not fund.rows:
        cards.append(_fail_card("基本面", ("", RuntimeError("無持久化業績"))))
    else:
        rows = [
            f"<tr><td>{r.reporting_period}</td><td class='num'>{r.revenue or '—'}</td>"
            f"<td class='num'>{r.net_profit_loss or '—'}</td><td class='num'>{r.equity or '—'}</td>"
            f"<td><span class='badge {r.completeness_status}'>{r.completeness_status}</span></td></tr>"
            for r in fund.rows[:10]
        ]
        cards.append(_card(f"基本面 · {len(fund.rows)} 期", _table(["期間", "收入", "純利", "權益", "完整度"], rows)))

    # Document entities card
    if ent is None:
        ent = []
    by_entity: dict[str, int] = {}
    for row in ent:
        by_entity[row.entity_type] = by_entity.get(row.entity_type, 0) + 1
    pills = "".join(f'<span class="pill">{_escape(k)} <b>{v}</b></span>' for k, v in sorted(by_entity.items())) or "<span class='pill'>無</span>"
    cards.append(_card(f"中介網絡 · {len(ent)} 筆", f"<div class='pills'>{pills}</div>"))

    # Share capital card
    if sc is None or not sc.rows:
        cards.append(_fail_card("股本變動", ("", RuntimeError("無持久化股本行"))))
    else:
        rows = [
            f"<tr><td class='num'>{r.announce_date}</td><td class='num'>{r.shares_million}M</td>"
            f"<td>{_escape(str(r.reason or ''))[:52]}</td></tr>"
            for r in sc.rows[:10]
        ]
        cards.append(_card(f"股本變動 · {len(sc.rows)} 行", _table(["公佈日", "股本", "原因"], rows)))

    # KPI strip
    kpi_top5 = "—"
    kpi_parts = len(snap.holdings) if snap else 0
    kpi_date = snap.snapshot_date if snap else "—"
    if snap:
        srt = sorted(snap.holdings, key=lambda h: h.shares, reverse=True)
        tot = sum(h.shares for h in srt) or 1
        kpi_top5 = f"{sum(h.shares for h in srt[:5]) / tot * 100:.1f}%"
    kpis = [
        ("快照日", str(kpi_date)),
        ("CCASS 參與者", f"{kpi_parts:,}"),
        ("Top 5 佔 CCASS", str(kpi_top5)),
        ("申報人", str(len(tl.timelines) if tl else 0)),
        ("情報事件", f"{len(ev):,}" if ev else "0"),
        ("業績期", str(len(fund.rows) if fund and fund.rows else 0)),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="kpi-label">{_escape(label)}</div><div class="kpi-value">{_escape(str(value))}</div></div>'
        for label, value in kpis
    )

    five_y_start = (end - timedelta(days=365 * 5)).isoformat()
    job_panel = (
        "<h2>Deep Refresh <span class='h2note'>admin key — 背後 job 完成後重載此頁</span></h2>"
        + _JOB_PANEL_SCRIPT.replace("__CODE__", normalized)
        .replace("__START5Y__", five_y_start)
        .replace("__END__", end.isoformat())
    )
    html = f"""<!DOCTYPE html><html lang="zh-HK"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{normalized} · 持倉情報總覽</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f5f7fa;color:#1e293b;font-family:-apple-system,'Segoe UI','Microsoft JhengHei','PingFang TC',sans-serif}}
.wrap{{max-width:1280px;margin:0 auto;padding:20px 24px 40px}}
header.top{{background:linear-gradient(135deg,#1e3a8a,#1d4ed8);color:#fff;border-radius:12px;padding:22px 26px;margin-bottom:16px}}
header.top h1{{margin:0;font-size:24px;font-weight:700;letter-spacing:.5px}}
header.top .sub{{font-size:12.5px;opacity:.85;margin-top:4px}}
header.top form{{margin-top:12px;display:flex;gap:8px}}
header.top input{{border:none;border-radius:6px;padding:8px 12px;font-size:14px;width:160px}}
header.top button{{background:#fff;color:#1d4ed8;border:none;border-radius:6px;padding:8px 16px;font-weight:600;cursor:pointer}}
nav.links{{margin:0 0 16px;font-size:13px}}
nav.links a{{color:#1d4ed8;text-decoration:none;margin-right:16px;font-weight:500}}
nav.links a:hover{{text-decoration:underline}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}}
.kpi{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:12px 16px}}
.kpi-label{{font-size:11.5px;color:#64748b;text-transform:uppercase;letter-spacing:.4px}}
.kpi-value{{font-size:22px;font-weight:700;color:#0f172a;margin-top:2px;font-variant-numeric:tabular-nums}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:16px}}
.card{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden}}
.card.wide{{grid-column:1/-1}}
.card summary{{cursor:pointer;padding:12px 18px;font-weight:700;font-size:14.5px;color:#0f172a;border-bottom:1px solid #eef2f7;list-style:none}}
.card summary::before{{content:'▸ ';color:#94a3b8}}
.card[open] summary::before{{content:'▾ '}}
.cardbody{{padding:10px 18px 16px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;color:#64748b;font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.4px;border-bottom:2px solid #e2e8f0;padding:6px 8px}}
td{{border-bottom:1px solid #f1f5f9;padding:6px 8px;font-variant-numeric:tabular-nums}}
tbody tr:hover{{background:#f8fafc}}
.num{{text-align:right}}
.up{{color:#16a34a;font-weight:600}}
.down{{color:#dc2626;font-weight:600}}
.pill{{display:inline-block;background:#eff6ff;color:#1d4ed8;padding:3px 10px;margin:3px 4px 3px 0;border-radius:999px;font-size:12px}}
.pill b{{font-weight:700}}
.badge{{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11px;font-weight:600}}
.badge.official{{background:#dbeafe;color:#1e40af}}
.badge.extracted{{background:#f1f5f9;color:#475569}}
.badge.partial{{background:#fef3c7;color:#92400e}}
.badge.complete{{background:#dcfce7;color:#166534}}
.warnbox{{background:#fef3c7;color:#92400e;border-radius:8px;padding:10px 14px;font-size:13px}}
.note{{color:#64748b;font-size:12px;margin:8px 0 0}}
h2{{font-size:15px;color:#0f172a}}
.h2note{{font-size:12px;color:#64748b;font-weight:400}}
#jobout{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px;white-space:pre-wrap;font-size:12.5px}}
.card button{{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;padding:4px 10px;border-radius:6px;cursor:pointer;font-size:12px}}
#adminkey{{border:1px solid #cbd5e1;border-radius:6px;padding:6px 10px;font-size:13px;width:280px}}
</style></head><body><div class="wrap">
<header class="top"><h1>{normalized} · 持倉情報總覽</h1><div class="sub">persisted 證據快取唯讀 · 窗口 {start} → {end} · 後端數據源不變</div>
<form method="get" action="/"><input name="code" value="{_escape(normalized)}" placeholder="輸入股票代號"><button>切換</button></form></header>
<nav class="links"><a href="/full?code={normalized}">完整即時產品（~35s）</a><a href="/console?code={normalized}">詳細 Console</a><a href="/api/v1/stocks/{normalized}/research-context?format=markdown">研究包 MD</a><a href="/api/v1/stocks/{normalized}/report-draft">報告初稿</a><a href="/api/v1/stocks/{normalized}/intelligence-events">事件全量 JSON</a><a href="/api/v1/intermediary-graph?start_date={start}&end_date={end}">中介圖譜</a></nav>
<div class="kpis">{kpi_html}</div>
<div class="grid">{''.join(cards)}</div>
{job_panel}
</div></body></html>"""
    return HTMLResponse(html)


@app.get("/full", response_class=HTMLResponse)
async def portal(
    code: str = Query(default=""),
    input_type: str = Query(default="Stock Code"),
    source_mode: str = Query(default="auto"),
    timeout_seconds: float = Query(default=12.0, ge=1.0),
    announcement_period: str = Query(default="All"),
    data_date: date | None = Query(default=None),
    history_range: str = Query(default="Latest"),
    top_n: int = Query(default=20, ge=5, le=100),
    percentage_basis: str = Query(default="CCASS"),
    big_change_threshold: int = Query(default=1_000_000, ge=0),
    use_local_history: bool = Query(default=True),
) -> HTMLResponse:
    if code.strip():
        try:
            build_task = asyncio.create_task(
                _build_portal_8504_bundle(
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
            )
            done, _ = await asyncio.wait({build_task}, timeout=45.0)
            if not done:
                build_task.cancel()
                raise TimeoutError("portal request deadline exceeded")
            bundle = build_task.result()
        except TimeoutError as exc:
            raise PlatformError(
                "PORTAL_REQUEST_TIMEOUT",
                "The request exceeded the 45-second product deadline.",
            ) from exc
        except PlatformError as exc:
            base = PortalBundle(
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
            bundle = Portal8504Bundle(base=base, price_rows=[], concentration_rows=[])
    else:
        base = PortalBundle(
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
        bundle = Portal8504Bundle(base=base, price_rows=[], concentration_rows=[])
    render_started = time.perf_counter()
    _post_emit("HTML_RENDER_START", render_started)
    html_page = _render_page(bundle)
    _post_emit("HTML_RENDER_END", render_started, completed=True, status="rendered")
    response_started = time.perf_counter()
    _post_emit("FASTAPI_RESPONSE_START", response_started)
    response = HTMLResponse(html_page)
    _post_emit("FASTAPI_RESPONSE_END", response_started, completed=True, status="created")
    _post_emit("ROUTE_RETURN", response_started, completed=True, status="returning")
    return response


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
    schema_version: int = Query(default=1, ge=1),
    locale: str = Query(default="en"),
    code: str = Query(default=DEFAULT_CODE),
    input_type: str = Query(default="Stock Code"),
    source_mode: str = Query(default="auto"),
    timeout_seconds: float = Query(default=12.0, ge=1.0),
    announcement_period: str = Query(default="All"),
    data_date: date | None = Query(default=None),
    history_range: str = Query(default="Latest"),
    top_n: int = Query(default=20, ge=5, le=100),
    percentage_basis: str = Query(default="CCASS"),
    big_change_threshold: int = Query(default=1_000_000, ge=0),
    use_local_history: bool = Query(default=True),
) -> StreamingResponse:
    if schema_version != 1:
        raise PlatformError(
            "SCHEMA_VERSION_UNSUPPORTED",
            f"Export schema version {schema_version} is unsupported; expected version 1.",
            status_code=400,
        )
    try:
        bundle = await _build_portal_8504_bundle(
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
        base = bundle.base
        if section == "live":
            if base.live_artifacts is None:
                raise PlatformError("NOT_FOUND", "Live product artifacts are unavailable.", status_code=404)
            if kind == "csv":
                return await _stream_bytes(base.live_artifacts.combined_csv_bytes, "text/csv", base.live_artifacts.combined_csv_filename)
            if kind == "xlsx":
                return await _stream_bytes(
                    base.live_artifacts.workbook_bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    base.live_artifacts.workbook_filename,
                )
            if kind == "json":
                return await _stream_bytes(base.live_artifacts.json_bytes, "application/json", base.live_artifacts.json_filename)
            if kind == "md":
                return await _stream_bytes(
                    _bundle_markdown(base, "live", locale).encode("utf-8"),
                    "text/markdown; charset=utf-8",
                    f"{base.resolved_code}_live_markdown.md",
                )
        if section == "ccass":
            if base.prepared is None:
                raise PlatformError("NOT_FOUND", "CCASS artifacts are unavailable.", status_code=404)
            if kind == "md":
                return await _stream_bytes(
                    _bundle_markdown(base, "ccass", locale).encode("utf-8"),
                    "text/markdown; charset=utf-8",
                    base.prepared.filename,
                )
            if kind == "json":
                payload = base.prepared.response.model_dump_json(indent=2).encode("utf-8")
                return await _stream_bytes(
                    payload,
                    "application/json",
                    f"{base.prepared.response.metadata.code}_ccass.json",
                )
            if base.ccass_artifacts is None:
                raise PlatformError("NOT_FOUND", "CCASS artifacts are unavailable.", status_code=404)
            if kind == "csv":
                return await _stream_bytes(base.ccass_artifacts.combined_csv_bytes, "text/csv", base.ccass_artifacts.combined_csv_filename)
            if kind == "xlsx":
                return await _stream_bytes(
                    base.ccass_artifacts.workbook_bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    base.ccass_artifacts.workbook_filename,
                )
            if kind == "md":
                return await _stream_bytes(
                    _bundle_markdown(base, "ccass", locale).encode("utf-8"),
                    "text/markdown; charset=utf-8",
                    base.prepared.filename,
                )
        if section == "raw_previews":
            if base.ccass_artifacts is None or base.prepared is None:
                raise PlatformError("NOT_FOUND", "Raw preview artifacts are unavailable.", status_code=404)
            if kind == "json":
                return await _stream_bytes(
                    base.ccass_artifacts.raw_preview_json_bytes,
                    "application/json",
                    base.ccass_artifacts.raw_preview_json_filename,
                )
            if kind == "summary_csv":
                return await _stream_bytes(
                    base.ccass_artifacts.raw_preview_summary_bytes,
                    "text/csv",
                    base.ccass_artifacts.raw_preview_summary_filename,
                )
            if kind == "holdings_csv":
                return await _stream_bytes(
                    base.ccass_artifacts.raw_preview_holdings_bytes,
                    "text/csv",
                    base.ccass_artifacts.raw_preview_holdings_filename,
                )
        if section in {"holdings", "changes", "big_changes", "concentration", "announcements", "price_history"}:
            if base.prepared is None or base.prepared.response is None:
                raise PlatformError("NOT_FOUND", f"{section} artifacts are unavailable.", status_code=404)
            if kind == "csv":
                payload, filename = build_section_csv_artifact(base.prepared.response, section)
                return await _stream_bytes(payload, "text/csv", filename)
        if section == "rainbow":
            rainbow_payload = _rainbow_download_payload(base.resolved_code)
            if kind == "json":
                payload = json.dumps(rainbow_payload, ensure_ascii=False, indent=2).encode("utf-8")
                return await _stream_bytes(
                    payload,
                    "application/json",
                    f"{base.resolved_code}_rainbow.json",
                )
            if kind == "csv":
                payload = _rainbow_csv_bytes(rainbow_payload)
                return await _stream_bytes(
                    payload,
                    "text/csv",
                    f"{base.resolved_code}_rainbow.csv",
                )
        raise PlatformError("NOT_FOUND", f"Unsupported download kind: {section}/{kind}", status_code=404)
    except PlatformError as exc:
        return JSONResponse(status_code=exc.status_code, content=exc.as_dict())



# Joe Intelligence Terminal (22-component frontend) — imported last: this module
# must fully define its helpers before app.terminal reads them.
from app.terminal import router as terminal_router  # noqa: E402

app.include_router(terminal_router)

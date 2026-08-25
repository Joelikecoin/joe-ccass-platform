from __future__ import annotations

import asyncio
import html
import json
import math
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, StreamingResponse

from app.config import get_settings
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
from app.services.ccass import get_ccass_service
from app.storage.history import NormalizedSnapshotRepository
from app.streamlit_ui import (
    build_download_artifacts,
    build_raw_preview_tables,
    prepare_report,
    render_prepared_report,
    resolve_streamlit_query_input,
)
from ccass_core.collector import SnapshotStore


APP_TITLE_EN = "Joe Visual Portal"
APP_TITLE_ZH = "Joe Visual Portal"
APP_SUBTITLE_EN = "Golden Joe reference portal for live market news and CCASS holdings."
APP_SUBTITLE_ZH = "Golden Joe 參考入口：即時市場資訊與 CCASS 持股。"

DEFAULT_PORTAL_CODE = "00700"
PRICE_HISTORY_LOAD_TIMEOUT_SECONDS = 5.0
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
        for row in windows[default_range][-12:]
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
                        for row in pane_rows[-12:]
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
          <div class="source-note">Stored CCASS snapshots in SQLite | latest data_as_of: {_svg_escape(latest["snapshot_date"])}</div>
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
    cards = [
        _metric_card("Portal", "入口", APP_TITLE_EN, tone="primary"),
        _metric_card("CCASS Source", "CCASS 來源", "HKEX SDW" if prepared and prepared.response else "Unavailable", tone="success"),
        _metric_card("Price Source", "價格來源", price_source_name, tone="accent"),
        _metric_card("Announcement Source", "公告來源", "HKEX News", tone="muted"),
        _metric_card("Snapshot History", "快照歷史", _format_int(snapshot_count), tone="secondary"),
        _metric_card("Last CCASS Date", "最近 CCASS 日期", _format_date(ccass_date), tone="secondary"),
        _metric_card("Last Price Date", "最近價格日期", _svg_escape(price_date or "—"), tone="secondary"),
        _metric_card("Source Mode", "來源模式", source_mode, tone="secondary"),
    ]
    notes: list[str] = []
    if result and result.source_notes:
        notes.extend(result.source_notes)
    if prepared and prepared.response and prepared.response.data_quality_warnings:
        notes.extend(prepared.response.data_quality_warnings)
    notes_html = ""
    if notes:
        notes_html = "<div class='warning-box'>" + _escape("\n".join(dict.fromkeys(notes))) + "</div>"
    return f"""
    <section id="overview" class="panel">
      <div class="kicker">AI-ready overview</div>
      <h2>Fetch summary</h2>
      <div class="metric-grid">{''.join(cards)}</div>
      {notes_html}
    </section>
    """


def _build_query_payload(bundle: PortalBundle) -> dict[str, object]:
    return {
        "code": bundle.resolved_code,
        "input_type": bundle.input_type,
        "source_mode": bundle.source_mode,
        "top_n": bundle.top_n,
        "big_change_threshold": bundle.big_change_threshold,
        "use_local_history": "true" if bundle.use_local_history else "false",
    }


@dataclass(slots=True)
class Portal8504Bundle:
    base: PortalBundle
    price_rows: list[dict[str, object]]
    concentration_rows: list[dict[str, object]]


async def _build_portal_8504_bundle(
    *,
    raw_code: str,
    input_type: str,
    source_mode: str,
    top_n: int,
    big_change_threshold: int,
    use_local_history: bool,
) -> Portal8504Bundle:
    base = await _build_bundle(
        raw_code=raw_code,
        input_type=input_type,
        source_mode=source_mode,
        top_n=top_n,
        big_change_threshold=big_change_threshold,
        use_local_history=use_local_history,
    )
    price_rows: list[dict[str, object]] = []
    if base.live_product is not None:
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
    concentration_rows = _concentration_history_rows(base)
    for row in concentration_rows:
        snapshot = row.get("snapshot")
        if isinstance(snapshot, HistoricalSnapshot):
            row["snapshot"] = snapshot
    return Portal8504Bundle(base=base, price_rows=price_rows, concentration_rows=concentration_rows)


def _render_page(bundle: Portal8504Bundle) -> str:
    base = bundle.base
    price_rows = bundle.price_rows
    concentration_rows = bundle.concentration_rows
    locale = "en"
    status_text = "LIVE CCASS + bilingual portal"
    if base.error_message:
        status_text = base.error_message
    live_status = "READY" if base.live_product and base.prepared and base.prepared.response is not None else "PARTIAL"
    current_query = json.dumps(_build_query_payload(base))
    ccass_warning_html = ""
    if base.prepared and base.prepared.response and base.prepared.response.data_quality_warnings:
        ccass_warning_html = (
            "<div class='warning-box'>"
            + _escape("\n".join(base.prepared.response.data_quality_warnings))
            + "</div>"
        )
    live_notes_html = ""
    if base.live_product and base.live_product.source_notes:
        live_notes_html = (
            "<div class='warning-box'>"
            + _escape("\n".join(base.live_product.source_notes))
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
        <form method="get" action="/">
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
          <div class="field">
            <label>{_i18n("Source mode", "來源模式", locale)}</label>
            <select name="source_mode">
              <option value="auto"{" selected" if base.source_mode == "auto" else ""}>{_i18n("Auto", "自動", locale)}</option>
              <option value="webbsite"{" selected" if base.source_mode == "webbsite" else ""}>{_i18n("Webb-site", "Webb-site", locale)}</option>
              <option value="google_drive_csv"{" selected" if base.source_mode == "google_drive_csv" else ""}>{_i18n("Google Drive CSV", "Google Drive CSV", locale)}</option>
            </select>
          </div>
          <button class="primary-btn" type="submit">{_i18n("Fetch", "擷取", locale)}</button>
          <details class="advanced">
            <summary>{_i18n("Advanced settings", "進階設定", locale)}</summary>
            <div style="margin-top:0.75rem;">
              <div class="field">
                <label>{_i18n("Top N holdings", "顯示前 N 筆持股", locale)}</label>
                <input name="top_n" type="number" min="5" max="100" step="5" value="{base.top_n}" />
              </div>
              <div class="field">
                <label>{_i18n("Big change threshold", "大變動門檻", locale)}</label>
                <input name="big_change_threshold" type="number" min="0" step="100000" value="{base.big_change_threshold}" />
              </div>
              <div class="field">
                <label>
                  <input type="checkbox" name="use_local_history" value="true"{" checked" if base.use_local_history else ""} />
                  {_i18n("Use local history", "使用本機歷史", locale)}
                </label>
              </div>
            </div>
          </details>
        </form>
        <div style="margin-top:1rem;">
          <div class="kicker">{_i18n("Current selection", "目前選項", locale)}</div>
          <div style="display:flex; flex-wrap:wrap; gap:0.45rem;">
            {_pill(base.resolved_code, "primary")}
            {_pill(base.source_mode, "accent")}
            {_pill(base.input_type, "neutral")}
          </div>
        </div>
      </aside>
      <main class="main">
        <section class="hero">
          <div class="hero-grid">
            {_metric_card("Resolved code", "已解析代號", base.resolved_code, note="Input accepted and normalized.", tone="primary")}
            {_metric_card("Live CCASS", "即時 CCASS", "YES" if base.live_product and base.prepared and base.prepared.response is not None else "NO", note="HKEX SDW browser acquisition enabled.", tone="success")}
            {_metric_card("Chinese HKEX titles", "HKEX 中文標題", "YES" if base.live_product and base.live_product.announcements else "NO", note="Official title search language set to Chinese.", tone="accent")}
            {_metric_card("Holdings rows", "持股列數", _format_int(len(base.prepared.response.holdings) if base.prepared and base.prepared.response else None), note="Top rows shown in the portal.", tone="muted")}
            {_metric_card("Previous history", "歷史比較", "YES" if base.previous_available else "NO", note="Local snapshot comparison when available.", tone="secondary")}
          </div>
        </section>

      <nav class="section-nav">
        <a href="#overview">{_i18n("Fetch Summary", "擷取摘要", locale)}</a>
        <a href="#live-market">Live Market &amp; News</a>
        <a href="#ccass-holdings">{_i18n("CCASS Holdings", "CCASS 持股", locale)}</a>
        <a href="#changes">{_i18n("Changes", "變動", locale)}</a>
        <a href="#big-changes">{_i18n("Big Changes", "大變動", locale)}</a>
        <a href="#concentration">{_i18n("Concentration", "集中度", locale)}</a>
        <a href="#raw-previews">{_i18n("Raw Previews", "原始預覽", locale)}</a>
        <a href="#downloads">{_i18n("Downloads", "下載", locale)}</a>
        <a href="#copy">{_i18n("Copy for ChatGPT / Report", "複製給 ChatGPT／報告", locale)}</a>
      </nav>

      {_overview_block(base, price_rows, concentration_rows)}

      <section id="live-market" class="panel">
        <div class="kicker">{_i18n("Live market data", "即時市場資料", locale)}</div>
        <h2>{_i18n("Live Market & News", "即時市場與公告", locale)}</h2>
        {_company_block(base)}
        {_price_panel(base, price_rows)}
        <div class="two-col">
          {_announcement_block("HKEX Announcements", "HKEX 公告", base.live_product.announcements if base.live_product else [], locale, empty_text="No announcement rows available.")}
          {_announcement_block("Corporate Events", "公司事件", base.live_product.corporate_events if base.live_product else [], locale, empty_text="No corporate event rows available.")}
        </div>
        <div class="two-col">
          {_announcement_block("Share Capital Changes", "股本變動", base.live_product.share_capital_changes if base.live_product else [], locale, empty_text="No share capital change rows available.")}
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
                ] for row in (base.live_product.officers[:12] if base.live_product else [])
            ], class_name="compact-table")}
          </div>
        </div>
        {live_error_html}
        {live_notes_html}
      </section>

      <section id="ccass-holdings" class="panel">
        <div class="kicker">{_i18n("CCASS / holdings", "CCASS／持股", locale)}</div>
        <h2>{_i18n("CCASS Holdings", "CCASS 持股", locale)}</h2>
        {_ccass_summary(base, locale)}
        <div style="margin-top:.85rem;">{_holdings_table(base)}</div>
      </section>

      <section id="changes" class="panel">
        <div class="kicker">{_i18n("Historical comparison", "歷史比較", locale)}</div>
        <h2>{_i18n("Changes", "變動", locale)}</h2>
        {_changes_block(base, locale)}
      </section>

      <section id="big-changes" class="panel">
        <div class="kicker">{_i18n("Threshold filtered", "門檻過濾", locale)}</div>
        <h2>{_i18n("Big Changes", "大變動", locale)}</h2>
        {_big_changes_block(base)}
      </section>

      <section id="concentration" class="panel">
        <div class="kicker">{_i18n("Distribution view", "分布視圖", locale)}</div>
        <h2>{_i18n("Concentration", "集中度", locale)}</h2>
        {_concentration_panel(base, concentration_rows)}
      </section>

      <section id="dt-rainbow" class="panel">
        <div class="kicker">{_i18n("Historical view", "歷史視圖", locale)}</div>
        <h2>{_i18n("DT Rainbow", "DT Rainbow", locale)}</h2>
        {_dt_rainbow_panel(base, concentration_rows)}
      </section>

      <section id="raw-previews" class="panel">
        <div class="kicker">{_i18n("Structured source audit", "結構化來源檢視", locale)}</div>
        <h2>{_i18n("Raw Previews", "原始預覽", locale)}</h2>
        {_raw_preview_block(base, locale)}
      </section>

      <section id="downloads" class="panel">
        <div class="kicker">{_i18n("Export", "匯出", locale)}</div>
        <h2>{_i18n("Downloads", "下載", locale)}</h2>
        <div class="section-footer">{_download_links(base)}</div>
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "joe-ccass-visual-portal-8504"}


@app.get("/", response_class=HTMLResponse)
async def portal(
    code: str = Query(default=""),
    input_type: str = Query(default="Stock Code"),
    source_mode: str = Query(default="auto"),
    top_n: int = Query(default=20, ge=5, le=100),
    big_change_threshold: int = Query(default=1_000_000, ge=0),
    use_local_history: bool = Query(default=True),
) -> HTMLResponse:
    if code.strip():
        try:
            bundle = await _build_portal_8504_bundle(
                raw_code=code,
                input_type=input_type,
                source_mode=source_mode,
                top_n=top_n,
                big_change_threshold=big_change_threshold,
                use_local_history=use_local_history,
            )
        except PlatformError as exc:
            base = PortalBundle(
                requested_code=code,
                resolved_code=code,
                input_type=input_type,
                source_mode=source_mode,
                top_n=top_n,
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
            top_n=top_n,
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
    top_n: int = Query(default=20, ge=5, le=100),
    big_change_threshold: int = Query(default=1_000_000, ge=0),
    use_local_history: bool = Query(default=True),
) -> StreamingResponse:
    bundle = await _build_portal_8504_bundle(
        raw_code=code,
        input_type=input_type,
        source_mode=source_mode,
        top_n=top_n,
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
        if base.ccass_artifacts is None or base.prepared is None:
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
    raise PlatformError("NOT_FOUND", f"Unsupported download kind: {section}/{kind}", status_code=404)

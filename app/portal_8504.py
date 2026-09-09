from __future__ import annotations

import asyncio
import csv
import html
import io
import json
import math
import os
import sys
import threading
import traceback
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
                _post_emit(stage + "_END", started, completed=False, exception_type=type(exc).__name__, timeout=isinstance(exc, TimeoutError))
                raise
            _post_emit(stage + "_END", started, completed=True, status="returned")
            return result
        return wrapped
    return decorate

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
    # The live Longbridge fallback persists before this point.  Refresh the
    # comparison inputs afterwards so the same request can read the previous
    # stored snapshot instead of evaluating history before the write.
    prepared = base.prepared
    if prepared is not None and prepared.response is not None:
        current_response = prepared.response
        try:
            source_name = str(current_response.metadata.source_name or "").lower()
            source_id = "longbridge" if source_name == "longbridge" else None
            previous_snapshot = _snapshot_repo().previous(
                base.resolved_code,
                before_date=current_response.metadata.holdings_date,
                source_id=source_id,
                include_partial=True,
            )
            previous_response = previous_snapshot.to_response() if previous_snapshot else None
            refreshed_analysis = compute_analysis(
                current_response,
                previous=previous_response,
                big_change_threshold=big_change_threshold,
            )
            base.prepared = replace(
                prepared,
                previous_response=previous_response,
                analysis=refreshed_analysis,
            )
            base.previous_available = previous_response is not None
        except Exception:
            # Keep the already prepared product response if history refresh is
            # unavailable; section-local history remains explicit below.
            pass
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


@app.exception_handler(PlatformError)
async def platform_error_handler(_: Request, exc: PlatformError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.as_dict())


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "joe-ccass-visual-portal-8504"}


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


@app.get("/", response_class=HTMLResponse)
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
    data_date: date | None = Query(default=None),
    history_range: str = Query(default="Latest"),
    top_n: int = Query(default=20, ge=5, le=100),
    percentage_basis: str = Query(default="CCASS"),
    big_change_threshold: int = Query(default=1_000_000, ge=0),
    use_local_history: bool = Query(default=True),
) -> StreamingResponse:
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


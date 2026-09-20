"""Joe Intelligence Terminal — the unlimited-creation frontend (22 components).

Single persisted-read page: every component renders from the Turso evidence
cache in parallel; deep refreshes stay behind the admin job panel. The data
layer is untouched — this module only reads.
"""
from __future__ import annotations

import asyncio
import html as _html
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from app.portal_8504 import (
    _JOB_PANEL_SCRIPT,
    get_announcements_service,
    get_intelligence_events_service,
    get_ownership_timeline_service,
    get_research_context_service,
)

router = APIRouter()

THIRTY_DAYS = timedelta(days=90)

_FAST_LANDING = """<!DOCTYPE html><html lang="zh-HK"><head><meta charset="utf-8"><title>Joe Intelligence Terminal</title>
<style>body{margin:0;background:#eef2f7;color:#1e293b;font-family:-apple-system,'Segoe UI','Microsoft JhengHei',sans-serif;display:flex;min-height:100vh;align-items:center;justify-content:center}
.panel{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:40px 48px;text-align:center}
h1{margin:0 0 6px;font-size:26px;color:#1e3a8a}
input{width:200px;border:1px solid #cbd5e1;border-radius:6px;padding:10px 12px;font-size:15px}
button{background:#1d4ed8;color:#fff;border:none;border-radius:6px;padding:10px 20px;font-size:15px;font-weight:600;cursor:pointer;margin-left:8px}
p{color:#64748b;font-size:13px}</style></head><body>
<div class="panel"><h1>Joe Intelligence Terminal</h1>
<p>22 個部件 · persisted 證據快取唯讀</p>
<form method="get" action="/terminal"><input name="code" placeholder="輸入股票代號 e.g. 02318"><button>載入終端</button></form>
</div></body></html>"""


def esc(value) -> str:
    from app.portal_8504 import _escape

    return _escape(str(value))


def _fmt_shares(value) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "—"


def _card(title: str, body: str, *, open_: bool = True, wide: bool = False, note: str = "") -> str:
    open_attr = " open" if open_ else ""
    wide_cls = " wide" if wide else ""
    note_html = "<p class='note'>" + esc(note) + "</p>" if note else ""
    sumnote = "<span class='sumnote'>" + esc(note) + "</span>" if note else ""
    return (
        "<details class='card" + wide_cls + "'" + open_attr + ">"
        + "<summary>" + esc(title) + sumnote + "</summary>"
        + "<div class='cardbody'>" + body + note_html + "</div></details>"
    )


def _table(headers: list[str], rows: list[str], cls: str = "") -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(f"<tr>{r}</tr>" for r in rows) or "<tr><td colspan='9' class='empty'>暫無數據</td></tr>"
    return f"<table class='{cls}'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _warn(title: str, message: str) -> str:
    return _card(title, f"<div class='warnbox'>{esc(message)}</div>")


def _bar(pct: float, color: str = "#1d4ed8") -> str:
    pct = max(0.0, min(100.0, pct))
    return (
        f"<div class='bartrack'><div class='barfill' style='width:{pct:.2f}%;background:{color}'></div>"
        f"<span class='barlabel'>{pct:.2f}%</span></div>"
    )


def _sparkline(points: list[float], color: str = "#1d4ed8") -> str:
    if len(points) < 2:
        return "<span class='empty'>數據不足</span>"
    lo, hi = min(points), max(points)
    span = (hi - lo) or 1.0
    w, h = 220, 44
    step = w / (len(points) - 1)
    coords = " ".join(f"{i * step:.1f},{h - (p - lo) / span * (h - 6) - 3:.1f}" for i, p in enumerate(points))
    last_x, last_y = (len(points) - 1) * step, h - (points[-1] - lo) / span * (h - 6) - 3
    return (
        f"<svg width='{w}' height='{h}' class='spark'><polyline fill='none' stroke='{color}' stroke-width='2' points='{coords}'/>"
        f"<circle cx='{last_x:.1f}' cy='{last_y:.1f}' r='3' fill='{color}'/></svg>"
    )


async def _build_components(normalized: str, start: date, end: date):
    svc = get_research_context_service()
    events_repo = get_intelligence_events_service().event_repository
    now = datetime.now(UTC)

    async def _safe(coro):
        try:
            return await coro
        except Exception as exc:  # fail loud per component
            return exc

    snapshot_repo = svc.snapshot_repository

    async def _concentration_series(code: str, points: int = 14):
        """Walk persisted snapshots backwards for a Top5 concentration series."""
        series: list[tuple[date, float]] = []
        snap = snapshot_repo.latest(code)
        while snap is not None and len(series) < points:
            holdings = sorted(snap.holdings, key=lambda h: h.shares, reverse=True)
            total = sum(h.shares for h in holdings) or 1
            top5 = sum(h.shares for h in holdings[:5]) / total * 100
            series.append((snap.snapshot_date, top5))
            snap = snapshot_repo.previous(code, before_date=snap.snapshot_date)
        series.reverse()
        return series

    components = await asyncio.gather(
        _safe(asyncio.to_thread(snapshot_repo.latest, normalized)),
        _safe(asyncio.to_thread(snapshot_repo.available_dates, normalized, True)),
        _safe(get_ownership_timeline_service().get_timeline(normalized, start_date=start, end_date=end)),
        _safe(asyncio.to_thread(events_repo.load, normalized)),
        _safe(asyncio.to_thread(svc.fundamentals_repository.load, normalized)),
        _safe(asyncio.to_thread(svc.entity_repository.load_rows, normalized, start_date=start, end_date=end)),
        _safe(asyncio.to_thread(svc.share_capital_repository.load, normalized, start_date=start, end_date=end)),
        _safe(asyncio.to_thread(get_announcements_service().repository.load, normalized, start_date=start, end_date=end)),
        _safe(_concentration_series(normalized)),
    )
    return components, now


@router.get("/terminal", response_class=HTMLResponse)
async def terminal(
    code: str = Query(default=""),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> HTMLResponse:
    normalized = (code or "").strip()
    from ccass_core.normalize import normalize_stock_code

    normalized = normalize_stock_code(normalized) if normalized else ""
    if not normalized:
        return HTMLResponse(_FAST_LANDING)
    now = datetime.now(UTC)
    end = end_date or now.date()
    start = start_date or end - timedelta(days=365 * 5)
    svc = get_research_context_service()

    results, _ = await _build_components(normalized, start, end)
    snapshot, dates, timeline, events, fundamentals, entities, share_capital, announcements, conc_series = results
    timeline = timeline if not isinstance(timeline, Exception) else None
    events = events if not isinstance(events, Exception) else None
    fundamentals = fundamentals if not isinstance(fundamentals, Exception) else None
    announcements = announcements if not isinstance(announcements, Exception) else None
    entities = entities if not isinstance(entities, Exception) else []
    share_capital = share_capital if not isinstance(share_capital, Exception) else None
    snapshot = snapshot if not isinstance(snapshot, Exception) else None
    conc_series = conc_series if not isinstance(conc_series, Exception) else []
    dates = dates if not isinstance(dates, Exception) else []

    cards: list[str] = []
    kpis: list[tuple[str, str, str]] = []  # label, value, sub

    # ---- 1. KPI strip ----
    holdings = sorted(snapshot.holdings, key=lambda h: h.shares, reverse=True) if snapshot else []
    total = sum(h.shares for h in holdings) or 1
    top5 = sum(h.shares for h in holdings[:5]) / total * 100 if holdings else 0
    kpis = [
        ("CCASS 快照", str(snapshot.snapshot_date) if snapshot else "—", f"{len(holdings):,} 參與者"),
        ("Top 5 佔 CCASS", f"{top5:.1f}%", "集中度"),
        ("申報人", str(len(timeline.timelines) if timeline else 0), "DION 官方申報"),
        ("情報事件", f"{len(events):,}" if events else "0", "官方+抽取"),
        ("業績期", str(len(fundamentals.rows) if fundamentals else 0), "已持久化"),
        ("覆蓋快照", str(len(dates)), "可回溯日期"),
    ]
    kpi_html = "".join(
        f"<div class='kpi'><div class='kpi-label'>{esc(l)}</div><div class='kpi-value'>{esc(v)}</div><div class='kpi-sub'>{esc(s)}</div></div>"
        for l, v, s in kpis
    )

    # ---- 2. Concentration trend (sparkline card) ----
    if conc_series:
        pts = [p for _, p in conc_series]
        first, last = conc_series[0], conc_series[-1]
        delta = last[1] - first[1]
        cards.append(
            _card(
                "② 集中度趨勢 Top 5",
                _sparkline(pts) + f"<p class='note'>{first[0]} {first[1]:.1f}% → {last[0]} {last[1]:.1f}%（<span class='{'up' if delta >= 0 else 'down'}'>{delta:+.1f}pp</span>）</p>",
                note=f"{len(conc_series)} 個持久化快照",
            )
        )
    else:
        cards.append(_warn("② 集中度趨勢 Top 5", "持久化快照不足兩個 — 每日累積後自動出現。"))

    # ---- 3. CCASS top holdings with bars ----
    if snapshot:
        rows = [
            f"<tr><td>{i + 1}</td><td>{esc(str(getattr(h, 'participant_name', None) or h.participant_id))[:32]}</td>"
            f"<td class='num'>{_fmt_shares(h.shares)}</td><td style='width:34%'>{_bar(h.shares / total * 100)}</td></tr>"
            for i, h in enumerate(holdings[:15])
        ]
        cards.append(
            _card("① CCASS Top 15 持倉", _table(["#", "Participant", "Shares", "佔 CCASS"], rows), note=f"快照 {snapshot.snapshot_date}")
        )
    else:
        cards.append(_warn("① CCASS Top 15 持倉", "無持久化快照。"))

    # ---- 4/5. Changes + Big changes derived from the two latest snapshots ----
    snapshot_repo = svc.snapshot_repository
    if snapshot:
        prev = snapshot_repo.previous(normalized, before_date=snapshot.snapshot_date)
        if prev is not None:
            prev_map = {h.participant_id: h.shares for h in prev.holdings}
            now_map = {h.participant_id: h.shares for h in holdings}
            changes: list[tuple[str, int, int, int]] = []
            for pid, now_shares in now_map.items():
                old = prev_map.get(pid)
                if old is None:
                    if now_shares > 0:
                        changes.append((pid, now_shares, now_shares, 1))
                else:
                    changes.append((pid, now_shares - old, now_shares, 0))
            for pid, old in prev_map.items():
                if pid not in now_map and old:
                    changes.append((pid, -old, 0, -1))
            changes.sort(key=lambda c: abs(c[1]), reverse=True)
            threshold = total * 0.005
            big = [c for c in changes if abs(c[1]) >= threshold]
            ch_rows = [
                f"<tr><td>{esc(pid)}</td><td class='num'>{_fmt_shares(now)}</td>"
                f"<td class='num'><span class='{'up' if ch > 0 else 'down' if ch < 0 else ''}'>{_fmt_shares(ch) if ch else '新' if kind == 1 else '清'}</span></td></tr>"
                for pid, ch, now, kind in changes[:12]
            ]
            cards.append(
                _card(
                    f"③ 持倉變動（{prev.snapshot_date} → {snapshot.snapshot_date}）",
                    _table(["Participant", "現持", "變化"], ch_rows),
                    note="由兩張持久化快照推算",
                )
            )
            big_rows = [
                f"<tr><td>{esc(pid)}</td><td class='num'><span class='{'up' if ch > 0 else 'down'}'>{_fmt_shares(ch)}</span></td>"
                f"<td class='num'>{_fmt_shares(now)}</td><td>{'新倉' if kind == 1 else '清倉' if kind == -1 else '—'}</td></tr>"
                for pid, ch, now, kind in big[:10]
            ]
            cards.append(
                _card(
                    "④ 大額變動（≥0.5% CCASS）",
                    _table(["Participant", "變化", "現持", "性質"], big_rows)
                    or _table(["Participant", "變化", "現持", "性質"], []),
                    note=f"門檻 {_fmt_shares(threshold)} 股",
                )
            )
        else:
            cards.append(_warn("③ 持倉變動 / ④ 大額變動", "只有一張持久化快照 — 多累積一日即出現。"))
    else:
        cards.append(_warn("③ 持倉變動 / ④ 大額變動", "無持久化快照。"))

    # ---- 6. CCASS metadata / coverage ----
    if dates:
        cards.append(
            _card(
                "⑨ 快照覆蓋",
                _sparkline([1] * min(len(dates), 30), "#94a3b8")
                + f"<p class='note'>{len(dates)} 個可回溯日期：{dates[0]} → {dates[-1]}</p>",
                open_=False,
            )
        )

    # ---- 10. Ownership timeline ----
    if timeline:
        rows = []
        for t in timeline.timelines[:12]:
            rows.append(
                f"<tr><td>{esc(t.filer)[:30]}</td><td class='num'>{t.movements_count}</td>"
                f"<td class='num'><span class='up'>+{t.increases}</span>/<span class='down'>−{t.decreases}</span></td>"
                f"<td class='num'>{t.latest_present_balance or '—'}</td><td class='num'>{t.latest_percentage if t.latest_percentage is not None else '—'}</td></tr>"
            )
        cards.append(
            _card(
                f"⑩ 大股東動向 · {len(timeline.timelines)} 名申報人",
                _table(["Filer", "申報", "增/減", "最新持倉", "%"], rows),
                note="官方 DION 鏈式推算",
            )
        )
    else:
        cards.append(_warn("⑩ 大股東動向", "無持久化 DION 申報。"))

    # ---- 11. DI highlights (top moves last 90 days) ----
    if timeline:
        moves: list[tuple[date, str, int, object]] = []
        for t in timeline.timelines:
            for m in t.movements:
                if m.change_shares and m.event_date >= end - THIRTY_DAYS:
                    moves.append((m.event_date, t.filer, m.change_shares, m))
        moves.sort(key=lambda x: abs(x[2]), reverse=True)
        rows = [
            f"<tr><td class='num'>{d}</td><td>{esc(f)[:26]}</td>"
            f"<td class='num'><span class='{'up' if ch > 0 else 'down'}'>{_fmt_shares(ch)}</span></td>"
            f"<td class='num'>{_fmt_shares(m.present_balance) if m.present_balance else '—'}</td></tr>"
            for d, f, ch, m in moves[:10]
        ]
        cards.append(
            _card("⑪ 近 90 日重點申報", _table(["日期", "Filer", "變化", "申報後持倉"], rows), note=f"共 {len(moves)} 次移動")
        )
    else:
        cards.append(_warn("⑪ 近 90 日重點申報", "無申報數據。"))

    # ---- 12. Intelligence events stream ----
    if events:
        by_type: dict[str, int] = {}
        for e in events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
        pills = "".join(f'<span class="pill">{esc(k)} <b>{v}</b></span>' for k, v in sorted(by_type.items()))
        ev_sorted = sorted(events, key=lambda e: e.announce_date, reverse=True)
        rows = [
            f"<tr><td class='num'>{e.announce_date}</td><td>{esc(e.event_type)}</td>"
            f"<td>{esc(str(e.counterparty or e.entity_name or ''))[:40]}</td>"
            f"<td><span class='badge {e.confidence}'>{e.confidence}</span></td></tr>"
            for e in ev_sorted[:25]
        ]
        cards.append(
            _card(f"⑫ 情報事件流 · {len(events):,} 項", f"<div class='pills'>{pills}</div>" + _table(["日期", "類型", "對手方", "信心"], rows), wide=True)
        )
    else:
        cards.append(_warn("⑫ 情報事件流", "無持久化事件快照 — 觸發 intelligence-events job。"))
    # ---- 港交所公告 (raw announcements table, friend-site parity) ----
    if announcements and announcements.announcements:
        ann_sorted = sorted(announcements.announcements, key=lambda a: a.announcement_date, reverse=True)
        ann_rows = [
            f"<tr><td class='num'>{a.announcement_date}</td><td>{esc(a.category or '—')[:18]}</td>"
            f"<td><a href='{esc(a.link or '#')}' target='_blank' rel='noopener'>{esc(a.title)[:80]}</a></td></tr>"
            for a in ann_sorted[:15]
        ]
        cards.append(
            _card(
                f"港交所公告 · {len(announcements.announcements)} 份（最新 15）",
                _table(["日期", "類別", "標題（點擊開 PDF）"], ann_rows),
                wide=True,
                note="persisted 快取 · 5 年窗口內全部可追溯原文",
            )
        )
    else:
        cards.append(_warn("港交所公告", "無持久化公告 — 觸發 announcements job（可帶 start_date/end_date 回填 5 年）。"))

    # ---- 13. Intermediary network ----
    by_entity: dict[str, int] = {}
    for row in entities:
        by_entity[row.entity_type] = by_entity.get(row.entity_type, 0) + 1
    pills = "".join(f'<span class="pill">{esc(k)} <b>{v}</b></span>' for k, v in sorted(by_entity.items())) or "<span class='pill'>暫無</span>"
    ent_rows = [
        f"<tr><td>{esc(r.announcement_date)}</td><td>{esc(r.entity_type)}</td><td>{esc(r.entity_name or '—')[:40]}</td></tr>"
        for r in entities[:10]
    ]
    cards.append(_card("⑬ 中介網絡", f"<div class='pills'>{pills}</div>" + _table(["日期", "角色", "機構"], ent_rows), open_=False))

    # ---- 14/15. Fundamentals + pressure signals ----
    if fundamentals and fundamentals.rows:
        rows = [
            f"<tr><td>{r.reporting_period}</td><td class='num'>{r.revenue or '—'}</td>"
            f"<td class='num'>{r.net_profit_loss or '—'}</td><td class='num'>{r.cash or '—'}</td>"
            f"<td class='num'>{r.debt or '—'}</td><td class='num'>{r.operating_cash_flow or '—'}</td>"
            f"<td><span class='badge {r.completeness_status}'>{r.completeness_status}</span></td></tr>"
            for r in fundamentals.rows[:8]
        ]
        cards.append(_card("⑭ 基本面（官方業績）", _table(["期間", "收入", "純利", "現金", "債務", "OCF", "完整度"], rows)))
        latest = next((r for r in fundamentals.rows if r.debt and r.equity), None)
        if latest:
            de = latest.debt / latest.equity if latest.equity else None
            signal = f"<div class='pills'><span class='pill'>債務/權益 <b>{de:.2f}</b></span>" if de else "<div class='pills'>"
            if latest.cash:
                signal += f"<span class='pill'>現金/債務 <b>{latest.cash / latest.debt:.2f}</b></span>" if latest.debt else signal
            signal += f"<span class='pill'>單位 <b>{fundamentals.rows[0].unit or 'raw'}</b></span><span class='pill'>已標註推算值</span></div>"
            cards.append(_card("⑮ 財務壓力訊號（推算）", signal, open_=False, note="衍生比率 — 僅供對照，非投資建議"))
    else:
        cards.append(_warn("⑭ 基本面 / ⑮ 壓力訊號", "無持久化業績 — 觸發 fundamentals job。"))

    # ---- 16. Company / next dates ----
    name = None
    if snapshot is not None:
        name = getattr(snapshot, "company_name", None) or getattr(snapshot, "name", None)
    cards.append(
        _card(
            "⑯ 公司與下一關鍵日",
            f"<p><b>名稱：</b>{esc(name or '—')}</p><p><b>未來關鍵日：</b>由業績/企業事件推斷 — 暫無已申報之未來日期（誠實標籤：需月報/AGM 文件支援）。</p>",
            open_=False,
        )
    )

    # ---- 17. Share capital + dilution ----
    if share_capital and share_capital.rows:
        base = share_capital.rows[-1].shares_million or 0
        latest_row = share_capital.rows[0]
        dilution = ""
        if base and latest_row.shares_million:
            pct = (latest_row.shares_million - base) / base * 100
            dilution = f"<p class='note'>窗口首尾：{base}M → {latest_row.shares_million}M（<span class='{'up' if pct >= 0 else 'down'}'>{pct:+.1f}%</span>）</p>"
        rows = [
            f"<tr><td class='num'>{r.announce_date}</td><td class='num'>{r.shares_million}M</td>"
            f"<td>{esc(str(r.reason or ''))[:46]}<br><span class='tag'>{esc('/'.join(r.reason_tags or []))}</span></td></tr>"
            for r in share_capital.rows[:12]
        ]
        cards.append(_card("⑰ 股本故事", _table(["公佈日", "股本", "原因 / 標籤"], rows) + dilution))
    else:
        cards.append(_warn("⑰ 股本故事", "無持久化股本行 — 觸發 share-capital job（分段窗）。"))

    # ---- 18. AI report draft (async fetch on expand) ----
    cards.append(
        _card(
            "⑱ AI 報告初稿",
            f"<button onclick='const d=this.closest(\".cardbody\");fetch(`/api/v1/stocks/{normalized}/report-draft`).then(r=>r.text()).then(t=>{{d.querySelector(\".draftbox\").textContent=t}})'>載入初稿</button>"
            "<pre class='draftbox'>點擊載入 — 20-30 頁骨架（事實+分析位）</pre>",
            open_=False,
            wide=True,
        )
    )

    # ---- 19-20. Research context + raw previews ----
    cards.append(
        _card(
            "⑲ 研究包下載（AI 用）",
            f"<div class='pills'><a class='pill' href='/api/v1/stocks/{normalized}/research-context?format=json'>研究包 JSON</a>"
            f"<a class='pill' href='/api/v1/stocks/{normalized}/research-context?format=markdown'>研究包 Markdown</a>"
            f"<a class='pill' href='/api/v1/stocks/{normalized}/report-draft'>報告初稿 MD</a>"
            f"<a class='pill' href='/api/v1/stocks/{normalized}/intelligence-events'>事件全量 JSON</a>"
            f"<a class='pill' href='/api/v1/intermediary-graph?start_date={start}&end_date={end}'>中介圖譜 JSON</a></div>",
            open_=False,
        )
    )
    cards.append(
        _card(
            "⑳ 原始預覽",
            f"<div class='pills'><a class='pill' href='/full?code={normalized}'>完整 /full 產品（原始預覽+全表）</a>"
            f"<a class='pill' href='/console?code={normalized}'>Console</a></div>",
            open_=False,
        )
    )

    # ---- 21. Provenance & coverage ----
    cards.append(
        _card(
            "㉑ 溯源與覆蓋聲明",
            "<div class='pills'><span class='pill'>official = 官方申報原行</span><span class='pill'>extracted = 官方文件抽取</span>"
            "<span class='pill'>缺口 2025-12-25→2026-07-21 = DEFERRED（私人途徑待導入）</span></div>"
            "<p class='note'>缺失=缺失，永不插值；每項事實帶 source_document / source_url。</p>",
            open_=False,
        )
    )

    # ---- 22. Downloads hub ----
    cards.append(
        _card(
            "㉒ 下載中心",
            "<div class='pills'>"
            f"<a class='pill' href='/download/holdings/csv?code={normalized}'>Holdings CSV</a>"
            f"<a class='pill' href='/download/changes/csv?code={normalized}'>Changes CSV</a>"
            f"<a class='pill' href='/download/big_changes/csv?code={normalized}'>Big Changes CSV</a>"
            f"<a class='pill' href='/download/concentration/csv?code={normalized}'>Concentration CSV</a>"
            f"<a class='pill' href='/download/announcements/csv?code={normalized}'>Announcements CSV</a>"
            f"<a class='pill' href='/download/price_history/csv?code={normalized}'>Price CSV</a>"
            "</div>",
            open_=False,
        )
    )

    import re as _re
    cells = "".join(f"<div class='cell' id='sec{i}'>{c}</div>" for i, c in enumerate(cards))
    titles = []
    for c in cards:
        m = _re.search(r"<summary>(.*?)(<span class='sumnote'>|</summary>)", c)
        titles.append(_re.sub(r"<[^>]+>", "", m.group(0)).replace("<span class='sumnote'>", "").strip() if m else f"部件 {len(titles)+1}")
    jumps = "".join(f"<a href='#sec{i}'>{esc(t[:16])}</a> " for i, t in enumerate(titles))
    numbered = cells
    kpi_html_final = kpi_html
    job_panel = (
        "<h2>Deep Refresh <span class='h2note'>admin key — job 完成後重載此頁</span></h2>"
        + _JOB_PANEL_SCRIPT.replace("__CODE__", normalized)
        .replace("__START5Y__", (end - timedelta(days=365 * 5)).isoformat())
        .replace("__END__", end.isoformat())
    )
    page = f"""<!DOCTYPE html><html lang="zh-HK"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{normalized} · Intelligence Terminal</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#eef2f7;color:#1e293b;font-family:-apple-system,'Segoe UI','Microsoft JhengHei','PingFang TC',sans-serif}}
.wrap{{max-width:1360px;margin:0 auto;padding:20px 24px 48px}}
header.top{{background:linear-gradient(120deg,#0f2557,#1d4ed8 70%,#2563eb);color:#fff;border-radius:14px;padding:24px 28px;margin-bottom:16px;box-shadow:0 6px 18px rgba(29,78,216,.18)}}
header.top h1{{margin:0;font-size:26px;font-weight:800}}
header.top .sub{{font-size:12.5px;opacity:.85;margin-top:5px}}
header.top form{{margin-top:14px;display:flex;gap:8px}}
header.top input{{border:none;border-radius:7px;padding:9px 12px;font-size:14px;width:170px}}
header.top button{{background:#fff;color:#1d4ed8;border:none;border-radius:7px;padding:9px 18px;font-weight:700;cursor:pointer}}
nav.links{{margin:0 0 14px;font-size:13px}}
nav.links a{{color:#1d4ed8;text-decoration:none;margin-right:16px;font-weight:600}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:12px;margin-bottom:16px}}
.kpi{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:13px 16px;box-shadow:0 1px 3px rgba(15,23,42,.05)}}
.kpi-label{{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.5px}}
.kpi-value{{font-size:23px;font-weight:800;color:#0f172a;margin-top:3px;font-variant-numeric:tabular-nums}}
.kpi-sub{{font-size:11px;color:#94a3b8;margin-top:2px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:16px}}
.cell{{scroll-margin-top:14px}}
.jumps{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:10px 14px;margin-bottom:14px;font-size:12px;line-height:2}}
.jumps a{{color:#1d4ed8;text-decoration:none;margin-right:10px;font-weight:600}}
.card{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;box-shadow:0 1px 3px rgba(15,23,42,.05)}}
.card.wide{{grid-column:1/-1}}
.card summary{{cursor:pointer;padding:13px 18px;font-weight:700;font-size:14px;color:#0f172a;border-bottom:1px solid #eef2f7;list-style:none}}
.card summary::before{{content:'▸ ';color:#94a3b8}}
.card[open] summary::before{{content:'▾ '}}
.sumnote{{font-size:11px;color:#94a3b8;font-weight:400;margin-left:8px}}
.cardbody{{padding:10px 18px 16px}}
table{{width:100%;border-collapse:collapse;font-size:12.8px}}
th{{text-align:left;color:#64748b;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.4px;border-bottom:2px solid #e2e8f0;padding:6px 8px}}
td{{border-bottom:1px solid #f1f5f9;padding:6px 8px;vertical-align:top}}
tbody tr:hover{{background:#f8fafc}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.up{{color:#16a34a;font-weight:700}}
.down{{color:#dc2626;font-weight:700}}
.bartrack{{position:relative;background:#eef2f7;border-radius:999px;height:14px;min-width:120px}}
.barfill{{height:14px;border-radius:999px}}
.barlabel{{position:absolute;right:8px;top:-1px;font-size:11px;color:#334155;font-weight:600}}
.pill{{display:inline-block;background:#eff6ff;color:#1d4ed8;padding:3px 10px;margin:3px 4px 3px 0;border-radius:999px;font-size:12px;text-decoration:none}}
.pill b{{font-weight:800}}
.badge{{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11px;font-weight:600}}
.badge.official{{background:#dbeafe;color:#1e40af}}.badge.extracted{{background:#f1f5f9;color:#475569}}
.badge.partial{{background:#fef3c7;color:#92400e}}.badge.complete{{background:#dcfce7;color:#166534}}
.warnbox{{background:#fef3c7;color:#92400e;border-radius:8px;padding:10px 14px;font-size:13px}}
.note{{color:#64748b;font-size:12px;margin:8px 0 0}}
.tag{{color:#94a3b8;font-size:11px}}
.empty{{color:#94a3b8}}
.spark{{display:block;margin:4px 0}}
.draftbox{{max-height:420px;overflow:auto;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;font-size:12px;white-space:pre-wrap}}
h2{{font-size:15px}}.h2note{{font-size:12px;color:#64748b;font-weight:400}}
.card button{{background:#1d4ed8;color:#fff;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12.5px;font-weight:600}}
#adminkey{{border:1px solid #cbd5e1;border-radius:6px;padding:6px 10px;font-size:13px;width:280px}}
</style></head><body><div class="wrap">
<header class="top"><h1>{normalized} · Intelligence Terminal</h1><div class="sub">22 個部件 · persisted 證據快取唯讀 · 窗口 {start} → {end} · 後端數據源不變 · 缺口 2025-12-25→2026-07-21 已標籤</div>
<form method="get" action="/terminal"><input name="code" value="{esc(normalized)}" placeholder="輸入股票代號"><button>切換</button></form></header>
<nav class="links"><a href="/?code={normalized}">快總覽</a><a href="/full?code={normalized}">完整即時產品</a><a href="/console?code={normalized}">Console</a><a href="/api/v1/stocks/{normalized}/research-context?format=markdown">研究包 MD</a><a href="/api/v1/stocks/{normalized}/report-draft">報告初稿</a></nav>
<div class="kpis">{kpi_html_final}</div>
<div class="jumps">{jumps}</div>
<div class="grid">{numbered}</div>
{job_panel}
</div></body></html>"""
    return HTMLResponse(page)



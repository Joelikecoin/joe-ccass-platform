from __future__ import annotations

import asyncio
import json
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from app.portal_8504 import (
    get_announcements_service,
    get_intelligence_events_service,
    get_ownership_timeline_service,
    get_research_context_service,
)

router = APIRouter()

_FAST_LANDING = """<!DOCTYPE html><html lang="zh-HK"><head><meta charset="utf-8"><title>Joe Intelligence Terminal</title>
<style>body{margin:0;background:#eef2f7;color:#1e293b;font-family:-apple-system,'Segoe UI','Microsoft JhengHei',sans-serif;display:flex;min-height:100vh;align-items:center;justify-content:center}
.panel{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:40px 48px;text-align:center}
h1{margin:0 0 6px;font-size:26px;color:#1e3a8a}
input{width:200px;border:1px solid #cbd5e1;border-radius:6px;padding:10px 12px;font-size:15px}
button{background:#1d4ed8;color:#fff;border:none;border-radius:6px;padding:10px 20px;font-size:15px;font-weight:600;cursor:pointer;margin-left:8px}
p{color:#64748b;font-size:13px}</style></head><body>
<div class="panel"><h1>Joe Intelligence Terminal</h1>
<p>A5 設計 · persisted 證據快取唯讀 · 逐日累積</p>
<form method="get" action="/terminal"><input name="code" placeholder="輸入股票代號 e.g. 02318"><button>載入終端</button></form>
</div></body></html>"""

_A5_CSS = """
*{box-sizing:border-box}
body{margin:0;background:#f6f8fb;color:#16213a;font-family:-apple-system,'Segoe UI','Microsoft JhengHei','PingFang TC',sans-serif;font-size:12.5px}
.wrap{max-width:1420px;margin:0 auto;padding:16px 20px 46px}
.topbar{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid #e4e9f2;border-radius:12px;padding:10px 16px;margin-bottom:12px;box-shadow:0 1px 4px rgba(22,33,58,.06);flex-wrap:wrap}
.logo{width:36px;height:36px;border-radius:9px;background:linear-gradient(135deg,#1d4ed8,#0ea5e9);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800}
.topbar h1{font-size:16px;margin:0}
.topbar .sub{font-size:11px;color:#7a8699}
.topbar form{display:flex;gap:6px;align-items:center}
.topbar input{border:1px solid #d7dee9;border-radius:8px;padding:7px 11px;font-size:13px;width:130px}
.topbar .btn{background:#1d4ed8;color:#fff;border:none;border-radius:8px;padding:7px 15px;font-weight:700;cursor:pointer}
.topbar .nav{margin-left:auto;display:flex;gap:10px;font-size:11.5px;flex-wrap:wrap}
.topbar .nav a{color:#1d4ed8;text-decoration:none;font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(8,1fr);gap:9px;margin-bottom:12px}
.kpi{background:#fff;border:1px solid #e4e9f2;border-radius:10px;padding:9px 12px}
.kpi .l{font-size:10px;color:#7a8699;text-transform:uppercase}
.kpi .v{font-size:16.5px;font-weight:800;font-variant-numeric:tabular-nums;margin-top:2px}
.kpi .s{font-size:10px;color:#16a34a;font-weight:700}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.card{background:#fff;border:1px solid #e4e9f2;border-radius:12px;padding:12px 15px;box-shadow:0 1px 4px rgba(22,33,58,.05)}
.card.w{grid-column:1/-1}
.card h3{margin:0 0 8px;font-size:13px;color:#16213a}
.card h3 span{color:#7a8699;font-weight:400;font-size:11px}
table{width:100%;border-collapse:collapse;font-size:11.8px}
th{text-align:left;color:#8a94a6;font-size:10px;text-transform:uppercase;border-bottom:1.5px solid #e4e9f2;padding:4px 5px}
td{padding:4px 5px;border-bottom:1px solid #f2f5f9;font-variant-numeric:tabular-nums}
.num{text-align:right}
.up{color:#0e9f6e;font-weight:700}.down{color:#e02424;font-weight:700}
.bar{position:relative;background:#eef2f8;border-radius:4px;height:14px}
.bar i{position:absolute;left:0;top:0;bottom:0;background:linear-gradient(90deg,#1d4ed8,#3b82f6);border-radius:4px}
.bar b{position:absolute;right:6px;top:0;font-size:10px;line-height:14px}
.chip{display:inline-block;background:#eef4ff;color:#1d4ed8;border-radius:999px;padding:1.5px 9px;font-size:10.5px;margin:2px 4px 2px 0;font-weight:600;text-decoration:none}
.chip.g{background:#e6f7f1;color:#0e9f6e}.chip.r{background:#fdecec;color:#e02424}.chip.a{background:#fef3c7;color:#92400e}
.note{color:#8a94a6;font-size:10.5px;margin-top:6px}
.seg{display:inline-flex;gap:4px}
.seg span{background:#eef2f8;border-radius:4px;padding:2px 9px;font-size:10.5px;color:#5a6678;cursor:pointer}
.seg span.on{background:#1d4ed8;color:#fff}
.legend{display:flex;flex-wrap:wrap;gap:5px 14px;font-size:10.5px;margin:6px 0}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
.insight{background:#eef4ff;border-left:4px solid #1d4ed8;border-radius:6px;padding:10px 14px;font-size:12px;margin-top:8px}
.insight b{color:#1d4ed8}
.warnbox{background:#fef3c7;border-left:4px solid #f59e0b;border-radius:6px;padding:8px 12px;font-size:11.5px;color:#92400e}
a{color:#1d4ed8}
.jump{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.jump a{background:#fff;border:1px solid #e4e9f2;border-radius:999px;padding:5px 13px;font-size:12px;font-weight:600;color:#5a6678;text-decoration:none}
"""


def _esc(value) -> str:
    from html import escape

    return escape(str(value if value is not None else ""))


def _fmt_shares(value) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "—"


def _fmt(value) -> str:
    return _fmt_shares(value)


async def _gather(*coros):
    results = await asyncio.gather(*coros, return_exceptions=True)
    return [r if not isinstance(r, Exception) else None for r in results]


def _build_rainbow_series(snapshot_repo, normalized: str, top_n: int = 12, *, as_of: date | None = None) -> dict:
    """Walk persisted snapshots chronologically within the last year; per
    date, each top broker's share of CCASS. Grows as the daily snapshot
    accumulation lands."""
    floor = (as_of or date.today()) - timedelta(days=365)
    dates: list[str] = []
    snapshots: list[dict] = []
    snap = snapshot_repo.latest(normalized)
    while snap is not None and len(dates) < 40:
        if snap.snapshot_date < floor:
            break
        dates.insert(0, snap.snapshot_date.isoformat())
        holdings = {h.participant_id: h for h in snap.holdings}
        total = sum(h.shares for h in snap.holdings) or 1
        snapshots.append({"date": snap.snapshot_date.isoformat(), "total": total, "holdings": holdings})
        snap = snapshot_repo.previous(normalized, before_date=snap.snapshot_date)
    if len(dates) < 1:
        return {"dates": [], "brokers": [], "values": {}}
    latest = snapshots[-1]["holdings"]
    top_ids = [pid for pid, _ in sorted(latest.items(), key=lambda kv: kv[1].shares, reverse=True)[:top_n]]
    names: dict[str, str] = {}
    for pid in top_ids:
        for snap in reversed(snapshots):
            if pid in snap["holdings"]:
                names[pid] = getattr(snap["holdings"][pid], "participant_name", None) or getattr(
                    snap["holdings"][pid], "participant", None
                ) or pid
                break
        else:
            names[pid] = pid
    brokers = [{"id": pid, "name": names.get(pid, pid)} for pid in top_ids]
    values: dict[str, list[float]] = {pid: [] for pid in top_ids}
    for snap in snapshots:
        total = snap["total"]
        day_map = snap["holdings"]
        for pid in top_ids:
            h = day_map.get(pid)
            values[pid].append(round(h.shares / total * 100, 2) if h else 0.0)
    return {"dates": dates, "brokers": brokers, "values": values}


def _transfer_pairs(changes: list[tuple[str, int, int, int]]) -> list[dict]:
    """Approximate warehouse-transfer candidates from the two-snapshot diff:
    pair the largest decreases with similar-sized increases (±10%)."""
    downs = sorted([c for c in changes if c[1] < 0], key=lambda c: c[1])
    ups = sorted([c for c in changes if c[1] > 0], key=lambda c: -c[1])
    used_up: set[str] = set()
    pairs: list[dict] = []
    for down in downs:
        for up in ups:
            if up[0] in used_up:
                continue
            if up[1] <= 0:
                continue
            ratio = up[1] / abs(down[1]) if down[1] else 0
            if 0.9 <= ratio <= 1.1:
                pairs.append({"out": down[0], "out_shares": abs(down[1]), "in": up[0], "in_shares": up[1]})
                used_up.add(up[0])
                break
    return pairs[:10]


def _flow_summary(timelines, days: int, end: date) -> list[dict]:
    cutoff = end - timedelta(days=days)
    flows: dict[str, int] = {}
    for t in timelines:
        for m in t.movements:
            if m.change_shares and m.event_date >= cutoff:
                flows[t.filer] = flows.get(t.filer, 0) + m.change_shares
    ordered = sorted(flows.items(), key=lambda kv: kv[1], reverse=True)
    top = ordered[:5] + ordered[-5:]
    seen: set[str] = set()
    rows: list[dict] = []
    for filer, net in top:
        if filer in seen or net == 0:
            continue
        seen.add(filer)
        rows.append({"filer": filer, "net": net})
    return rows


def _render_kpis(snapshot, timelines, fundamentals, latest_close: str) -> str:
    holdings = sorted(snapshot.holdings, key=lambda h: h.shares, reverse=True) if snapshot else []
    total = sum(h.shares for h in holdings) or 1
    top5 = sum(h.shares for h in holdings[:5]) / total * 100 if holdings else 0
    top10 = sum(h.shares for h in holdings[:10]) / total * 100 if holdings else 0
    periods = len(fundamentals.rows) if fundamentals else 0
    cash = None
    if fundamentals and fundamentals.rows:
        cash = fundamentals.rows[0].cash
    kpis = [
        ("最新收市", '<span id="kpi-close">載入中…</span>', "Yahoo 延遲行情"),
        ("市值", '<span id="kpi-mcap">—</span>', "收市×已發行（可得時）"),
        ("CCASS 快照", str(snapshot.snapshot_date) if snapshot else "—", f"{len(holdings):,} 參與者"),
        ("Top 5 佔 CCASS", f"{top5:.1f}%", "集中度"),
        ("Top 10 佔 CCASS", f"{top10:.1f}%", "集中度"),
        ("DION 申報人", str(len(timelines) if timelines else 0), "官方申報"),
        ("業績期", str(periods), "已持久化"),
        ("現金結餘", _fmt(cash) if cash else "—", "百萬（最新期）"),
    ]
    return "".join(
        f'<div class="kpi"><div class="l">{_esc(l)}</div><div class="v">{v}</div><div class="s">{_esc(s)}</div></div>'
        for l, v, s in kpis
    )


@router.get("/terminal", response_class=HTMLResponse)
async def terminal(
    code: str = Query(default=""),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    flow: int = Query(default=30, ge=7, le=1825),
):
    try:
        flow = int(flow)
    except (TypeError, ValueError):
        flow = 30
    normalized = (code or "").strip()
    from ccass_core.normalize import normalize_stock_code

    normalized = normalize_stock_code(normalized) if normalized else ""
    if not normalized:
        return HTMLResponse(_FAST_LANDING)
    now = datetime.now(UTC)
    end = end_date or now.date()
    start = start_date or end - timedelta(days=365 * 5)
    svc = get_research_context_service()
    snapshot_repo = svc.snapshot_repository

    snapshot, timeline, events, fundamentals, entities, share_capital, announcements = await _gather(
        asyncio.to_thread(snapshot_repo.latest, normalized),
        get_ownership_timeline_service().get_timeline(normalized, start_date=start, end_date=end),
        asyncio.to_thread(get_intelligence_events_service().event_repository.load, normalized),
        asyncio.to_thread(svc.fundamentals_repository.load, normalized),
        asyncio.to_thread(svc.entity_repository.load_rows, normalized, start_date=start, end_date=end),
        asyncio.to_thread(svc.share_capital_repository.load, normalized, start_date=start, end_date=end),
        asyncio.to_thread(get_announcements_service().repository.load, normalized, start_date=start, end_date=end),
    )
    snapshot = snapshot if snapshot is not None else None
    timelines = timeline.timelines if timeline is not None else []
    event_rows = events if events is not None else []
    fundamentals = fundamentals if fundamentals is not None else None
    entities = entities if entities is not None else []
    share_capital_rows = share_capital.rows if share_capital is not None else []
    announcement_rows = announcements.announcements if announcements is not None else []

    holdings = sorted(snapshot.holdings, key=lambda h: h.shares, reverse=True) if snapshot else []
    total = sum(h.shares for h in holdings) or 1

    prev = None
    if snapshot is not None:
        try:
            prev = snapshot_repo.previous(normalized, before_date=snapshot.snapshot_date)
        except Exception:
            prev = None

    changes: list[tuple[str, int, int, int]] = []
    if snapshot is not None and prev is not None:
        prev_map = {h.participant_id: h.shares for h in prev.holdings}
        now_map = {h.participant_id: h.shares for h in holdings}
        names = {h.participant_id: (getattr(h, "participant_name", None) or getattr(h, "participant", None) or h.participant_id) for h in holdings}
        for pid in prev_map:
            names.setdefault(pid, pid)
        for pid, now_shares in now_map.items():
            old = prev_map.get(pid)
            if old is None:
                changes.append((pid, now_shares, now_shares, 1))
            else:
                changes.append((pid, now_shares - old, now_shares, 0))
        for pid, old in prev_map.items():
            if pid not in now_map and old:
                changes.append((pid, -old, 0, -1))

    transfer_pairs = _transfer_pairs(changes)
    rainbow = _build_rainbow_series(snapshot_repo, normalized, as_of=end)
    flows = _flow_summary(timelines, flow, end)

    # ---- 轉倉偵測 rows ----
    tr_rows = "".join(
        f"<tr><td>快照間</td><td class='down'>{_esc(p['out'][:30])} −{_fmt_shares(p['out_shares'])}</td>"
        f"<td class='up'>{_esc(p['in'][:30])} +{_fmt_shares(p['in_shares'])}</td><td class='num'>≈同量</td>"
        f"<td><span class='chip a'>轉倉候選</span></td></tr>"
        for p in transfer_pairs
    ) or "<tr><td colspan='5'>兩張快照間無同量一減一增配對</td></tr>"

    # ---- broker distribution ----
    prev_map = {h.participant_id: h.shares for h in prev.holdings} if prev is not None else {}
    dist_rows = []
    for i, h in enumerate(holdings[:10]):
        pid = h.participant_id
        name = getattr(h, "participant_name", None) or getattr(h, "participant", None) or pid
        old = prev_map.get(pid)
        if old is None:
            ch_html = "<span class='up'>新</span>"
        else:
            ch = h.shares - old
            ch_html = f"<span class='{'up' if ch > 0 else 'down' if ch < 0 else ''}'>{_fmt_shares(ch) if ch else '+0'}</span>"
        dist_rows.append(
            f"<tr><td>{i + 1}</td><td>{_esc(str(name)[:34])}</td><td class='num'>{_fmt_shares(h.shares)}</td>"
            f"<td class='num'>{h.shares / total * 100:.2f}%</td><td class='num'>{ch_html}</td></tr>"
        )

    # ---- 資金流向 rows ----
    flow_rows = "".join(
        f"<tr><td>{_esc(f['filer'][:34])}</td><td class='num'><span class='{'up' if f['net'] > 0 else 'down'}'>{_fmt_shares(f['net'])}</span></td></tr>"
        for f in flows
    ) or "<tr><td colspan='2'>窗口內無申報變動</td></tr>"

    # ---- 大股東動向 ----
    own_rows = "".join(
        f"<tr><td>{_esc(t.filer[:36])}</td><td class='num'>{t.movements_count}</td>"
        f"<td class='num'><span class='up'>+{t.increases}</span>/<span class='down'>−{t.decreases}</span></td>"
        f"<td class='num'>{_fmt_shares(t.latest_present_balance)}</td><td class='num'>{t.latest_percentage if t.latest_percentage is not None else '—'}</td></tr>"
        for t in timelines[:10]
    )

    # ---- 90日重點申報 ----
    recent: list[dict] = []
    cutoff90 = end - timedelta(days=90)
    for t in timelines:
        for m in t.movements:
            if m.change_shares and m.event_date >= cutoff90:
                recent.append({"date": m.event_date, "filer": t.filer, "ch": m.change_shares, "present": m.present_balance})
    recent.sort(key=lambda r: r["date"], reverse=True)
    recent_rows = "".join(
        f"<tr><td>{r['date']}</td><td>{_esc(r['filer'][:32])}</td>"
        f"<td class='num'><span class='{'up' if r['ch'] > 0 else 'down'}'>{'+' if r['ch'] > 0 else ''}{_fmt_shares(r['ch'])}</span></td>"
        f"<td class='num'>{_fmt_shares(r['present'])}</td></tr>"
        for r in recent[:10]
    ) or "<tr><td colspan='4'>90 日內無申報</td></tr>"

    # ---- 情報事件流 ----
    event_rows = sorted(event_rows, key=lambda e: e.announce_date, reverse=True)[:10]
    event_rows_html = "".join(
        f"<tr><td>{e.announce_date}</td><td>{_esc(e.event_type)}</td><td>{_esc(str(e.counterparty or e.entity_name or '—'))[:40]}</td>"
        f"<td><span class='chip {'g' if e.confidence == 'extracted' else ''}'>{e.confidence}</span></td></tr>"
        for e in event_rows
    )

    # ---- 港交所公告 ----
    ann_sorted = sorted(announcement_rows, key=lambda a: a.announcement_date, reverse=True)
    ann_rows = "".join(
        f"<tr><td>{a.announcement_date}</td><td>{_esc((a.category or '—')[:16])}</td>"
        f"<td><a href='{_esc(a.link or '')}' target='_blank'>{_esc(a.title[:70])}</a></td></tr>"
        for a in ann_sorted[:10]
    ) or "<tr><td colspan='3'>無持久化公告 — 觸發 /admin/announcements/job</td></tr>"

    # ---- 損益表 / 資產負債表（fundamentals rows）----
    f_rows = sorted(fundamentals.rows, key=lambda r: (r.announcement_date, r.reporting_period), reverse=True) if fundamentals else []
    periods = [r.reporting_period for r in f_rows[:3]]
    def _by_period(field: str):
        return {r.reporting_period: r.model_dump().get(field) for r in f_rows}
    revenue = _by_period("revenue")
    profit = _by_period("net_profit_loss")
    ocf = _by_period("operating_cash_flow")
    equity = _by_period("equity")
    cash = _by_period("cash")
    debt = _by_period("debt")
    net_assets = _by_period("net_assets")
    shares_out = _by_period("shares_outstanding")

    def _ratio(num_map: dict, den_map: dict) -> dict:
        out: dict[str, str] = {}
        for p in periods:
            n, d = num_map.get(p), den_map.get(p)
            out[p] = f"{n / d * 100:.2f}%" if (n is not None and d not in (None, 0)) else "—"
        return out

    margin = _ratio(profit, revenue)
    roe = _ratio(profit, equity)
    nav_ps = {p: (round(equity.get(p) * 1e6 / s, 2) if (equity.get(p) is not None and s not in (None, 0)) else "—") for p, s in shares_out.items()}
    eps = {p: (round(profit.get(p) * 1e6 / s, 3) if (profit.get(p) is not None and s not in (None, 0)) else "—") for p, s in shares_out.items()}
    netdebt = {p: ((debt.get(p) - cash.get(p)) if (debt.get(p) is not None and cash.get(p) is not None) else None) for p in periods}

    def _cells(field_map: dict) -> str:
        return "".join(f"<td class='num'>{_fmt(field_map.get(p)) if field_map.get(p) is not None else '—'}</td>" for p in periods)
    def _cells_raw(field_map: dict) -> str:
        return "".join(f"<td class='num'>{field_map.get(p)}</td>" for p in periods)
    is_rows = "".join(f"<tr><td>{label}</td>{_cells(m)}</tr>" for label, m in (("收入", revenue), ("純利", profit), ("經營現金流", ocf)))
    is_rows += "".join(f"<tr><td>{label}</td>{_cells_raw(m)}</tr>" for label, m in (("純利率", margin), ("每股盈利", eps)))
    bs_rows = "".join(f"<tr><td>{label}</td>{_cells(m)}</tr>" for label, m in (("淨資產", net_assets), ("股東權益", equity), ("現金及等價物", cash), ("借貸總額", debt), ("淨負債(借貸−現金)", netdebt)))
    bs_rows += "".join(f"<tr><td>{label}</td>{_cells_raw(m)}</tr>" for label, m in (("每股淨值", nav_ps), ("ROE", roe)))
    is_note = "" if f_rows else "<p class='note'>無持久化業績 — 觸發 /admin/fundamentals/job</p>"

    # ---- 相關人物 ----
    persons: list[tuple[str, str, str]] = []
    for t in timelines[:5]:
        persons.append((_esc(t.filer[:34]), f"{'機構/股東'} {t.latest_percentage or '—'}%", f"{t.movements_count} 次官方申報"))
    for row in entities[:5]:
        persons.append((_esc(str(row.entity_name or "—"))[:34], _esc(row.entity_type), "文件抽取"))
    person_rows = "".join(f"<tr><td>{p}</td><td>{r}</td><td>{c}</td></tr>" for p, r, c in persons) or "<tr><td colspan='3'>暫無</td></tr>"

    # ---- 股本故事 ----
    sc_sorted = sorted(share_capital_rows, key=lambda r: r.announce_date)
    sc_first = sc_sorted[0].shares_million if sc_sorted else None
    sc_last = sc_sorted[-1].shares_million if sc_sorted else None
    dilution = ""
    if sc_first and sc_last:
        dilution = f"窗口首尾 {sc_first}M → {sc_last}M（{(sc_last / sc_first - 1) * 100:+.1f}%）"
    sc_rows = "".join(
        f"<tr><td>{r.announce_date}</td><td class='num'>{_fmt(r.shares_million)}M</td><td>{_esc((r.reason or '—')[:40])} {','.join(r.reason_tags)}</td></tr>"
        for r in sc_sorted[:10]
    ) or "<tr><td colspan='3'>無持久化股本 — 觸發 /admin/share-capital/job</td></tr>"

    rainbow_json = json.dumps(rainbow, ensure_ascii=False)

    html = f"""<!DOCTYPE html><html lang="zh-HK"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{normalized} · Intelligence Terminal</title><style>{_A5_CSS}</style></head><body><div class="wrap">
<div class="topbar"><div class="logo">J</div><div><h1>{normalized} · Intelligence Terminal</h1><div class="sub">A5 設計 · DT 式彩虹堆疊 · 陰陽燭 · 全組件 · 缺口期已由 gap_pack 導入（證據股）</div></div>
<form method="get" action="/terminal"><input name="code" value="{_esc(normalized)}"><button class="btn">切換</button></form>
<div class="nav"><a href="/?code={normalized}">快總覽</a><a href="/full?code={normalized}">完整產品</a><a href="/console?code={normalized}">Console</a><a href="/api/v1/stocks/{normalized}/research-context?format=markdown">研究包 MD</a><a href="/api/v1/stocks/{normalized}/report-draft">報告初稿</a></div></div>
<div class="kpis">{_render_kpis(snapshot, timelines, fundamentals, "—")}</div>
<div class="jump"><a href="#pxcard">價格</a><a href="#rbcard">券商彩虹</a><a href="#distcard">分佈</a><a href="#flowcard">資金流向</a><a href="#trcard">轉倉偵測</a><a href="#owncard">大股東</a><a href="#evcard">事件流</a><a href="#anncard">公告</a><a href="#fscard">財務</a><a href="#dlcard">下載</a></div>
<div class="grid">

<div class="card w" id="pxcard"><h3>價格 · 陰陽燭 + 成交量 <span>· 日線 · Yahoo 延遲</span>
<div class="seg" id="pxseg"><span data-px="22">1個月</span><span class="on" data-px="66">3個月</span><span data-px="130">6個月</span><span data-px="260">1年</span></div></h3>
<div id="candles">載入中…</div></div>

<div class="card w" id="rbcard"><h3>★ CCASS 券商彩虹 · 堆疊面積圖 <span>· 每色=一個券商 · 厚度=持股% · 總高=合計持股% · 隨每日快照累積生長</span></h3>
<div id="rainbow"></div><div class="legend" id="rblegend"></div>
<div class="insight"><b>分段解讀：</b>{len(rainbow['dates'])} 個持久化快照點。快照日之間無日度數據（缺口/累積中如實標示）——每日快照 job 會逐日加厚彩虹。</div></div>

<div class="card" id="distcard"><h3>券商持股完整分佈 <span>· Top 10 / 共 {len(holdings)} 名 · 對上一快照變化</span></h3>
<table><tr><th>#</th><th>券商 / 參與者</th><th>持股</th><th>佔 CCASS</th><th>變化</th></tr>{''.join(dist_rows)}</table>
<p class="note">由 {prev.snapshot_date if prev is not None else '—'} → {snapshot.snapshot_date if snapshot else '—'} 兩張持久化快照差分</p></div>

<div class="card" id="flowcard"><h3>資金流向 <span>· 官方申報推算 ·
<a href='/terminal?code={normalized}&flow=7'>7D</a> ·
<span style='color:#1d4ed8;font-weight:800'>{flow}D</span> ·
<a href='/terminal?code={normalized}&flow=90'>90D</a> ·
<a href='/terminal?code={normalized}&flow=365'>1Y</a> ·
<a href='/terminal?code={normalized}&flow=1825'>5Y</a></span></h3>
<table><tr><th>Filer</th><th>淨申報（{flow}D）</th></tr>{flow_rows}</table>
<p class="note">官方 DION 申報股數淨變化 · 推算港元值需要申報日收市價（v2）</p></div>

<div class="card" id="trcard"><h3>轉倉偵測 <span>· 快照間同量一減一增配對（±10%）</span></h3>
<table><tr><th>窗口</th><th>流出券商</th><th>流入券商</th><th>股數</th><th>判讀</th></tr>{tr_rows}</table>
<p class="note">⚠️ 轉倉 ≠ 真實買入 · 快照間配對為近似（同日同量偵測需日內多快照）</p></div>

<div class="card" id="owncard"><h3>⑩ 大股東動向 <span>· 官方 DION 鏈 · {len(timelines)} 名</span></h3>
<table><tr><th>Filer</th><th>申報</th><th>增/減</th><th>最新持倉</th><th>%</th></tr>{own_rows}</table>
<p class="note">首次申報方向標 unknown（無前值可鏈）· 永不估計</p></div>

<div class="card"><h3>⑪ 近 90 日重點申報 <span>· Top 10</span></h3>
<table><tr><th>日期</th><th>Filer</th><th>變化</th><th>申報後</th></tr>{recent_rows}</table></div>

<div class="card" id="evcard"><h3>⑫ 情報事件流 <span>· {len(event_rows)} 項（最新 10）</span></h3>
<table><tr><th>日期</th><th>類型</th><th>對手方</th><th>信心</th></tr>{event_rows_html}</table>
<p class="note"><a href='/api/v1/stocks/{normalized}/intelligence-events'>全量 JSON</a> · <a href='/api/v1/stocks/{normalized}/alerts?days=30'>30 日警報</a></p></div>

<div class="card" id="anncard"><h3>港交所公告 <span>· {len(ann_sorted)} 份持久化（最新 10，原生繁體標題 + 原文連結）</span></h3>
<table><tr><th>日期</th><th>類別</th><th>標題</th></tr>{ann_rows}</table>
<p class="note">窗口外更舊公告由累積 workflow 逐窗補回</p></div>

<div class="card"><h3>異動盤 <span>· 大手/連續/對盤（當日捕捉）</span></h3>
<div class="warnbox">tape 當日限定 — 需日內定時捕捉（Actions 分鐘級）先有歷史；捕捉器屬 RTSS/監察階段工程。</div></div>

<div class="card"><h3>成交量分佈 <span>· Value Area（近似 POC）</span>
<div class="seg"><span>1個月</span><span class="on">1年</span></div></h3>
<div id="vpvr">載入中…</div></div>

<div class="card"><h3>⑭ 資產負債表 <span>· 深度解析（v4 目標）</span></h3>
<table><tr><th>項目</th>{''.join(f'<th>{_esc(p)}</th>' for p in periods)}</tr>{bs_rows}</table>
<p class="note">現有欄位：淨資產/股東權益/現金/借貸 · 總資產/存貨/應收明細 = v4 解析工程（年報綜合資產負債表頁）</p></div>

<div class="card"><h3>⑭b 損益表 <span>· 官方業績文件抽取</span></h3>
<table><tr><th>項目</th>{''.join(f'<th>{_esc(p)}</th>' for p in periods)}</tr>{is_rows}</table>{is_note}
<p class="note">真實欄位計算：純利率/ROE/每股盈利/每股淨值由現有欄位推導 · 毛利/股息明細 = v4 解析工程</p></div>

<div class="card"><h3>⑩ 相關人物 <span>· DION 大戶 + 文件抽取實體</span></h3>
<table><tr><th>人物 / 機構</th><th>角色</th><th>關聯</th></tr>{person_rows}</table>
<p class="note">人物 × 券商 × 事件交叉 = 財技訊號（<a href='/api/v1/intermediary-graph'>中介圖譜 JSON</a>）</p></div>

<div class="card"><h3>⑰ 股本故事 <span>· 窗口內</span></h3>
<table><tr><th>公佈日</th><th>股本</th><th>原因</th></tr>{sc_rows}</table>
<p class="note">{dilution or '窗口內無股本變動紀錄'}</p></div>

<div class="card w" id="dlcard"><h3>下載 AI 數據源（給 ChatGPT / 任何 AI）</h3>
<div>
<a class="chip" href="/api/v1/stocks/{normalized}/research-context?format=json">研究包 JSON（全量結構化+溯源）</a>
<a class="chip" href="/api/v1/stocks/{normalized}/research-context?format=markdown">研究包 Markdown（AI 直讀）</a>
<a class="chip" href="/api/v1/stocks/{normalized}/report-draft">AI 報告初稿 MD（八章+分析位）</a>
<a class="chip" href="/api/v1/stocks/{normalized}/intelligence-events">事件全量 JSON</a>
<a class="chip" href="/api/v1/intermediary-graph">中介圖譜 JSON</a>
<a class="chip" href="/api/v1/stocks/{normalized}/ownership-timeline">Ownership Timeline JSON</a>
<a class="chip" href="/api/v1/stocks/{normalized}/alerts?days=30">30 日警報 JSON</a>
</div><p class="note">一條連結交俾 AI — 全部帶來源與信心標籤</p></div>

<div class="card"><h3>㉑ 溯源與覆蓋 <span>· fail-loud</span></h3>
<span class="chip">official = 官方申報原行</span><span class="chip">extracted = 官方文件抽取</span>
<p class="note">CCASS 缺口期已導入 gap_pack（證據股 2025-12→2026-07 完整）· 缺失永不插值 · 每日快照+累積由 GitHub Actions 排程</p></div>
</div></div>
<script>
(function(){{
  var CODE = "{normalized}";
  var RB = {json.dumps(rainbow, ensure_ascii=False)};
  var COLORS=["#1d4ed8","#0ea5e9","#16a34a","#f59e0b","#e02424","#8b5cf6","#ec4899","#14b8a6","#f97316","#64748b","#84cc16","#06b6d4","#a855f7","#ef4444","#0d9488"];
  function esc(s){{return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;")}}
  function fmt(n){{return (n==null)?"—":Number(n).toLocaleString("en-US")}}

  var SHARES_M = {float(f_rows[0].model_dump().get("shares_outstanding") or 0) if f_rows else 0};

  var ALLROWS=[];
  function renderCandles(rows){{
    var box=document.getElementById("candles");if(!box)return;
    if(!rows.length){{box.innerHTML='<p class="note">無價格數據</p>';return}}
    var W=1300,AX=78,H=200,lo=1e15,hi=0,vmax=1;
    rows.forEach(function(r){{lo=Math.min(lo,(r.low!=null?r.low:r.close));hi=Math.max(hi,(r.high!=null?r.high:r.close));vmax=Math.max(vmax,r.volume||0)}});
    var pad=(hi-lo)*0.06||1;lo-=pad;hi+=pad;
    var plotW=W-AX;
    var step=plotW/rows.length,bw=Math.max(1.5,step*0.6);
    var svg='<svg width="100%" viewBox="0 0 '+W+' '+(H+54)+'" preserveAspectRatio="none">';
    for(var g=0;g<=4;g++){{
      var pv=lo+(hi-lo)*g/4,py=H-(pv-lo)/(hi-lo)*H;
      svg+='<line x1="0" y1="'+py+'" x2="'+plotW+'" y2="'+py+'" stroke="#eef2f8" stroke-width="1"/>';
      svg+='<text x="'+(plotW+6)+'" y="'+(py+4)+'" font-size="10.5" fill="#5a6678">'+pv.toFixed(2)+'</text>';
    }}
    rows.forEach(function(r,i){{
      var x=i*step+step/2;
      var hiV=(r.high!=null?r.high:r.close),loV=(r.low!=null?r.low:r.close);
      var yHi=H-((hiV-lo)/(hi-lo)*H),yLo=H-((loV-lo)/(hi-lo)*H);
      var o=(r.open!=null?r.open:r.close),c=r.close;
      var yO=H-((Math.max(o,c)-lo)/(hi-lo)*H),yC=H-((Math.min(o,c)-lo)/(hi-lo)*H);
      var col=(c>=o)?"#0e9f6e":"#e02424";
      svg+='<line x1="'+x+'" y1="'+yHi+'" x2="'+x+'" y2="'+yLo+'" stroke="'+col+'" stroke-width="1"/>';
      svg+='<rect x="'+(x-bw/2)+'" y="'+yO+'" width="'+bw+'" height="'+Math.max(1,yC-yO)+'" fill="'+col+'"/>';
      var vh=(r.volume||0)/vmax*46;
      svg+='<rect x="'+(x-bw/2)+'" y="'+(H+6+(46-vh))+'" width="'+bw+'" height="'+vh+'" fill="'+col+'" opacity="0.7"/>';
    }});
    svg+='</svg>';
    box.innerHTML=svg+'<p class="note">綠燭=收≥開 · 紅燭=收&lt;開 · 底部柱=成交量 · 來源：Yahoo（延遲）</p>';
  }}
  function renderVPVR(rows){{
    var box=document.getElementById("vpvr");if(!box)return;
    if(!rows.length){{box.innerHTML='<p class="note">無數據</p>';return}}
    var lo=1e15,hi=0;rows.forEach(function(r){{lo=Math.min(lo,r.close);hi=Math.max(hi,r.close)}});
    var N=22,span=(hi-lo)||1,buckets=[];for(var i=0;i<N;i++)buckets.push(0);
    rows.forEach(function(r){{var b=Math.min(N-1,Math.floor((r.close-lo)/span*N));buckets[b]+=(r.volume||0)}});
    var vmax=1;pct=0;var poc=0;buckets.forEach(function(v,i){{if(v>vmax)vmax=v;if(v>buckets[poc])poc=i}});
    var W=560,rowH=13;
    var svg='<svg width="100%" viewBox="0 0 '+W+' '+(N*rowH+6)+'">';
    buckets.forEach(function(v,i){{
      var w=v/vmax*(W-170);
      var price=(lo+span*((i+0.5)/N)).toFixed(2);
      var near=Math.abs(i-poc)<=2;
      svg+='<rect x="0" y="'+(i*rowH+2)+'" width="'+Math.max(2,w)+'" height="'+(rowH-3)+'" fill="'+(i===poc?"#1d4ed8":near?"#3b82f6":"#cbd5e1")+'"/>';
      svg+='<text x="'+(W-160)+'" y="'+(i*rowH+12)+'" font-size="10" fill="#5a6678">'+price+'</text>';
      svg+='<text x="'+(W-80)+'" y="'+(i*rowH+12)+'" font-size="10" fill="#8a94a6">'+(v/1e6).toFixed(1)+'M</text>';
    }});
    svg+='</svg>';
    box.innerHTML=svg+'<p class="note">深藍=POC 最大成交量價位 · 近藍=Value Area（近似：收市價分桶）</p>';
  }}
  function fillPriceKPIs(rows){{
    if(!rows.length)return;
    var last=rows[rows.length-1],prev=rows.length>1?rows[rows.length-2]:null;
    var k1=document.getElementById("kpi-close");
    if(k1)k1.innerHTML=last.close+((prev&&prev.close)?'<div class="s">'+((last.close>=prev.close?"+":"")+((last.close-prev.close)/prev.close*100).toFixed(2)+"%</div>"):"");
    var k2=document.getElementById("kpi-mcap");
    if(k2&&SHARES_M>0)k2.innerHTML=(last.close*SHARES_M/100).toFixed(1)+"億"+'<div class="s">'+SHARES_M+"M股×"+last.close+"</div>";
  }}
  function loadPrice(days){{
    fetch("/api/v1/stocks/"+CODE+"/price?days="+days).then(function(r){{return r.json()}}).then(function(j){{
      var rows=(j.prices||[]).filter(function(r){{return r.close!=null}});
      ALLROWS=rows;fillPriceKPIs(rows);renderCandles(rows);renderVPVR(rows);
    }}).catch(function(e){{var b=document.getElementById("candles");if(b)b.textContent="價格載入失敗: "+e}});
  }}
  document.addEventListener("click",function(ev){{
    var t=ev.target;
    if(t&&t.dataset&&t.dataset.px){{
      var seg=document.getElementById("pxseg");if(seg)Array.prototype.forEach.call(seg.children,function(s){{s.classList.remove("on")}});
      t.classList.add("on");loadPrice(parseInt(t.dataset.px,10));
    }}
  }});

  function renderRainbow(){{
    var box=document.getElementById("rainbow");if(!box)return;
    var dates=RB.dates,brokers=RB.brokers,n=dates.length;
    if(!n){{box.innerHTML='<p class="note">持久化快照累積中</p>';return}}
    var W=1300,AX2=64,H=230,step=n>1?((W-AX2)/(n-1)):W;
    var series=brokers.map(function(b){{return []}});
    var totals=[];
    for(var i=0;i<n;i++){{
      var running=0;
      brokers.forEach(function(b,bi){{
        var v=(RB.values[b.id]&&RB.values[b.id][i]!=null)?RB.values[b.id][i]:0;
        series[bi].push([running,running+v]);running+=v;
      }});
      totals.push(running);
    }}
    var top=Math.max.apply(null,totals.concat([1]))*1.1;
    var svg='<svg width="100%" viewBox="0 0 '+W+' '+(H+26)+'" preserveAspectRatio="none">';
    brokers.forEach(function(b,bi){{
      var col=COLORS[bi%COLORS.length],d="";
      series[bi].forEach(function(seg,i){{d+=(i===0?"M":"L")+(i*step)+","+(H-seg[1]/top*H)}});
      for(var i=n-1;i>=0;i--){{d+=" L"+(i*step)+","+(H-series[bi][i][0]/top*H)}}
      svg+='<path d="'+d+' Z" fill="'+col+'" opacity="0.82"/>';
    }});
    dates.forEach(function(dt,i){{
      svg+='<text x="'+(i*step)+'" y="'+(H+18)+'" font-size="9.5" fill="#8a94a6">'+dt.slice(5)+'</text>';
      svg+='<line x1="'+(i*step)+'" y1="0" x2="'+(i*step)+'" y2="'+H+'" stroke="#eef2f8"/>';
    }});
    for(var gp=0;gp<=4;gp++){{var pv=top*gp/4,py=H-pv/top*H;
      svg+='<text x="'+(W-AX2+8)+'" y="'+(py+4)+'" font-size="10" fill="#5a6678">'+pv.toFixed(1)+'%</text>';
      svg+='<line x1="0" y1="'+py+'" x2="'+(W-AX2)+'" y2="'+py+'" stroke="#eef2f8" stroke-width="1"/>';
    }}
    svg+='</svg>';
    box.innerHTML=svg;
    var lg=document.getElementById("rblegend");
    if(lg)lg.innerHTML=brokers.map(function(b,bi){{
      var last=(RB.values[b.id]&&RB.values[b.id][n-1]!=null)?RB.values[b.id][n-1]:null;
      var pctTxt=(last!=null)?(" "+last.toFixed(2)+"%"):"";
      return '<span><i style="background:'+COLORS[bi%COLORS.length]+'"></i>'+esc(b.name.slice(0,26))+pctTxt+"</span>";
    }}).join("");
  }}

  renderRainbow();
  loadPrice(260);
}})();
</script></body></html>"""

    return HTMLResponse(html)

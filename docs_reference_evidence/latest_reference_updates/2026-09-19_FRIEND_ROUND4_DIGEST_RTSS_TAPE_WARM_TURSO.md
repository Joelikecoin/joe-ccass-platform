# FRIEND ROUND-4 NOTES DIGEST — RTSS / tape / warm cache / Turso&Drive (2026-09-19)

> **Sources:** four new notes in `latest_reference_updates/` dated 1309–1709 2026 (authoritative folder).
> **Purpose:** map each note to our platform — what we already do better (with evidence), what to adopt, what stays scoped out. Feeds V3 §12 next-session list.
> **Governance reminder (V3 §2):** RTSS / VCP / 派貨 / 殼價 are Derived Intelligence — never raw-data services inside this platform; RTSS is a **separate future project**.

## 1. `17092026 warm_ccass_cache…` — friend's warm cache revisited

- Friend-side facts: `warm_ccass_cache.py` runs `hybrid_light` (`?light=1`) = **Concentration + Big Changes only** (1.7 s because shallow — 10 Big Changes + 15 Concentration rows for 01825), **not** participant-level; history-date support unconfirmed.
- The critical fork: `cconchist.asp` (concentration **history**) vs `choldings.asp` (**today** only). If warm hits the latter, it is useless for any T-2 historical predictor.
- **Amends V3 §5.1 (which recorded warm_ccass_cache ABSENT from the 08-14 pack): the friend's later rounds did build it — new evidence, investigation legitimately re-opened at digest level.**
- **Our position (verified in code 2026-09-19):** we do NOT have this fork:
  - Historical layer `app/sources/webbsite_historical.py` reads the **local canonical archive**, fully date-parameterized (`get_holdings_for_date(requested_date)`), bounded by `WEBB_HISTORICAL_COVERAGE_END=2025-12-24` (the known gap start).
  - Live layer `app/sources/webbsite.py` uses `choldings.asp`/`orgdata.asp` for current snapshots, and our accumulation lives in **Turso** — warm reads = SQL on accumulated history, date-parameterized by construction.
  - **We already do better:** any "warm" read on our stack serves full participant-level history; the friend's warm serves an undated summary at best.
- Residual watch-item (non-blocking): if we ever add live mirror concentration-history fetching, use `cconchist.asp`, never `choldings.asp` for history.

## 2. `14092026 逐筆成交分析` — Longbridge tape: today-only, so capture-daily or nothing

- Verified on a real case (09-14): Longbridge **tick tape exists for TODAY only** — historical tape is unrecoverable (08-27/09-01/09-03 gone forever unless captured live).
- Analytical gold in the note: M盤 (off-book) = 96.2% of volume at 0.520 while market printed 0.69–0.735 (24.6% real-vs-displayed gap); book so thin that HK$140k moved price 2.1%; no broker IDs on tape (CCASS T+2 confirms brokers).
- **Implication for us:** any tape/爆量 history is **accumulate-or-lose** — exactly our Evidence-Cache philosophy (V3 §2 layer C). If Phase-1 ever wants tape depth, it must be a daily capture job from day one; backfill is impossible. Phase-1 candidate note only — not P0.
- Also validates the dual-denominator discipline: tape volume vs M盤 volume must never be mixed in turnover-derived analytics (V3 derived-turnover labelling rule).

## 3. `13092026 自建 RTSS 式即市異動監察｜開工前準備` — separate future project; three transferable rules

- RTSS stack sketch: Longbridge keys + Turso + private GitHub repo + Streamlit Cloud, `pip install longport libsql-client streamlit`, no Docker — deliberately a **separate lightweight system**, consistent with V3 §2 (derived intelligence is a separate layer, never a raw-data service here) and §8 (standalone screener pages explicitly stopped for THIS platform).
- **Three rules worth importing into our engineering culture:**
  1. **The 5-minute test decides the architecture**: probe whether intraday data actually changes before building intraday anything. Our equivalent discipline: Fail-Loud runtime verification before feature work (already §6).
  2. **Day-1 = one real CSV** (~30 lines), not the whole website — smallest real evidence first. Matches our Reference→Current→Gap workflow.
  3. **Expectation honesty (quoted):** 爆量訊號經檢驗冇超額報酬（616 樣本，p=0.600）— the tool's value is 報時（邊隻今日有人郁 → 人手查財技）+ 累積（六個月後獨有歷史庫），**不是買入訊號**. Any screener/monitor built later must carry this label.
- Account checklist status for our stack: Longbridge keys ✅ (production env), Turso ✅, GitHub ✅, Streamlit Cloud — n/a (our portal is FastAPI on Render).

## 4. `13092026 Joe Platform Turso&Drive建立` — independent validation of our storage model

- Friend-side thinking converges on the same architecture we locked in §8.0: **Turso = query/accumulation layer; Drive = archive only**; GitHub Actions daily after-close; events idempotent (`INSERT OR IGNORE` — ours already uses `ON CONFLICT … DO UPDATE` upserts).
- Their 4-table sketch (securities / events 964條 / daily_quotes / tracking_book) is a coarse preview of our Phase-1 🥇 unified event layer — our event schema (§8: event_type, announce/effective dates, shares before/after, counterparty, placing_agent, adviser, confidence) is strictly richer. No change needed; treat as confirmation.
- Suggestion "CCASS Research MCP 加 route 讀 Turso" — already satisfied: our API + job infra expose the same reads.

## 5. `14092026 跟DT 或原Webbsite做…` — the CCASS middle-gap data source named

- Contains the Drive folder link (Joe's private channel) designated for **post-2025-12 gap data** — this is the gap-closure source §7's parallel track awaited ("Joe will supply from private channels").
- DT (per the RTSS note) exports 殼股價值分析 + 六個財技事件（配股/供股/全購/合股/拆股/CB）— **these six map 1:1 onto our Phase-1 event_type values**; if DT has an API, the "only human step" in any weekly pipeline disappears. Import path (not re-derivation) is our committed posture for gap closure.
- Action queued for Phase-1: build the labelled import path (source=DT/webbsite-archive, provenance kept) when the data lands; do not start Zhipu retrieval (unchanged rule).

## 6. File housekeeping

- `15092026 原webbsite係點拎DATA.md` is **0 bytes (empty)** on the Drive — likely a failed save. Joe: re-upload if it had content.

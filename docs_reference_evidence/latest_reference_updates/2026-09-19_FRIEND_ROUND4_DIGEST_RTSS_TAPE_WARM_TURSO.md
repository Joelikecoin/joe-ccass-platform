# FRIEND ROUND-4 NOTES DIGEST — RTSS / tape / warm cache / Turso&Drive (2026-09-19)

> **Sources:** four new notes in `latest_reference_updates/` dated 1309–1709 2026 (authoritative folder).
> **Joe's framing (2026-09-19): these four notes are targeted answers to HIS current situation — (a) HOW to extract data, and (b) the relationship between Turso and the database.** Mapping below.
> **Purpose:** map each note to our platform — what we already do better (with evidence), what to adopt, what stays scoped out. Feeds V3 §12 next-session list.
> **Governance reminder (V3 §2):** RTSS / VCP / 派貨 / 殼價 are Derived Intelligence — never raw-data services inside this platform; RTSS is a **separate future project**.

## 0. Joe's-situation mapping (note → current problem → answer → our next step)

| Note | Joe's current problem it answers | The friend's answer | Our platform's next step |
|---|---|---|---|
| `17092026 warm_ccass_cache` | 抽 CCASS 數據：快速暖 cache 定深抓？ | warm 1.7s 只係淺摘要（Concentration+BigChanges），深度/歷史未證實；先答「要咩粒度+要唔要歷史」先至 mass-extract | 我哋已答：Turso 累積層 = 有日期嘅完整歷史；唔需要 warm 式淺抓。P0 修復（FIX-1/2/3）優先於任何大规模抽取 |
| `15092026 原webbsite係點拎DATA` | 原版 webbsite 究竟點抽數據（抽取方法權威解說） | 四角色數據流：Webb-site 源頭 → 本機一次抓 → Turso（抓一次讀多次）→ Render API（free plan 慢）或**直連 Turso 最穩** → Drive 交收 | 記錄規則：姊妹系統（RTSS 等）直連 Turso 讀；Render API 服務人類/外部查詢（見 §5b） |
| `14092026 跟DT或原Webbsite做` | 中間缺口（2025-12-25→2026-07-21）數據用邊條路抽；**DT = DisclosureTracker 財技網站**；**數據幾日內到** | 跟 DT 或原 Webbsite 做法；Drive folder 有數據；預留方法後加 2025-12 後 DATA | Phase-1：寫有 provenance 標籤嘅 import path（§7 parallel track 已記）；**數據落地前準備好** |
| `14092026 逐筆成交分析` | Longbridge 逐筆點抽、抽到幾多 | 今日限定（歷史 tape 攞唔返）+ 盤路分析法（M盤 vs 市場盤、主動買沽、簿厚度） | Phase-1 tape 日捕捉 candidate（Evidence-Cache 模式） |
| `13092026 Turso&Drive建立` | Turso 同 database（本地 SQLite/Drive CSV）嘅關係同分工 | **Turso = 查詢/累積層**（Streamlit Cloud 讀唔到 G:\、逐行 upsert、唔使開機）；**Drive = 歸檔層**（CSV 快照、dossier、規格書）；GitHub Actions 每日收市跑；events 用 INSERT OR IGNORE | 我哋 production 已經係呢個模型（§8.0 鎖定、DI 966 rows 實證）— 筆記係獨立驗證，無需改動 |

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

- **DT = DisclosureTracker**（財技網站）— the note's route is DT-based; DT roughly teaches the grabbing approach (大約教抓下的方式). Joe: **gap data lands in ~a few days** (2026-09-19 estimate).
- Contains the Drive folder link (Joe's private channel) designated for **post-2025-12 gap data** — this is the gap-closure source §7's parallel track awaited ("Joe will supply from private channels").
- DT (per the RTSS note) exports 殼股價值分析 + 六個財技事件（配股/供股/全購/合股/拆股/CB）— **these six map 1:1 onto our Phase-1 event_type values**; if DT has an API, the "only human step" in any weekly pipeline disappears. Import path (not re-derivation) is our committed posture for gap closure.
- Action queued for Phase-1: build the labelled import path (source=DT/webbsite-archive, provenance kept) when the data lands — **ETA days, be ready**; do not start Zhipu retrieval (unchanged rule).

## 5b. `15092026 原webbsite係點拎DATA` — the four-role data-flow map (file re-uploaded 2026-09-19, was empty)

The friend's teaching doc on how the original webbsite data pipeline is assembled. Four roles: **Webb-site = 原始數據源頭 → 本機 warm 抓取 → Turso（抓一次讀多次）→ Render API（free plan 慢/唔穩）或直連 Turso → 報表 CSV 經 Google Drive 交收 → Streamlit 前端**.

Key architectural lessons — and our position:

1. **"Read Turso directly, bypass the Render middleman, 最穩"** — the friend's own verdict on free-plan Render instability. Our equivalent rule to record: **the Render API (joe-ccass-api) serves humans/external queries; sibling systems (RTSS/monitor scripts) should read Turso directly** (`turso_query.py` pattern). Our mitigations for the Render side (async jobs + keepalive + Turso accumulation) are already locked in §8.0.
2. **Extraction is a LOCAL one-time job** (Webb-site → 本機 → Turso), usage is cloud-side — same shape as our 17GB Webb SQL / workstate extraction feeding Turso accumulation. Confirms: never re-run broad extraction on servers; extract locally, accumulate remotely.
3. Their status table shows warm→Turso stuck on credentials and STOCKSCAN→Turso as PART 2 — i.e., the friend is building, on their side, the same Turso-centred accumulation we already run in production (DI 966 rows).

## 6. File housekeeping

- `15092026 原webbsite係點拎DATA.md` — **FIXED 2026-09-19**: Joe re-uploaded via Desktop copy; correct 2,027-byte version now on the Drive (digested in §5b).


## 7. ADDENDUM 2026-09-19 (evening): RTSS feasibility note + full tech spec (v1.0) received

Two new docs: `13092026 自建 RTSS 式即市異動監察｜可行性與架構` and `20260912 技術規格書 自建RTSS掃描器 由零開始`.

- **Confirmed: RTSS is EOD-first** — GitHub Actions 17:00 HKT → Longbridge `screener_search` (1 call sweeps the whole market) → `candlesticks` only for qualifiers (10-day turnover 10× / >500k / mcap<10億) → **Turso 唯一真源** → Streamlit read-only. No intraday worker needed at Layer 1 (15-min delayed quotes accepted).
- **Signal honesty (both docs repeat it): 爆量 has zero excess return after controlling same-day gain (p=0.600); the tool's value = 報時 + 累積. "當日第 N 次" counter is the field worth keeping (≥3 次 historically precedes GO 報時 7.1×).**
- **Compatibility contract with our platform (the rule already adopted):** RTSS reads Turso directly. Our platform's tables are its join surface — every RTSS alert can be enriched instantly with our CCASS snapshots, announcement stream and intelligence_events (`intelligence_event_snapshots.events_json`). Our event layer's DT-mapped 財技事件 types are exactly what turns an RTSS 報時 into a 財技 story.
- Known open items RTSS must solve (their spec flags them): market-cap denominator (H shares/內資股), T+0 vs full-day turnover (store BOTH), holiday/half-day state resets.
- **Sequencing (friend's own advice, matches ours): Layer 1 EOD board first (1-2 days Codex work, zero cost), run 2 weeks against the RTSS channel for threshold alignment, only then decide on the Layer-2 always-on worker.**
- This platform (joe-ccass-platform) does NOT build the scanner — RTSS stays a separate project per §2 governance.

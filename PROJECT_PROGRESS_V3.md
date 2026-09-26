# PROJECT_PROGRESS_V3.md

# Joe CCASS Platform — Project Progress & Agent Handoff V3

> **Handoff date:** 2026-09-17 (evening, written after production branch HEAD landed)
> **Supersedes:** `PROJECT_PROGRESS.md` (V2, archived at `docs_reference_evidence/latest_reference_updates/2026-09-17_PROJECT_PROGRESS_V2_ARCHIVED.md`). On any conflict, this file wins.
> **Repository:** `Joelikecoin/joe-ccass-platform`
> **Authority branch:** `p0-runtime-api-key-fingerprint-proof` (tracks `origin/openhands/p0-runtime-api-key-fingerprint-proof`)
> **Authority HEAD:** `3324d8625d682c304e875d94867a1cc59e362da5` (2026-09-17 18:29 +0800)
> **Render:** `joe-ccass-api`, Docker runtime, latest redeploy `dep-dalvpk142hec73dsi6i0` = LIVE (commit `3324d86`)
> **Current P0:** verify live Docker Chromium + real DION E2E → then any-new-stock unified gate.
> **RESUME PHRASE (Joe pastes this to any machine/session):** `read PROJECT_PROGRESS_V3.md §12` — then follow §12's scoped task list.
> **Product definition:** changed — see §2. The platform is now a **5-Year Stock Intelligence Data Layer**, not a CCASS website.

---

## 中文摘要（給 Joe）

- 平台定位已升級：**以 5 年財技故事線為核心嘅 Stock Intelligence Data Layer**；前端 8504 只是出口之一，真正產品係餵 AI 寫 20–30 頁深度報告，最後先做 Monitor。
- Repo 有兩條分岔 branch：`main`（Gate 20，09-14，**冇 Dockerfile**）同 production branch（09-17，有 Dockerfile + 最新 DI 修復）。**一切以 production branch 為準**，合併係 P1 工作。
- CCASS 7 個月缺口已 row-level 證實：Webb 最後有效日 `2025-12-24`、Longbridge 觀察最早 `2026-07-22` → 缺口 `2025-12-25 → 2026-07-21`。**Joe 已確認：缺口日後會由其他私人途徑攞數據補上**；喺數據到手前照舊標 `DEFERRED_DATA_GAP`，禁止造假/插值。
- 朋友解題包／朋友原站嘅**權威位置係 H:\ 雲端嘅 `latest_reference_updates` 資料夾**；H: 上其他 docs_reference_evidence 子資料夾可能已過時，引用前必須核實時效。
- 注意：當前 portable workstate（selective index）**只有 dailylog + bigchanges**，冇 holdings/parthold/issuedshares → 完整快照重建喺呢個 workstate 暫時跑唔到。舊 PASS 證據仍然有效，但要還原需從 17GB SQL 重新抽取（**唔好重跑全量抽取/索引**）。
- 第一個動作唔變：驗證 live Docker Chromium → 真實 DION 00388/01810 → unseen-stock 統一 gate。

---

## 1. Relationship to prior handoffs

| Document | Status |
|---|---|
| `docs_reference_evidence/latest_reference_updates/2026-09-09_P0_8504_HOME_CODEX_HANDOVER.md` | Superseded, evidence still valid |
| `docs_reference_evidence/latest_reference_updates/2026-09-16_WEBBSITE_CCASS_ROW_PROOF_HANDOFF.md` | Superseded by the 09-17 boundary handoff |
| `docs_reference_evidence/latest_reference_updates/2026-09-17_CCASS_BOUNDARY_AND_WORKSTATE_HANDOFF.md` | **Active** — row-level boundary proof + workstate facts (§4 here) |
| `PROJECT_PROGRESS.md` (V2) | Archived in repo; still the fullest module checklist |
| `2026-09-17_PRODUCT_REDEFINITION_ROADMAP_V2.md` | **Active** — product definition + ROI order (§2, §7 here) |
| `HANDOFF_20260905.md` | Historical |

---

## 2. Product redefinition (locked by Joe, 2026-09-17)

> **A Stock Intelligence Data Layer built around a 5-year financial-engineering storyline.**
> Default lookback = 5 years (or since listing if younger). Evidence-triggered extension = up to 10 years or listing date.

The deliverable chain is:

```text
P0 DATA FOUNDATION (7 domains)
├─ Market Data (OHLCV / turnover / market cap)
├─ CCASS (current + historical)
├─ 5-Year Corporate Intelligence
│   ├─ Announcements / Corporate Actions / Share Capital
│   ├─ DI / Ownership / Major Shareholders
│   └─ Directors / Advisers / Intermediaries
├─ Fundamentals
└─ Evidence / Provenance
        ↓ DERIVED INTELLIGENCE (派貨/收貨/轉倉/爆量性質、殼價、有局無局反證)
        ↓ AI 20–30 頁深度財技報告
        ↓ MONITOR / ALERTS   (deliberately LAST)
```

Storage model (three layers):

```text
A. Persistent Time-series        CCASS / OHLCV / issued-shares snapshots
B. 5-Year Historical Retrieval   HKEX announcements / DI / circulars / annual reports / people
C. Structured Evidence Cache     verified key events, permanently stored, never re-derived
```

Key teaching-materials conclusion: VCP / RTSS / Settle / 派貨 / 收貨 / 殼價 are **Derived Intelligence** on top of the 7 domains — never new raw-data services. The 01933 vs 06890 friend reports prove the product bar: not "see the anomaly" but "classify the anomaly" (distribution vs transfer vs liquidity event vs 財技 deployment).

Monitor Engine stays out of the top-5 build order: **first understand the story, then monitor for its next chapter.**

---

## 3. Repo reality — drift corrections vs V2 handoff

Verified directly against the cloned repo on 2026-09-17:

1. **Two diverged branches.**
   - `main` HEAD = `bd84cbd` (2026-09-14, "fix: align snapshot backup wording"); carries the **Gate 20** P1 production-acceptance lock (`docs_reference_evidence/latest_reference_updates/2026-09-14_GATE20_P1_CORE_PRODUCTION_ACCEPTANCE_LOCK.md`); **has no Dockerfile**.
   - Authority branch HEAD = `3324d86` (2026-09-17 18:29); 68 commits ahead of main, 8 behind.
   - **Rule: the authority branch is the production/working truth.** Do not build on `main`. Reconciliation/merge of the 68/8 divergence is a **P1 task, deferred until the P0 gate passes.**

2. **P0-1 runtime root cause is addressed at image level.**
   `Dockerfile` now builds `FROM mcr.microsoft.com/playwright/python:v1.51.0-noble` (Chromium provisioned in image; see commit `dc9bd6a` "build: provision Playwright runtime for DION") and runs `uvicorn app.portal_8504 --port ${PORT:-10000}`. The last code commit `3324d86` is "fix: call disclosure repository save method".
   **Still unproven: the LIVE container actually launching headless Chromium and completing a real DION query.** Image-level provisioning ≠ runtime acceptance (Fail Loud).

3. **DI chain files all exist on the authority branch**: `app/sources/disclosure_interests.py` (DION at `https://di.hkex.com.hk/di/`, Playwright headless Chromium transport, fails loud as UNAVAILABLE — never silent empty), plus service/storage/tests/portal wiring.

4. **`PROJECT_PROGRESS.md` was never committed** (lived only in `Downloads/`). V3 is the first progress doc inside the repo, so both machines see the same state.

---

## 4. CCASS boundary — row-level proven facts (from the 09-17 boundary handoff)

```text
WEBB (archive row-level proof, dailylog + bigchanges):
  00388: 2007-06-26 → 2025-12-24   DAILYLOG=4563  BIGCHANGES=1289
  01211: 2007-06-26 → 2025-12-24   DAILYLOG=4563  BIGCHANGES=2351
  01810: 2018-07-09 → 2025-12-24   DAILYLOG=1840  BIGCHANGES=392
  WEBBSITE_LAST_VALID_CCASS_DATE=2025-12-24
  5Y_HISTORY_AVAILABLE=YES   10Y_HISTORY_AVAILABLE=YES

LONGBRIDGE (observed, 00388/01211/01810/06182):
  broker_holding_daily: 40 rows, 2026-07-22 → 2026-09-15, no date params, single-broker only
  LONGBRIDGE_OBSERVED_EARLIEST_DATE=2026-07-22
  LONGBRIDGE_TRUE_SOURCE_EARLIEST_DATE=NOT_PROVEN

GAP CANDIDATE: 2025-12-25 → 2026-07-21   (ZHIPU_RANGE_LOCKED=NO — do not start Zhipu retrieval yet)
CLOSURE PLAN (Joe, 2026-09-17): gap will be back-filled later from other PRIVATE channels.
Until that data arrives: keep labelling the gap DEFERRED_DATA_GAP; no fabrication, no interpolation.
```

**Do not state** that Longbridge history begins 2026-07-22 — that is an observed 40-row boundary only. Next gap work = determine the earliest authoritative date for a *complete participant-level* snapshot, **then** define the true middle gap. Closure data is expected from Joe's private channels (see above), so agents should build/preserve the import path, not hunt for substitute sources.

### Workstate caveats (critical, easy to misread)

- The current portable workstate is `webbsite_selective.sqlite` (2.6 MB; local copy `D:\WEBBSITE_CCASS_EXTRACT\`, portable copy on the NamFung Drive research pack). It contains **dailylog + bigchanges only**.
- In this workstate: `HOLDINGS_ROWS=0`, `PARTHOLD_ROWS=0`, `ISSUEDSHARES_ROWS=0` → `FULL_SNAPSHOT_RECONSTRUCTION=FAIL`, `CANONICAL_CONVERSION=FAIL`, `CHANGES_ENGINE_ACCEPTED=FAIL`.
- **Meaning:** these FAILs describe the *current extraction state*, not a disproof. The earlier PASS proofs (00388/01211/01810/00004 participant reconstruction, stake %, derived reports) remain valid historical evidence. But the reconstruction chain is **not runnable right now** until holdings/parthold/issuedshares tables are re-extracted from the 17 GB SQL member (still present: `D:\WEBBSITE_CCASS_EXTRACT\ccassData-2025-12-27- 600.sql`, logical size 17,059,800,013 bytes; archive `ccass251227.7z` on the Drive).
- The old canonical workstate `webbsite_canonical_historical_snapshot.sqlite` is **not currently on D:**.
- **Do not** redo the broad extraction or rebuild the selective index (index build took ~3621 s). Any re-extraction must be targeted at the missing tables only.
- **Do not delete** `D:\WEBBSITE_CCASS_EXTRACT`.

---

## 5. Corrected capability matrix (V2 roadmap matrix × repo reality)

The V2 roadmap matrix marked DI / Advisers / Fundamentals as MISSING. That predates the component work — corrected status:

| Domain | Status | Evidence / what is actually missing |
|---|---|---|
| CCASS current chain | **READY** | Longbridge → validate → normalize → Turso → API → 8504, production-proven |
| Changes / Big Changes / Concentration | **PASS recent / PARTIAL history** | Computation proven; historical depth limited by the gap + workstate caveats (§4) |
| Webb historical reconstruction | **PASS (evidence) / NOT RUNNABLE (current workstate)** | Prior proofs valid; needs targeted re-extraction of holdings/parthold/issuedshares to run again |
| CCASS middle gap | **DEFERRED_DATA_GAP** | Only accepted gap: `2025-12-25 → 2026-07-21`; Zhipu range not yet locked |
| HKEX Announcements | **COMPONENT_PASS** | Code + real fetch proven; 5-year production retrievability + fresh-stock gate pending |
| DI / Ownership | **COMPONENT_PASS → P0-1** | source/parser/storage/service/tests done; LIVE Docker Chromium + real DION E2E is the current first task |
| Fundamentals | **COMPONENT_PASS / PARTIAL depth** | Normalized model + real periods proven; missing NAV/Debt/Receivables/OCF/Auditor/Going-Concern depth |
| Document entities / intermediaries | **COMPONENT_PASS / PARTIAL depth** | Placing agent, offeror, underwriter, adviser, whitewash, concert parties demonstrated; no 5-year entity graph yet |
| Share capital history | **PARTIAL** | Path exists; long-range production proof incomplete |
| Officers / directors | **PARTIAL** | Current snapshot only; no historical coverage |
| OHLCV / turnover | **PARTIAL** | Service exists; 5-year production coverage unproven; derived turnover must stay labelled |
| Major shareholders history | **NOT BUILT** | No dedicated service |
| 5-Year unified event layer + Evidence Cache | **NOT BUILT** | The V2 🥇; schema defined in §7 |
| People / intermediary entity graph | **NOT BUILT** | The V2 #5 |
| Monitor / alerts | **DEFERRED by design** | Last, after the intelligence layer |

### 5.1 Friend `warm_ccass_cache` question — RESOLVED (2026-09-17)

The long-open `WARM_FILE_FOUND=NO / FINAL_CLASSIFICATION=NOT_FOUND` item is now closed with direct evidence:

- The **authoritative friend handover pack** (`CCASS_Codex_Handover_20260814.zip` in the H: `latest_reference_updates` folder) was extracted and searched in full: **zero occurrences** of `warm_ccass_cache` (or any `warm*` symbol) in code or docs.
- No authoritative document in `latest_reference_updates` mentions a warm cache either.
- The friend system's real CCASS path (per its own `TECHNICAL_ARCHITECTURE.md`, verified 2026-08-14 against packaged source): `utils/source_router.py` (mirror / hybrid / local DB / Render bridge) → `utils/fetcher.py` (**builds Webb URLs, resolves issue IDs, requests-first, optional Playwright fallback**) → parsers → `utils/snapshot_db.py` (SQLite snapshot upsert/diff/concentration). Any "instant" behaviour is local-SQLite snapshot reuse, not a hidden warm file.
- `hybrid_light` likewise does not exist in the 08-14 pack — it was only specified later in the Longbridge round-3 task spec (09-04). Timeline is consistent.

Verdict: `FRIEND_WARM_BEHAVIOR=NOT_PROVEN → ABSENT_IN_AUTHORITATIVE_EVIDENCE`. `JOE_DEEP_CCASS_ARCHITECTURE=KEEP` unchanged. Do not re-open this investigation; do not redesign Joe's CCASS layer based on a claimed faster friend warm path.
**AMENDMENT 2026-09-19 (new evidence, supersedes the "do not re-open" only as documentation):** the friend's LATER rounds did build `warm_ccass_cache.py` — per the 17/09 note it runs `hybrid_light` (`?light=1`) = Concentration + Big Changes summaries only (1.7 s because shallow), participant-level and history-date support UNCONFIRMED; fork = `cconchist.asp` (history) vs `choldings.asp` (today). Our stack has no such fork: archive layer is date-parameterized, Turso warm reads serve full history by construction. Full digest: `latest_reference_updates/2026-09-19_FRIEND_ROUND4_DIGEST_RTSS_TAPE_WARM_TURSO.md`.

### 5.2 Friend original site — live benchmark (Joe's declared standard)

Per Joe (2026-09-17): the friend solution pack is the successful example; later friend rounds added the Longbridge API (legitimate, no workaround, faster); the friend original site is **Joe's benchmark**, and Joe's platform must ultimately **exceed it**.

**Live observation (probed 2026-09-17 ~16:19 UTC):**

- UI: `https://webbsite-ccass-tool-r3ntrqvqx9w2k3xffasgwf.streamlit.app/` — **login-gated** (Streamlit private sharing). **Joe (09-17 evening): friend will NOT grant viewer access — live UI browsing is CLOSED.** `01_Reference_Website\` screenshots are **OUTDATED (per Joe)**; Joe will supply **new long screenshots** (promised 2026-09-18). Friend api_token: **friend declined to provide** — live functional benchmarking via friend API is CLOSED; openapi surface is the only current functional reference.
- API: `https://webbsite-ccass-api.onrender.com` — public, `v1.13.0`, `ok:true`. `/health` shows: **Longbridge authenticated via oauth_device_flow** (token refreshable), **`db_backend: turso`** (migrations complete), watchlists `lshape79(79) / caiji(28) / research(557)`, Google Drive service account configured, Render free-tier (cold starts; uptime was 410 s at probe).

**Friend capability surface (from `/openapi.json`) — the parity benchmark:**

```text
/api/stock            core CCASS summary (holdings/changes/big changes/concentration)
/api/stock/diff       CCASS holdings diff between two dates          <- Joe parity candidate
/api/stock/events     corporate events
/api/stock/officers   officers (optional snapshot date)
/api/stock/price      price history (Yahoo)
/api/stock/announcements  HKEX announcements (2-year lookback)
/api/stock/capital    share capital changes + buybacks
/api/screen           batch screen up to 20 codes                    <- Joe parity candidate
/api/participant      one participant's holdings across 20 codes     <- Joe parity candidate
/api/date-alignment   event date -> CCASS trade/settlement snapshot  <- Joe parity candidate (correctness-critical)
/api/longbridge/stock normalized Longbridge holdings
/timeline  /panel/broker_daily  /panel/transfers  /brief/latest  /brief/{date}  /hypotheses
/api/snapshots/export  /api/snapshot_all
/announcement/pdf     fetch + extract HKEX announcement PDF text
/admin/*              longbridge device-flow auth, watchlist mgmt, run_daily jobs, hypotheses CRUD (bearer-protected)
```

**Joe must EXCEED the friend at (per Joe's direction, the actual differentiators):** deep participant-level historical reconstruction (friend has none — mirror fetch + snapshot reuse only), 5-year corporate intelligence event layer + permanent evidence cache, DI/ownership engine, normalized fundamentals with auditor/going-concern, provenance/coverage discipline, and a unified AI research-context read model.

**Joe must at least MATCH (P1 parity candidates, friend-only today):** two-date holdings diff, participant cross-stock view, trade/settlement date-alignment service, batch screening, broker-daily/transfer panels, daily brief, hypothesis tracking with hit/miss, scheduled daily runs, PDF text extraction.

### 5.3 Friend live UI evidence (Joe's PDF `18092026朋友原站.pdf`, 21 pages, 06182) — benchmark corrections

Three findings change earlier assumptions:

1. **The friend's own browser layer is broken too.** Their data-quality warnings show `CHROMIUM_UNAVAILABLE` — Playwright Chromium fails with `libglib-2.0.so.0: cannot open shared object file` (chromium-1234 in `~/.cache/ms-playwright`), so Webb mirror Holdings/Changes fetches fall back to Longbridge MCP. **Browser-on-free-hosting fragility is the industry situation, not a Joe-specific defect.** Joe's platform must simply be the one that FIXES it (Playwright official image + correct timeout).
2. **Correction to §5.2 depth claims:** the friend DOES hold long history for some sections via the `webb-database.com` mirror (issue-based pages: `ccass/conchist.asp`, `ccass/bigchanges/issue.asp`, `dbpub/hpu.asp`): Concentration 2,131 rows (≈8.5 y daily Top5/Top10/NCIP), Price History 2,132 rows (≈8.7 y, with VWAP + Total Return + est-turnover columns), Big Changes multi-year row-level. What the friend still does NOT have: **full participant-level daily holdings history** (Holdings = current Longbridge snapshot, 105 participants for 06182, + local accumulation), DI, fundamentals depth, a unified event layer, or a permanent evidence cache. Joe's moat stands.
3. **The provenance/UX bar to match** (from the PDF): master CSV carries per-row `section / row_meaning / source / fetch_method / http_status / error_message / data_quality_warning / ccass_trade_date / settlement_date / implied dates / export_schema_version`; date-basis is annotated everywhere (Holdings/BigChanges/Concentration = settlement T+2, Changes = explicit trade date, implied dates need XHKG sessions); `SUSPECT_DENOMINATOR` auto-excludes concentration rows on share-capital effective dates; custody/warehouse-transfer detection flags pairs like KINGSTON +75 % / GET NICE −75 %; block-trade suspect flags; DT Rainbow chart with merged-price toggle; Copy-for-ChatGPT markdown; snapshot-DB backup download; Research Panel (Daily Brief / Timeline / Broker stack). 06182 live reference values (2026-09-16, Longbridge): 105 participants, largest 宏智證券 B02094 492,684,000 = 61.58 %, 金利豐 B01438 31,024,000 = 3.87 %, Top5 = 89.61 %, Top10 = 93.38 % (useful cross-check fixtures for Joe's own 06182 runs).

---

## 6. Governance (unchanged, binding)

- Workflow: `Reference → Current → Gap → Earliest Root Cause → Minimal Fix → Runtime Verify`. Clone-First: the friend/reference implementation is the Golden Master wherever real evidence exists.
- **Fail Loud, Never Fake.** Tests passed / HTTP 200 / route exists / fixture / mock / cache / fallback / UI section / `skipped=True` — none of these is completion evidence.
- Dynamic fresh-stock rule: no preload, no whitelist, no stock-specific hardcoding; a real zero-event search is `COMPLETE_ZERO_RECORDS`, not `UNAVAILABLE`.
- Timing gate: target ≤ 60 s, hard stop ≤ 90 s; every domain must land in an explicit terminal state. No infinite loading.
- Friend benchmark usage (Joe, 09-17 evening): friend packs/site are the **benchmark to exceed, NOT a dependency** — build every capability natively; consult packs only to verify a concept exists, never as a code/design crutch.
- While P0 is blocked: no UI polish, no reports, no refactor, no new features, no LLM-translator work.

---

## 7. Phase 0 work checklist (P0 — execute in order)

- [~] **0.1** LIVE runtime identity CONFIRMED 2026-09-17 (Render API, key working): live deploy `dep-dalvpk142hec73dsi6i0` = commit `3324d86`, autoDeploy off; `/health` = 200 warm (0.5 s). Chromium executable presence inside the container is **still unproven** — see 0.2 evidence.
- [x] **0.2** Real DION 00388 — **CLOSED 2026-09-18, Option A production-verified.** Historical narrative below is preserved verbatim for the record; final status: `POST /admin/disclosure-interests/job` for 00388 2y (2024-09-18→2026-09-18) = `succeeded`, **108 real rows persisted to Turso** (90.9 s). DION's own counter lists 122 for the query; the 14-row difference is surfaced honestly as `DI_DATE_WINDOW_DIFFERENCE` (DION's list counter vs per-row event-date window), never hidden. Rerun across a redeploy is **idempotent** (Turso 00388 count stays 108, ON CONFLICT upsert). Root causes found and fixed en route: (1) **the old parser matched a fabricated row shape** — real DION rows are nested `<tr>`s keyed by a CS/DA form serial in the first cell, the date column is NOT last, Long/Short share a cell, and the record counter lives in `<span id="lblRecCount">` — the old code returned `source_status:"ready"` with 0 rows against a page showing 554 records (silent-empty fail-loud violation; local repro via dumped `NSAllFormList` HTML); (2) **browser-per-page pagination blew the container CPU budget** — pager pages are stateless GETs (`&pg=N`), now fetched via plain httpx after the browser earns page 1; (3) `REQUEST_TIMEOUT_SECONDS` 90→180 via Render API (01810's real runtime of 130 s proves 90 s was insufficient). Original 2026-09-17 narrative:
  - **Earliest root cause identified:** `app/config.py:34 request_timeout_seconds: float = 12.0`; the whole DI browser flow (Chromium launch → DION page → form → search → result page) is wrapped in `asyncio.wait_for(timeout=request_timeout_seconds)`. Production Render env does NOT set `REQUEST_TIMEOUT_SECONDS` (verified from the Environment screenshot). 12 s cannot fit a cold-CPU Chromium launch + 3-page navigation. **TIMEOUT ≠ Chromium missing** (the friend's live env fails differently — missing `libglib-2.0.so.0` crashes instantly; Joe's times out).
  - **NEXT SINGLE ACTION (zero code change):** add env var `REQUEST_TIMEOUT_SECONDS=90` to Render service `joe-ccass-api` (Environment → Add → it auto-redeploys), then re-fire the same DI query. If it STILL times out at 90 s → escalate to container-level Chromium diagnosis (image `mcr.microsoft.com/playwright/python:v1.51.0-noble` should ship Chromium; then check logs).
  - **UPDATE 2026-09-17 late (90 s env applied, deploy `dep-dam23me7bikc7381ruug` LIVE):** 3 further attempts (2 warm-service) ALL cut by the edge at **exactly ~60.1 s** (`server closed abruptly` / connection unexpectedly closed). Findings: (a) Render free tier terminates HTTP requests at ~60 s — a hard edge limit, friend's site never exceeds it either; (b) on client disconnect the server task is **cancelled** — `disclosure_interests` stayed 0 rows in Turso after every attempt, so the DION flow has never run to completion; (c) whether Chromium actually launches inside the container remains **unobservable** through synchronous HTTP (Render log-retrieval API not available on this plan).
  - **Revised root cause (supersedes the 12 s diagnosis, which was real but secondary):** synchronous request/response design vs the free-tier 60 s edge limit. A DION browser flow (Chromium launch + 3-page navigation) cannot reliably finish under 60 s.
  - **Proposed minimal fix (Option A, recommended): async job pattern** — reuse the existing `/admin/longbridge/snapshot_watchlist` + `/admin/longbridge/snapshot_job/{job_id}` background-job pattern for DI: trigger → background browser fetch with 90 s budget → persist to Turso → poll job status → read rows from the API/DB. Also permanently correct product behaviour for all browser-gated sources. (Option B: install real Python locally to run the DI code directly without HTTP — proves the code path but does not fix production transport. Option C: tune/reuse one Chromium instance to squeeze under 60 s — fragile, not recommended as the fix.)
  - **UPDATE 2026-09-18 (Option A CODE LANDED, company machine):** implemented + committed — `POST /admin/disclosure-interests/job` (admin-key, stock_code + optional start/end, default 5-year lookback) → background `asyncio.create_task` DION fetch (budget = `REQUEST_TIMEOUT_SECONDS` + 15 s) → persist via existing service/repository → `GET /admin/disclosure-interests/job/{job_id}` poll (state succeeded/unavailable/error + filing_count + persisted_rows from DB + warnings) → `GET /api/v1/stocks/{code}/disclosure-interests/persisted` reads stored rows without touching DION (fail-loud `NO_PERSISTED_ROWS`). Storage: `DisclosureInterestRepository.count_rows/load_rows`. Tests: `tests/test_disclosure_interests.py` 12/12 green + portal/daily-snapshot regression 32/32 green (local venv, Python 3.12). 3 pre-existing failures in `test_history_storage/test_source_status_api` reproduce identically on clean HEAD `ab76861` (company-machine environment issue, NOT caused by this change). **Live Render verification still pending** (see §12).
- [x] **0.3** Real DION E2E for `01810` — **CLOSED 2026-09-18, production-verified.** Job `9ab4b79e…` = `succeeded`, **230 real rows persisted** (130.1 s, 5 result pages via httpx pager). Independently verified: Turso `SELECT stock_code, COUNT(*), MIN(event_date), MAX(event_date)` = `01810 | 230 | 2024-10-04 | 2026-09-03`; `GET /api/v1/stocks/01810/disclosure-interests/persisted` reads back `ready / 230 / "HKEX DION (persisted)"`, top row `CS20260908E00043 BlackRock, Inc.` matches the live DION site. Zero warnings — DION counter (230) matched collected exactly. Local wide-window check: 00388 2007→2026 parsed 347 real rows incl. 2026 filings, confirming parser generality.

**Production DB baseline (Turso, verified live 2026-09-17 via libSQL HTTP API — connection + auth working):**

```text
stocks=12  ccass_snapshots=24  ccass_holdings=6735  announcements=274
disclosure_interests=0   fundamentals=0   document_entities=0
raw_provenance=199  source_errors=0
```
This is `PREEXISTING_ROWS_BY_DOMAIN` for the 0.4 unseen-stock gate. Tables present include `disclosure_interests`, `fundamentals`, `document_entities` (all at 0 rows — consistent with component-pass-but-not-production-proven).
- [x] **0.4** **GATE PASSED 18/18 — RE-RUN 2026-09-19 on company machine, stock = 02020 (ANTA SPORTS)**, `PREEXISTING_ROWS_BY_DOMAIN` all zeros measured first. All FIX-1/2/3 fixes exercised live: **CURRENT_CCASS** (snapshot 2026-09-18, 241 holdings), **CONCENTRATION** (evidence route, 241 participants), **CHANGES/BIG_CHANGES/OHLCV** (portal bundle 826KB/18.9s, all sections), **UNIFIED_EVIDENCE_PACKAGE** (same bundle), **ANNOUNCEMENTS 117 rows via async job**, **DI 25 rows via async job** (2-row DION-counter difference honestly labelled, persisted route ready/25 after redeploy), **SHARE_CAPITAL 25 rows ready**, **OFFICERS 5 ready**, **CORPORATE_EVENTS** (stock-events ready + timeline 37 events), **FUNDAMENTALS PASS-with-label** (partial: 2 periods extracted with real figures; Anta's 224+-page reports correctly skipped via DOCUMENT_TOO_MANY_PAGES/RUN_BUDGET warnings), **INTERMEDIARIES + WHITEWASH_CONCERT PASS-with-label** (3 documents attempted for 02020, 0 entities — genuine absence; extraction engine production-proven on 02318 with 9 rows/3 types incl. the Morgan Stanley/Lufax offer), **PROVENANCE + COVERAGE** (every domain landed in an explicit labelled terminal state — honest zeros counted per §6), **CCASS_MIDDLE_GAP DEFERRED** by design. Persistence proven: redeploy restart + second queries identical. Original 2026-09-18 first run (02318, 14/3/1) drove the FIX-1/2/3 work above.
  - Backlog from the re-run (non-blocking): document-entities `NO_ENTITIES_EXTRACTED` warning when docs parse but yield no labels; fundamentals >140-page reports belong in the async pattern later.
  - **PASS (14):** CURRENT_CCASS (Longbridge snapshot 2026-09-17, 357 holdings persisted), CHANGES + BIG_CHANGES + OHLCV_TURNOVER (portal bundle sections), CONCENTRATION (evidence route: 357 participants, snapshot_date must be the CCASS settlement date, not today), ANNOUNCEMENTS (2y: 236 rows ready), SHARE_CAPITAL (2y: 24 rows ready), OFFICERS (6 ready), CORPORATE_EVENTS (stock-events ready) + CORPORATE_TIMELINE (2y: 52 events), **DI (628 real rows in Turso via 4 × 6-month windows: 110+174+147+197, upsert-dedup exact vs local 628; latest CS20260918E00041 BlackRock 2026-09-15)**, PROVENANCE (raw_provenance 199→202; per-row provenance on DI rows), COVERAGE (every domain landed in an explicit terminal state — none silent), UNIFIED_EVIDENCE_PACKAGE (portal page `/?code=02318` = 835KB bundle in 29.1s, all sections), CCASS_MIDDLE_GAP (labelled DEFERRED_DATA_GAP as designed).
  - **FAIL (3 domains, 2 root causes):** FUNDAMENTALS + INTERMEDIARIES + WHITEWASH_CONCERT — their sources read **hardcoded per-stock document whitelists** (`HKEX_FUNDAMENTAL_DOCUMENTS`, `DOCUMENT_ENTITY_SPECS`): unseen stock → empty tuple → `unavailable, 0 documents attempted, empty warnings`. Direct violation of §6 dynamic fresh-stock rule. Fix = dynamic HKEXnews document discovery layer (FIX-1/FIX-2 below).
  - **Capacity findings (0.5):** ANNOUNCEMENTS 5y and CORPORATE_TIMELINE 5y crash the free container (single 10k-row HKEXnews payload → OOM; 2y windows fine); a single DI pull spanning ~13 pages also crashed the container — 6-month windows are the safe unit today. Also: Playwright strict-mode (`List of all notices` link rendered TWICE on multi-block issuers like 02318) was fixed by `.first` (commit 4fcc78a); job records now carry `timeout_budget` + effective `request_timeout_seconds` (180 confirmed).
  - **Persistence proven the hard way:** 02318 data survived ≥3 unplanned container crashes + 1 clean redeploy; second queries after redeploy identical (DI persisted route ready/628; concentration 357).
- [ ] **0.5** Scoped fixes from the 0.4 run, in order: **FIX-1 dynamic fundamentals — LANDED + production-verified 2026-09-19** (commits `36859ff`→`88a8357`): whitelist `HKEX_FUNDAMENTAL_DOCUMENTS` DELETED; discovery walks the stock's announcement stream, title-classifies reporting documents (ranked backups per period), year-sanity period derivation, budgets (45s run / 140 pages / 25MB / 6 attempts). **Production: 02318 ready 4 periods with real figures; 00388/02020/00941 local E2E green.** Known limits recorded per row: insurer phrasing partially covered (02318 fields 2-3), occasional wrong-scale captures possible (label-parser brittleness — every value carries source_document provenance). **FIX-3 step 1 — ADMIN ASYNC JOB PATTERN LANDED + production-verified 2026-09-19** (commits `64b9d0d`+`0df23a5`): `POST /admin/fundamentals/job` + `POST /admin/announcements/job` (750-day window ceiling) following the DI job infra. **Acid test: 00941 China Mobile — the issuer that 502-crashed the sync container twice — now completes via async job: fundamentals 4 periods in Turso (52s), announcements 196 rows in Turso (36.5s).** **REMAINING:** fundamentals deep-parser refinement (insurer labels, wrong-scale guards — non-blocking, values provenance'd); optional: portal UI/`/api/v1` surfaces for job triggers. **FIX-2 — LANDED + production-verified 2026-09-19 (commit `5a4de72`): `DOCUMENT_ENTITY_SPECS` whitelist DELETED**; discovery title-classifies corporate-action documents from the announcement stream (general offers incl. mandatory/cash/composite, whitewash, rights issues, placings, underwriting, circulars) with the same capacity discipline; the `_extract_rows` regex engine is unchanged. **Production: 02318 = partial, 9 entity rows, 3 entity types in Turso (offeror `Ping An Insurance (Group)`, financial adviser `Morgan Stanley Asia Limited` — the Morgan Stanley mandatory cash offers for Lufax); 00941 = honest zero (`NO_ENTITY_DOCUMENTS_DISCOVERED` — correct COMPLETE_ZERO_RECORDS behaviour).** This closes the INTERMEDIARIES + WHITEWASH_CONCERT gate FAILs (whitewash/concert rows extract whenever such documents exist; genuine absence is a labelled zero). Then re-run this same 0.4 gate until 18/18 (middle gap stays DEFERRED by design). **Pack-verified answers stored at `docs_reference_evidence/latest_reference_updates/2026-09-18_FRIEND_PACK_ANSWERS_FOR_FIX123.md`**.
- [ ] **0.5** Fix the earliest failing non-gap dependency; re-run the same gate until it passes.
- [ ] **0.6** (post-gate, P1) Reconcile `main` ↔ authority branch (68/8 divergence); fold Gate 20 P1 work with this line.

**P0 parallel track (independent, from the 09-17 boundary handoff):** determine the earliest authoritative date for a complete participant-level snapshot from Joe sources / Longbridge; only then lock the gap range. Do not fabricate or interpolate. **Joe will supply the missing middle period from other private channels later** — when it arrives, the task is a clean import into the persistent time-series layer (source-labelled, provenance kept), not a re-derivation.

---

## 8. Phase 1 build order (V2 ROI, locked)

### 8.0 Hard constraint: ZERO BUDGET (Joe, 2026-09-17 evening — binding)

> The whole platform must be built without paying. (The friend also never paid successfully — and still reached v1.13.0, which proves the free path works.)

Consequences (all design must respect these):

- **No Render Starter / persistent disk / background worker.** The 09-08 architecture doc's "US$7 Starter + 1 GB disk" suggestion is REJECTED.
- **Persistence = external free-tier DB.** Turso (already the production DB) is the accumulation layer — this also resolves the "SQLite wiped each deploy" single-point-of-failure for free. Watch Turso free-tier quotas as snapshot volume grows.
- **Scheduling = GitHub Actions scheduled workflows + keepalive pings** (the friend's own repo ships exactly this: `.github/workflows/daily_snapshot.yml` + `keepalive.yml` in the 08-14 pack — proven zero-cost pattern); external cron (e.g. cron-job.org) also acceptable.
- **Cold starts remain** — keepalive mitigates; morning-brief jobs must tolerate 30–60 s cold start.

1. 🥇 **5-Year Historical Corporate Intelligence Engine** — unify announcements / corporate actions / share capital / DI / major shareholders / directors / advisers into one event layer with temporal identity + permanent Structured Evidence Cache. Event schema:
   `event_type, announce_date, effective_date, shares_before, shares_after, price, ratio, discount, counterparty, beneficial_owner, placing_agent, adviser, source_document, confidence`.
2. 🥈 **DI / Ownership Engine** — DION rows → 5-year ownership timeline (turns CCASS inference into verified fact; cf. 01933 / Chance Talent).
3. 🥉 **CCASS Historical Gap Closure** — after the authoritative boundary is determined (§7 parallel track).
4. **Financial Fundamentals Layer** — Revenue / Profit / NAV / Cash / Debt / Receivables / OCF / Auditor / Going Concern; answers "why did the company have the motive".
5. **Historical People / Intermediary Entity Graph** — who entered/left when, and with which brokers/financial advisers/placing agents they co-occur.
6. **Monitor / Alerts — last.**

Explicitly **stopped** (not P0, do not spend time): Rainbow visuals, Excel/download expansion, 1:1 UI clone, standalone VCP/Cup/Supertrend pages, tick/Level-2 history, AI report formatting, per-strategy databases, another CCASS persistence architecture.

---

## 9. Machines, environment & two-computer sync

**Machine A (this machine, Joe Lau):**
- Repo: `C:\Users\Joe Lau\.zcode\workspace\default\joe-ccass-platform`, branch `p0-runtime-api-key-fingerprint-proof` tracking origin.
- Local `.env` (gitignored) now holds **working** `RENDER_API_KEY` (Render API verified 2026-09-17: services + deploys readable) and `TURSO_DATABASE_URL`/`TURSO_AUTH_TOKEN` (production DB verified live). NOTE: `.env` values pasted from Windows Notepad carry CRLF — strip `\r` before using (`tr -d '\r'`).
- Friend live UI long screenshots: `Desktop\18092026朋友原站.pdf` (digestion → §5.3).
- `D:\WEBBSITE_CCASS_EXTRACT`: 17 GB Webb SQL member + `webbsite_selective.sqlite` (2.6 MB). **Do not delete; do not re-extract broadly.**
- `Downloads\PROJECT_PROGRESS.md` (V2, archived into repo) + Longbridge round-3 task spec (background for Longbridge auth / dual-denominator / source-label rules).

**Cloud drive (NamFung Drive, H: mounted on Machine A):**
- Webb research pack incl. `ccass251227.7z` and the portable selective index (`WEBBSITE_CCASS_WORKSTATE`).
- **Reference authority for the friend solution pack / friend original site (per Joe, 2026-09-17 evening):**
  `H:\NamFung Drive\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\docs_reference_evidence\latest_reference_updates\`
  Contents and roles:
  - `CCASS_Codex_Handover_20260814.zip` — friend system source pack; **searched 2026-09-17: no `warm_ccass_cache`, no `hybrid_light`** (see §5.1).
  - `01092026JOE CCASS PLATFORM P0 ROOT CAUSE LOCK Owner Objective.md` — Webb-chain P0 dependency order (pre-Longbridge era); the "no fixing higher layers while lower layers fail" rule stays binding even where the source choice has since moved to Longbridge.
  - `06092026Render + Longbridge + Webb-site mirror + AI 每朝分析」的完整資料架構.md` — three-layer design input for Phase 1: Longbridge = daily latest; Webb mirror = history; Render + SQLite = accumulation. **Flagged biggest single point of failure: Render free tier has no persistent disk (SQLite wiped each deploy)** — its paid fix is REJECTED by the zero-budget rule (§8.0); the free fix is Turso-as-accumulation + GitHub Actions scheduling. The `/brief/latest` / `/panel/broker_daily` endpoint concepts remain valid Phase 1 design input; not locked policy.
  - `01092026…代碼審查報告(朋友原站回覆).md`, `29082026_朋友原站AI經github提供參考….md` — friend original-site AI replies.
  - `04092026mcp.longbridge.com 嘅原始碼用途.md`, `claude_CODEX任務規格書_…_20260904.md` — Longbridge/MCP background.
  - `WEBBSITE_CCASS_WORKSTATE\` — portable selective index.
- **Other H: `docs_reference_evidence` subfolders (`00_/01_/02_/03_/04_`, `Archive_legacy_solution_packs`, `02_Friend_Architecture`) may be OUTDATED** — verify recency before citing them; when a conflict arises, `latest_reference_updates` wins.

**Render (production):**
```text
SERVICE=joe-ccass-api        SERVICE_ID=srv-dads94740ujc73cpdktg
URL=https://joe-ccass-api.onrender.com
BRANCH=openhands/p0-runtime-api-key-fingerprint-proof
COMMIT=3324d8625d682c304e875d94867a1cc59e362da5
RUNTIME=Docker  DOCKERFILE=./Dockerfile
LATEST_REDEPLOY=dep-dalvpk142hec73dsi6i0  STATUS=LIVE
```

**Two-computer sync rule (binding):**
1. This file is the single source of truth; keep it committed on the authority branch.
2. Before starting work: `git pull`.
3. After finishing each checklist item: tick the box, add one line of evidence (commit/deploy/probe result), `git commit` + `git push`.
4. Never leave progress only in a local copy or a chat log.

---

## 10. What agents must NOT do

Everything in V2 §13 still applies, plus:

- Do not build on `main` or merge it into the authority branch before the P0 gate passes.
- Do not treat the Playwright-based Dockerfile as proof Chromium works in production — only live runtime evidence counts.
- Do not claim Longbridge coverage starts 2026-07-22; it is an observed boundary, `TRUE_SOURCE_EARLIEST_DATE=NOT_PROVEN`.
- Do not start Zhipu retrieval before the gap range is locked (gap closure will come from Joe's private channels; agents build the import path, not substitute sources).
- Do not re-open the `warm_ccass_cache` investigation — resolved 2026-09-17 (§5.1): absent from the authoritative friend pack.
- Do not cite H: subfolders outside `latest_reference_updates` as current reference authority (Joe: they may be outdated).
- Do not redo the 17 GB extraction or rebuild the selective index.
- Do not read the selective-index FAILs as disproof of the earlier Webb reconstruction proofs.
- Do not start the Monitor engine before the intelligence layer exists.

---

## 11. Definition of Done

> A normal user enters a real HK stock code into the 8504 product — even one never queried before — and receives trustworthy Reference-equivalent data quickly: persistent across reload/restart, second snapshot derivable, Changes / Big Changes / Concentration derived from the same chain, **and a 5-year (listing-bounded, evidence-extendable to 10 years) corporate intelligence storyline** suitable for AI 20–30-page financial-engineering analysis — with every fact provenanced and every gap explicitly labelled.

No preload, no fixtures, no prior history, no manual imports, no stock-specific code, no fake fallback data.

---

## 12. End-of-day handoff (2026-09-17 night) — NEXT SESSION STARTS HERE

```text
JOE_STATUS=AWAY 2026-09-18 (authorized one-shot permission accept; agent worked unattended)
OPTION_A_ASYNC_DI_JOB=PRODUCTION-VERIFIED 2026-09-18 — 0.2 + 0.3 both CLOSED (see §7 for evidence)
ALL_WORK_PUSHED_THROUGH=8e2aa34 (+ this docs commit)
RENDER_DEPLOY=dep-damhudbm8hqs73d7ej3g LIVE = commit 8e2aa34; REQUEST_TIMEOUT_SECONDS=180 (raised from 90 — 01810 needs 130 s real)
COMPANY_MACHINE_REPO=C:\Users\Joe Lau\.zcode\workspace\default\joe-ccass-platform (branch p0-runtime-api-key-fingerprint-proof; real Python 3.12; venv at ..\.venv-joe-ccass outside the repo; push.default=upstream so plain `git push` works; Drive mounts as G:\ here, H:\ on home machine)
COMPANY_MACHINE_ENV=.env created 2026-09-18 (RENDER_API_KEY + TURSO_DATABASE_URL + TURSO_AUTH_TOKEN + API_KEY), CRLF-stripped, all four verified live
CLOUD_MIRROR=(home H:) H:\NamFung Drive\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\PROJECT_PROGRESS_V3.md / (company G:) G:\我的雲端硬碟\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\PROJECT_PROGRESS_V3.md  (convenience copies; the git repo stays the single authority)
NOTE: DI cancellation raised and REJECTED for now (2026-09-18 morning): friend has no DI at all; plan ladder already succeeded at rung 1 (async job) — no need for the GitHub Actions fetcher rung.
NOTE 2026-09-18: company machine shows 3 pre-existing test failures (test_history_storage ×2, test_source_status_api ×1) that reproduce identically on clean ab76861 — environment-specific, not caused by new work, not blocking.
LESSON 2026-09-18: the original DI parser matched a fabricated HTML shape and returned ready+0 rows against a 554-record page — regression fixtures must be built from REAL upstream dumps, never invented markup. `debug_dion.py` (workspace root, outside repo) reproduces the live flow with step dumps.
```

**Next session's task — P0 COMPLETE (0.4 gate 18/18 on 02020). PHASE 1 🥇 v0 IS LIVE (2026-09-19) — continue the event layer:**

**REMAINING WORK CHECKLIST — 2026-09-19 NIGHT PROGRESS (home-machine session, autonomous; original 12-item list from the company machine's evening handoff, items kept for traceability):**

```text
ITEM_1 (02318+00941 股本持久化) = BLOCKED-CAPACITY — 3 attempts each; heavy-issuer share-capital jobs run >10 min and appear to OOM-crash the free container (multiple 502s around them); Turso still 0 rows for 02318/00941. NEW BACKLOG: windowed/segmented share-capital persistence (or lighter document set) for heavy issuers. Retry solo after the queue drains.
ITEM_2 (證據股 2021-2024 回填) = RUNNING — 42-job detached queue (home machine: bash script jobs_queue.sh; results in /tmp/job_results.txt of Machine A Git-Bash). VERIFIED LANDING: 02020 DI 89 rows (earliest 2021-04-20, was 25), 02318 announcements 551 rows (5y, was 236 — includes the first corporate-timeline job's persisted windows). Queue drains automatically; each trigger is health-gated.
ITEMS_3-9 (code) = DONE + DEPLOYED LIVE (ecd63d2 = deploy dep-danb2f740ujc73bbb1v0):
  - 3: NO_ENTITIES_EXTRACTED warning ✓
  - 4: /console job trigger panel (admin key input + 7 buttons + 10-min poll) — VERIFIED LIVE
  - 5: fundamentals parser v3 (insurer labels Insurance/Operating revenue; _resolve_unit thousand/billion + SCALE_AMBIGUOUS_UNIT; SCALE_SUSPECT revenue-vs-net-assets cross-check) ✓
  - 6: document-entities cover-page fallback (title-agnostic recent PDFs ×3, COVER_PAGE_FALLBACK_ATTEMPTED) ✓
  - 7: POST/GET /admin/corporate-timeline/job (5y window, internal ≤750d sub-windows, events in job result) — route VERIFIED LIVE; first run lost to a container crash → re-run once the queue drains
  - 8: GET /api/v1/stocks/{code}/report-draft — VERIFIED LIVE (02318: 23.7KB, 8 chapters, 7 【AI 分析位】slots, every fact provenanced)
  - 9: GET /api/v1/intermediary-graph (cross-stock nodes + same-document co-occurrence edges) — VERIFIED LIVE (real nodes: Morgan Stanley/Lufax adviser, Ping An offeror)
ITEM_10 (branch 對齊) = DONE — merge 3d478fc reconciled main (Gate 20 + CI) into authority; main fast-forwarded to authority HEAD; divergence 0/0; workflows identical on both branches.
ITEM_11 (API key 換新) = PENDING BY DESIGN — the queue uses the 64-zero key; rotate ONLY after it drains: ① Render env API_KEY (Render API) ② both machines' .env ③ GitHub secret API_KEY (web UI or gh admin).
ITEM_12 (3 個測試失敗根查) = DONE — they were NOT company-env-specific: 7 stale/broken tests fixed (ecd63d2): history_storage migrations 1-10; registry/status tests updated for the 4th webbsite_archive source; accumulation auth test now monkeypatches get_settings (unconfigured → 503, configured-no-key → 401); officers service no longer falls back to a live Webb source on explicit "pending" state (test determinism). Full suite at home: 549 passed / 26 failed — the 26 are ALL test_streamlit_ui, pre-existing at 18cb04a (NOT from the merge): requirements floats streamlit>=1.40,<2 and home pulled 1.64.0; the company venv is older. Fix = pin the version (low priority).
NEW_FINDINGS: (a) heavy-issuer share-capital jobs crash the free container (see ITEM_1); (b) the ~60s Render edge only bites synchronous HTTP — async jobs run 90-180s+ fine; (c) captured document-entity names can be noisy ("s should be construed accordingly. Ping An…") — parser refinement stays on the backlog; (d) home machine now has REAL Python 3.12.10 (winget) + venv at C:\Users\Joe Lau\.zcode\workspace\default\.venv-home (respx/pytest-asyncio added) — full local test runs now possible on BOTH machines.
NEXT_SESSION: ① check /tmp/job_results.txt + Turso DI/announcement counts per evidence stock; ② retry share-capital 02318/00941 SOLO (accept a possible crash, or defer to the new windowed backlog item); ③ re-run one corporate-timeline 5y job to verify events; ④ item 11 rotation (three places); ⑤ V3 update + push + both Drive mirrors (H: home, G: company).

### AUTONOMOUS SESSION COMPLETE 2026-09-20 afternoon (Joe away; full authorization ran)

1. **Backfill DRAINED (04:09Z)** — every evidence-stock window now persisted. Turso final: DI 00388=108 / 01810=230 / 02020=89 / 02318=1307 / 00256=28 / 00397=11; announcements 02318=551 / 00256=148 / 00397=209 / 02020=117+95+108=320. 00256/00397 DI windows with filing_count:0 are genuine small-cap zeros (labelled, idempotent-retried, same result).
2. **Share-capital job = CONFIRMED SYSTEMIC CAPACITY LIMIT** — 02318 ×4, 00941 ×2, 08283 ×1 attempts: every run >8-10 min, no persistence, container restarts. NOT issuer-specific. **NEW BACKLOG (design work): windowed/segmented share-capital persistence** (e.g., per-year sub-jobs or a lighter document subset), then backfill 02318/00941/00256/00397/08283.
3. **Fresh-stock gate on 08283 中食民安控股 (genuinely unseen, Turso pre-check 0/0/0/0) — 4/5 domains PASS with real data from stock code alone:** DI 7 filings persisted ✓, announcements 92 ✓, fundamentals 4 periods/4 documents ✓, intelligence-events snapshot ✓; fast page rendered all 7 sections. share-capital = the one known capacity FAIL (documented above).
4. **ITEM 11 API KEY ROTATION = DONE + VERIFIED LIVE.** API_KEY rotated from 64-zeros to a 64-hex secret via Render API (full env-var list PUT — all 8 vars preserved incl. REQUEST_TIMEOUT_SECONDS=180; ADMIN_API_KEY was already a real value, untouched). Old key → 401, new key → 202 (live-verified). Home `.env` updated. GitHub secret `API_KEY` ALSO ROTATED via API (updated_at 2026-09-20T05:18:37Z, using the stored git credential PAT — verified). Only remaining: company machine `.env` API_KEY line (no automation runs from there — update next visit).
5. Everything pushed (both branches) + Drive mirror refreshed.

### FRONTEND ACCEPTANCE OVERHAUL 2026-09-20 (Joe's directive: frontend speed first, backend data unchanged)

**Joe's acceptance standard:** frontend loads fast; every domain complete except the 7-month gap; he trims frontend features; backend data sources untouched.

- **`/` is now the FAST persisted overview** — parallel evidence-cache reads (asyncio.gather + to_thread), Top-N rendering (events latest 30, holdings top 15, timeline top 10 filers), Deep Refresh job panel on-page, nav links to everything else. **Measured live on 02318 (heavy stock): 35.4s/863KB → 4.8–6.2s/11KB (cold first hit 9.4s).** All 7 sections render.
- **The old full live product moved to `/full?code=`** (unchanged ~35s bundle, all params) — nothing deleted, only re-routed.
- report-draft / research-context / full JSON endpoints remain API-only links from the fast page (AI consumption surface, not the human landing).
- Remaining known costs: warm events snapshot read ~1.5s (1MB events_json parse) is the floor of the current page; further speedup (e.g., latest-window-only read) is optional polish.

### A5 DESIGN FINALIZED 2026-09-20 late night — awaiting Joe's verification tomorrow

Joe iterated the terminal design through 5 rounds (browser-shown each time). **A5 final design (`outputs/mockup_a5.html`, commit 92db4df/e4b65a6):** light detailed theme · 2-col layout · functional price chart with 1M/3M/6M/1Y switcher (verified live-switching) · KPI strip: 市值/最新收市/CCASS快照/Top5/Top10 92.3%/DION申報人/業績期/現金結餘 (情報事件 KPI removed per Joe) · **DT-style stacked CCASS rainbow with broker legend + CCASS IDs + 分段解讀 box** · 轉倉偵測 card (same-day 一減一增 pairs) · 資金流向 with 7D-5Y selector · 異動盤 (大手/連續/對盤, tape-capture caveat labelled) · VPVR with 1週→3年 selector + POC/VA · 港交所公告 card with原生繁體 titles + PDF links · 資產負債表/損益表 (AAStocks-style, v4 target) · 相關人物 (細價股人物主導) · 下載 AI 數據源 + Excel/CSV hub · all components 10 rows.
**Tomorrow: Joe verifies A5 → on approval, wire real data into /terminal following this exact design (all pipelines ready: price endpoint ✓, announcements 551 ✓, DI movements ✓, rainbow = snapshot walk + Webb archive import).**
### JOE INTELLIGENCE TERMINAL DELIVERED 2026-09-20 night (`/terminal?code=`)

Joe granted unlimited creative license ("以你的創作 不用限制"). Delivered `app/terminal.py` (APIRouter, imported at the bottom of portal_8504): a **22-component persisted terminal** — ① CCASS Top15 with % bars, ② concentration trend sparkline (walks `previous()` snapshots; grows as daily accumulation lands), ③ snapshot-diff 持倉變動, ④ 大額變動 ≥0.5%, ⑤-⑨ coverage/source cards, ⑩ ownership timeline, ⑪ 90-day DI highlights, ⑫ events stream with type pills + confidence badges, ⑬ intermediary network, ⑭ fundamentals table, ⑮ derived pressure signals (labelled), ⑯ company/next dates, ⑰ 股本故事 + dilution, ⑱ inline report-draft loader, ⑲ research-context downloads, ⑳ raw previews links, ㉑ provenance & coverage declaration, ㉒ downloads hub. Browser-verified live on 02318 (29.5KB, KPI strip: 09-18 / 72.1% / 23 filers / 1,212 events / 4 periods).
Polish notes (non-blocking): 覆蓋快照 KPI shows 0 — `available_dates` returned empty, signature needs review; concentration sparkline has only 2 points until daily accumulation grows; fullPage screenshot artifact (4× header repeat) is a capture glitch — live HTML verified non-duplicated.
- **ADDENDUM 2026-09-20 late night (Joe feedback: 加港交所公告 + 睇唔到全貌):** ① dedicated 港交所公告 card added (persisted announcements, latest 15 with PDF links, count + coverage note; 02318 = 551 份) — closes the friend-site parity gap; ② sticky-style jump navigation bar added under the KPI strip (anchor per component) — solves "can't see the whole page"; ③ two deploy roundtrips to land (gather item + import missed in first pass — lesson: scripted multi-edit must verify each anchor applied).
- **DESIGN PASS 2026-09-20 evening (Joe picked option A — light professional):** `/` redesigned — blue gradient header, KPI strip (快照日/參與者/Top5%/申報人/事件/業績期), card grid with collapsible sections, red/green movement coding, confidence badges, restyled landing. Browser-verified live on 02318: 357 參與者 / Top5 72.1% / 23 申報人 / 1,212 事件 / 4 業績期, all cards rendering real data.
- **IMPORTANT DISCOVERY:** `/full`（35s 全包）已經係一個專業級淺色儀表板（"Joe Visual Portal"：Fetch Summary 卡、Price & Turnover 圖表、章節 pill 導航、EN/繁中切換、下載區）— earlier sessions only curl-timed it and never viewed the UI. Two-surface product now: `/` = ≤5 秒快總覽（日常驗收面）；`/full` = 完整即時參考產品（深度/圖表/下載）。Optional future: rebuild /full sections on persisted reads to keep its rich UI at fast speed.
- Commits: `7d1d76d` (fast overview + /full split) + accessor fix; deploys `dep-danktu740ujc73c9m3og` line LIVE. Portal tests 24/24 green.
- **Backfill relaunched on the new container** (runner + supervisor detached on Machine A; queue file /tmp/job_queue.txt, results /tmp/job_results.txt): remaining 19 windows draining automatically; supervisor relaunches the runner if it dies; done windows auto-skipped.

### ⭐ MORNING DECISION QUEUE（更新 2026-09-22 深夜）

1. **D 槽合併** = Joe 自己照 docs/TASK_D_MERGE_C.md 做 DiskGenius（步驟 1-3 已完成 ✓，淨低 DiskGenius GUI + 重啟驗證）；完成後叫 ZCode 做最終 partition 驗證
2. **A5 實裝 = 暫緩**（Joe 考慮更好介面方向）
3. Webb 17GB 導入 = 已完成 ✅（19 年數據庫建成，見下方 milestone）

### SHUTDOWN HANDOFF 2026-09-20 01:30 HKT (superseded by the section above — kept for the Turso state snapshot)

Backfill runners were stopped cleanly. **Turso state at shutdown (verified):** DI — 00388=108, 01810=230, 02020=89 (2021-04-20→2026-05-15), 02318=1307 (2021-01-05→2026-09-15), 00256=11 (2022-01-05→2022-06-10); announcements — 00388=274, 00941=196, 02020=117, 02318=551; share_capital_history — 02020=25 only.

**Remaining backfill windows (19 async jobs; run from ANY machine with bash+curl — trigger then poll `/admin/<domain>/job/{id}` ~3-6 min each; skip nothing, all are upsert-idempotent):**

```bash
BASE=https://joe-ccass-api.onrender.com
KEY=0000000000000000000000000000000000000000000000000000000000000000   # 64 zeros until item 11 rotation
run(){ curl -sS --max-time 30 -X POST "$BASE$1&key=$KEY"; echo; sleep 210; }
# DI 00256 remaining 4 windows
for w in "2023-01-01 2023-06-30" "2023-07-01 2023-12-31" "2024-01-01 2024-06-30" "2024-07-01 2024-12-31"; do set -- $w; run "/admin/disclosure-interests/job?stock_code=00256&start_date=$1&end_date=$2"; done
# DI 00397 all 8 windows
for w in "2021-01-01 2021-06-30" "2021-07-01 2021-12-31" "2022-01-01 2022-06-30" "2022-07-01 2022-12-31" "2023-01-01 2023-06-30" "2023-07-01 2023-12-31" "2024-01-01 2024-06-30" "2024-07-01 2024-12-31"; do set -- $w; run "/admin/disclosure-interests/job?stock_code=00397&start_date=$1&end_date=$2"; done
# ANN 6 windows
for CODE in 00256 00397 02020; do run "/admin/announcements/job?stock_code=$CODE&start_date=2021-01-01&end_date=2023-01-20"; run "/admin/announcements/job?stock_code=$CODE&start_date=2023-01-21&end_date=2024-12-31"; done
# then solo, watching for container crashes (502 → wait for /health 200 before continuing):
run "/admin/share-capital/job?stock_code=02318"
run "/admin/share-capital/job?stock_code=00941"
run "/admin/corporate-timeline/job?stock_code=02318&start_date=2021-09-20&end_date=2026-09-20"
```

After the 19 jobs: verify Turso counts grew (00256 DI should stay tiny — genuine small-cap; 00397 expect real rows; ANN each stock +2021-2024 rows), then item 11 rotation, then V3 update.
```

Original 12-item list (2026-09-19 evening handoff, company machine): 1 share-capital job calls 02318+00941; 2 evidence-stock DI/announcements 2021-2024 backfill; 3 NO_ENTITIES_EXTRACTED warning; 4 console job buttons + admin key; 5 fundamentals parser v3; 6 entities cover-page fallback; 7 corporate-timeline 5y async; 8 AI report generator v1; 9 entity-graph seed; 10 branch alignment; 11 API key rotation; 12 company-machine test failures.
1. **DONE 2026-09-19 — Unified Event Layer v0** (commits `c6eb614`→`e47b838`, Render LIVE): `intelligence_events` (MIGRATION_8, §8 row schema) + `intelligence_event_snapshots` evidence cache (MIGRATION_9, one payload_json upsert per coverage window — per-row remote writes starved the free container, 650 HTTP statements → container death; snapshot = 1 upsert, 5.9s for 637 events). `IntelligenceEventsService` derives events from persisted DI (confidence=**official**) + document-entity stores (confidence=**extracted**), upserts idempotently, serves via `GET /api/v1/stocks/{code}/intelligence-events` (4.3s sync read of 637 events) and builds via `POST /admin/intelligence-events/job`. **02318 live: 637 events (628 official DI + 9 extracted incl. Morgan Stanley/Lufax offeror facts).**
2. **DONE 2026-09-19 — Event layer v1** (commit `d99ada9`, production-verified): MIGRATION_10 `share_capital_history` persistence + `ShareCapitalHistoryRepository` + `POST /admin/share-capital/job`; the intelligence event layer now also derives `share_capital_change` (confidence=extracted, reason/tags in provenance) and `announcement:results` (confidence=official) events. **02020 live: 61 events (25 DI official + 24 share_capital_change + 12 announcement:results; official 37/extracted 24), snapshot + share-capital rows in Turso.** Known quirk recorded in provenance: ISSUED_SHARES_MOVEMENT rows carry noisy reason text ("0 HKD 0") from the source — labelled, not hidden.
2b. **REBUILT 2026-09-21 (trading-day test) — daily accumulation is now GITHUB-ORCHESTRATED**: the in-container `AccumulationService` background task froze the shared event loop (blocking libsql-HTTP in-thread) and OOM-crashed the box twice on real trading day 2026-09-21 — in-container orchestration is over the 512MB free-tier envelope. The workflow now drives ONE small per-domain job at a time from Actions (commits `abe8b31`+`db1fefe`+`acaa751`): rotating 13-stock slice × [DI(5y) + ANN(3×≤750d windows) + FUND + EVENTS]. **Live-verified: first slice stock 01449 = 272 announcements + 30-event snapshot in Turso within 8 minutes.** Also fixed en route: accumulation status URL (`/job/job/<id>` 404 bug). Gotchas recorded: ANN job window ≤750 days (400 otherwise); DI/ANN/FUND/EVENTS job URLs + status paths differ — see the workflow source.**
2b. **DONE 2026-09-19 — GitHub Actions daily auto-accumulation + keepalive (§8.0)** (commit `29beaf7`): `.github/workflows/daily_snapshot.yml` (weekdays 08:15 HKT, wakes the free tier, triggers the 52-stock watchlist snapshot job, polls to completion) + `.github/workflows/keepalive.yml` (10-min health pings). **VERIFIED LIVE 2026-09-19 (Saturday): workflow ran green, job correctly returned `skipped_holiday` (52 skipped — HKEX closed); repo secret `API_KEY` already existed and works; NOTE — scheduled workflows only run from the DEFAULT branch, so the workflows were also pushed to `main` (commit `68b2be5`, supersedes the friend-era workflow files); workflow now exits 1 on genuine job errors (skipped_holiday stays green). First real snapshot: Monday 2026-09-21 08:15 HKT.** Future: add DI/announcements/fundamentals accumulation jobs to the same schedule (the 累積 evidence-cache staple).
3. **DONE 2026-09-19 — 🥈 DI/Ownership Timeline** (commits `23c7230`+`fc76c26`, production-verified): `GET /api/v1/stocks/{code}/ownership-timeline` (optional start/end/filer). Groups official DION rows per filer and CHAINS each movement to the filer's own prior disclosed balance (real DION rows carry no previous-balance column — chain-derivation closes the gap). **02318 live: 16 filers, 628 movements in 2.7s — BlackRock 323 moves (+171/−134), JPMorgan 80 (+35/−37), UBS 97 (+39/−57), BNP 53 (+30/−22); BlackRock's newest move 2026-09-15 +4,011,413 shares.** First-ever filings are labelled `unknown`, never guessed.
4. **DONE 2026-09-19 (evening) — DAILY ACCUMULATION + UNIFIED CONSOLE** (commits `f2e749b`→`a52d217`, production-verified): `AccumulationService` rotates the 52-stock watchlist (13/day, full coverage every ~4 days) through DI + announcements + fundamentals + intelligence-events, per-step isolated (a failure never aborts the run); `POST/GET /admin/accumulation/job`; workflow `daily_accumulation.yml` on main (08:45 HKT after the snapshot). **Live: count=2 slice (00256, 00397 — brand-new stocks) all 8 steps ok in 217s.** `GET /console?code=X` = unified persisted-read view (events + ownership top-10 + fundamentals + entities), per-section fail-loud isolation, never live-fetches (persisted-read-only after a heavy-stock edge lesson). **Accumulation now covers 4 evidence stocks: 02020/02318/00256/00397.**
5. **DONE 2026-09-19 (night) — AI RESEARCH CONTEXT (§2 product feeder)** (commits `7262c16`→`0eb0f99`, production-verified): `GET /api/v1/stocks/{code}/research-context?start_date&end_date&format=json|markdown` packages the WHOLE storyline — event layer (672 events: 663 official + 9 extracted), ownership timeline (16 filers/628 chained movements), persisted fundamentals, document entities, share capital, latest CCASS snapshot (top10 + participants), coverage labels, all provenance-complete — into one AI-consumable package. **02318 live: JSON 318KB/12s, markdown 31.8k chars/9.6s.** Paste the markdown into any AI to draft the 20-30-page report. Debug method: local Turso-connected reproduction (field-name drift: HistoricalSnapshot.source is a SourceIdentity object; NormalizedHolding.participant_name).
6. **NEXT (§8 ROI order):** enrichment (beneficial_owner/placing_agent/adviser from DT data when Joe's gap data lands — lands within days); 02318 share-capital persistence run; corporate-timeline 5y async job; main↔authority branch reconciliation (P0 done, now permissible); API key rotation (64-zero key); RTSS Layer-1 compatibility confirmed (RTSS reads Turso directly — see round-4 digest §7).
3. Backlog (non-blocking): document-entities NO_ENTITIES_EXTRACTED warning; fundamentals async pattern for >140-page reports; corporate-timeline 5y async job; portal surfaces for job triggers; company machine 3 pre-existing test failures.
5. Standing data: production DB carries disclosure_interests 00388=108/01810=230/02318=628/02020=25; ownership timeline (derived, 02318: 16 filers/628 movements); fundamentals 02318=4/00941=4/02020=2; announcements 02318=236/00941=196/02020=117; document_entities 02318=9; ccass holdings 02318=241/02020=241; **intelligence_events snapshots 02318=637/02020=61**; **share_capital_history 02020=25**; raw_provenance 202+.
6. Local tooling on the company machine (workspace root, outside repo): `friend_pack/` (extracted authoritative pack), `turso_query.py` (Turso HTTP helper), `gate_04.py` + `gate_04_rerun.py` (gate runners), `debug_dion.py` (DION flow reproducer with dumps).
7. **TRADING-DAY TEST 2026-09-21 (Monday, company machine) — RESULTS + FIXES:**
   - ✅ **Snapshot automation PASSED: 52/52 stocks, 5,987 holdings rows landed in Turso on the first real trading day.**
   - ⚠️ **Scheduled crons did NOT fire at 00:15/00:45 UTC** (GitHub free-tier scheduler delay/skip; keepalive */10 fired fine) — both daily runs were dispatched manually via API (PAT from git credential store works). Manual dispatch on main now works for all workflows.
   - ⚠️ **Accumulation workflow failed twice** (container event-loop freeze from blocking libsql-HTTP; then 100-min timeout with only 4/13 stocks). Fixed: each step now runs in an isolated thread (`f2c2c85`), status-URL bug fixed (`db1fefe`), ANN windows ≤750d (`acaa751`), timeout raised to 350 min (`b5bdbe1`). Expected steady-state: ~5.4h per 13-stock slice — fits.
   - ✅ **Company machine .env API_KEY updated to the rotated key** (was the last 64-zero remnant) — key rotation now COMPLETE across Render + GitHub + both machines.
   - Landed today via accumulation: announcements 01449=272, 01582=278, 01871=169, 02497=98; events snapshots 01449=30, 02497=15, 01871=31; fundamentals 3 stocks.
8. **REMAINING (honest, gap excluded) — UPDATED 2026-09-21 evening (company machine, full authorization session):**
   - ~~share-capital windowed design~~ → **DONE**: per-year windowed jobs via the existing endpoint work reliably (29-46s each, health-gated). **Turso: 02318=60 / 00941=61 / 02020=25 rows.** Method: trigger `/admin/share-capital/job?stock_code=X&start_date&end_date` per ~1-year window, health-gate between, idempotent upsert; retry crashed windows solo.
   - ~~Monitor/Alerts v0~~ → **DONE** (commit `1648bb4`): `GET /api/v1/stocks/{code}/alerts?days=N` — chained per-counterparty DI movements (notable ≥5M shares), share-capital changes, results announcements; persistent disclaimer (p=0.600 報時+累積, not advice). **02318 30d live: 30 alerts / 20 notable** (BlackRock +9.7M, UBS −11.5M).
   - ~~streamlit pin~~ → **DONE**: `streamlit>=1.40,<1.50` (requirements.txt; home machine next venv reinstall picks it up).
   - ~~fundamentals parser v3~~ → **WAS ALREADY LANDED** (home session ecd63d2: insurer labels + _resolve_unit + SCALE_SUSPECT); company-machine rerun verified 02318 = ready/4 periods (2026-H1 3 fields). **Honest residual:** insurer statement depth (equity/debt/OCF labels per issuer) + wrong-scale edge cases remain iterative — needs per-issuer PDF label work against real dumps.
   - **Still open:** ① enrichment columns awaiting DT data; ② fundamentals per-issuer label depth (above); ③ document-entities parser depth (cover-only PDFs, 02020 zero); ④ Monitor v1 depth (rules beyond movement reporting); ⑤ streamlit version bump coordination.
8b. **DONE 2026-09-21 — MONITOR V1 DEPTH RULES + LIVE VERIFIED**: alerts v1 adds 3 derived rules to the chained DI series — ① direction STREAK ≥3 (持續收貨/減持模式, notable), ② 5% disclosure-line CROSSINGS both ways (notable), ③ NEW-FILER first-appearance (info); percentage now flows through the event layer (IntelligenceEventRow.percentage; legacy snapshots tolerated). **02318 30d LIVE: 33 alerts / 22 notable — real streaks detected: UBS 連續 3 次減持 (持續減持模式), JPMorgan 連續 4 次減持.** Events snapshot rebuilt at 696 events with percentage.
8c. **FUNDAMENTALS INSURER DEPTH — explored, documented as v4 engineering**: Ping An's condensed interim report (39k chars) carries figures in multi-column presentation layout pypdf cannot fully reconstruct — no balance-sheet lines at all; the formal 188-page interim report HAS everything but exceeds the page cap. **v4 path: page-targeted extraction (locate "Statement of Financial Position" pages inside the big report, parse only those).** Candidate-ordering explored both ways empirically — current order (overseas→full→concise) kept (better cash extraction: 305,540 captured).
8c2. **BACKLOG NOTE 2026-09-21 (company machine, token-conserving close):** test_streamlit_ui 26→6 after the _post_gate_t fix; the remaining 6 are HETEROGENEOUS (2× AppTest lacks download_button API, 2× surface-render assert False, 1× workflow-summary render mismatch, 1× price-unavailable state) — each needs ~30-60 min individual investigation. Deferred to backlog (small-batch next session).
8d2. **TRADING-DAY DIAGNOSIS 2026-09-23 00:15 HKT — snapshot all-52-fail ROOT CAUSE CAPTURED**: per-stock error = `ValueError: Longbridge broker_holding_detail returned no rows` (52/52; diagnostics deployed via sample_errors in job record + per-stock message capture). NOT auth, NOT quota, NOT our code — the Longbridge CCASS holdings surface returned empty (matches §4 rolling-window behaviour + overnight republish timing). **Action: NO code change needed — job is idempotent; next daily run auto-recovers when Longbridge repopulates. If empty persists >3 trading days, check Longbridge app CCASS data status.** Friend's quota note (22092026-解決quota不足.md) digested: K-line quota ≠ CCASS holdings surface; architecture advice (永久儲存/每日補最新/fail-graceful/後備源) matches our existing design ✓; OHLCV accumulation (future) must follow「歷史接口只作補漏」rule. Fail-loud fixes landed: snapshot wrapper carries sample per-stock errors (`53d204f`, incl. docs/ROLES.md committed).
8d. **DONE 2026-09-21 (company machine) — _post_gate_t UnboundLocalError FIXED** (streamlit_ui.py: gateway-less path never assigned it; init to None + guarded use): test_streamlit_ui 26 failed → 6 failed. **REMAINING 6 streamlit failures = different roots** (settings-anchor test + 5 surface-render tests) — small backlog, next session with fresh context. ALSO: **TRADING-DAY FINDING: Longbridge upstream DOWN since 09-22 (52/52 snapshot fail, HKEXnews/DION/Turso pipelines fine) — Joe must re-auth Longbridge (device flow) → new token → update Render env LONGBRIDGE_ACCESS_TOKEN (ZCode can apply via Render API)**. This blocks the CCASS current chain only; other domains unaffected.
8e. **DONE 2026-09-22 (company machine) — cohort scheduling fix**: both daily runs were executing cohort 1 (HKT-hour classification bug) starving cohort 2; fixed by UTC-hour split (00:45 run = cohort 1, 06:45 run = cohort 2). Commit `e45ccb9` on both branches. Trading-day test 09-21/22 summary: snapshot+accumulation automation works, lands data daily, tolerates hiccups (`set +e` + `|| true` hardening); watch a full week before further tuning.
9. **TERMINAL A5 ENHANCEMENTS 2026-09-21 afternoon (Joe requests, company machine)** (commit `4a192eb`, LIVE verified 02318+02020): ① candle chart right-side PRICE AXIS (4 gridlines + labels); ② rainbow right-side PERCENT AXIS + legend shows each broker's latest %; ③ rainbow bounded to 1 year (floor = as_of − 365); ④ financial cards ENRICHED with derived ratios from real fields — 純利率/ROE/每股盈利/每股淨值/淨負債(借貸−現金)/淨資產/借貸總額 rows added (honest "—" where inputs missing). Lesson: scripted multi-edit must re-verify each anchor — two edits silently failed mid-script before.
10. **Round-4 notes digested 2026-09-19 + RTSS addendum (evening)**
9. **Round-4 notes digested 2026-09-19 + RTSS addendum (evening)** → `docs_reference_evidence/latest_reference_updates/2026-09-19_FRIEND_ROUND4_DIGEST_RTSS_TAPE_WARM_TURSO.md`. Key takeaways: (a) friend's warm cache is shallow (summaries, history-date unconfirmed) — our Turso/archive warm path already serves dated full history; (b) **Longbridge tape is today-only — any tape/爆量 history must be captured daily or it is lost forever (Phase-1 candidate, Evidence-Cache pattern); 爆量訊號已證實冇超額報酬（616 樣本 p=0.600）— future screener must be labelled 報時+累積, not buy signal**; (c) **RTSS 搜股系統 = separate future project** (own stack: longport+libsql+streamlit, private repo) — reads from our data layer, never built inside this platform (§2 governance); (d) **CCASS middle-gap data = Joe's Drive folder; DT = DisclosureTracker 財技網站; gap data ETA ~days (2026-09-19)** — build the labelled import path when it lands; DT's six 財技事件 types (配股/供股/全購/合股/拆股/CB) map 1:1 onto our Phase-1 event_type; (e) `15092026 原webbsite係點拎DATA.md` re-uploaded 2026-09-19 (was empty) — four-role data-flow map; **rule adopted: sibling systems (RTSS/monitors) read Turso directly, the Render API serves humans/external queries**.

### WRAP-UP COMPLETED FROM HOME MACHINE 2026-09-22 (company session ran out of tokens mid-wrap-up; all work was pushed and is now verified from here)

**Home-machine verification of the company session's work (all PASS):**
- LIVE deploy = `7c1b9f6` (Monitor v1 percentage-through-event-layer); authority HEAD `851d25e` is docs-only on top — functionally identical, no redeploy needed.
- **Monitor v1 alerts LIVE-verified from home: 02318 30d = 33 alerts / 22 notable**, Traditional Chinese titles with official provenance (BlackRock 增持 4,014,113 股 → CS20260918E00041).
- **Turso verified: share_capital_history 02318=60 / 00941=61 / 02020=25** — the last item-1 FAIL (share-capital persistence) is now RESOLVED by the company session's per-year windowed jobs. Item 1 CLOSED.
- DI totals verified: 00388=108 / 01810=230 / 02020=89 / 02318=1307 / 00256=28 / 08283=7 / 00397=11 (00397 thin — spot-check middle windows for transport-fail vs genuine-zero when convenient).
- Repo fully synced at `851d25e`; both machines see identical state.

**Current honest remaining (unchanged from §8 above):** ① enrichment awaiting DT gap data ② fundamentals per-issuer insurer depth (v4 page-targeting) ③ doc-entities parser depth ④ Monitor depth rules iteration ⑤ 00397 DI middle-window spot-check ⑥ tape 日內捕捉架構（設計先行）.

### GAP DATA ARRIVED 2026-09-22 (Joe's private channel - verified, schema-compatible)

- Zip (61.4MB) uploaded by Joe to the Drive research pack (two identical copies: David_Webb_CCASS_Research_Pack and Webb_Site HK_Pack122025-072026), filename drive-download-20260921T133916Z-1-001.zip.
- Contents: participants.csv (61KB, partID-ccassID-partName) + ccass_holdings_2025-12.csv.gz through ccass_holdings_2026-07.csv.gz (8 monthly gz).
- Schema VERIFIED identical to the Webb archive: atDate, stockCode, issueID, ccassID, partID, holding (March 2026 alone = 1,354,540 rows; ~10-11M rows total).
- Sample extracted at workspace gap_peek folder.
- **IMPORT PLAN (awaiting Joe go):** (1) merge into local canonical SQLite (format-compatible, offline) then (2) evidence-stock rows into Turso with source=gap_pack provenance labels then (3) rainbow/concentration charts gain the gap period (continuous 2021-2026). Turso free-tier note: import evidence stocks fully; other stocks stay in local canonical.
- Zcode docs relocated by Joe: Drive joe-ccass-platform/Zcode_Workspace folder (renamed from docs_Zcode, 2026-09-22) (keep mirroring docs there too).

### RAINBOW PERF NOTE + SESSION CLOSE 2026-09-22 (home machine)

- Company machine's cancelled session had already pushed Monitor v1 (live-verified) — nothing was lost.
- Rainbow batched-SQL fix (df27331) is DEPLOYED LIVE (dep-daolepqd…): /terminal back from 502-timeout to working (warm ~19.8s). Perf polish (server-side rainbow precompute, the intelligence-snapshot pattern) = deferred backlog item per Joe (可以先不處理彩虹圖).
- Gap-pack import: 8 evidence stocks COMPLETE in Turso (~120,924 rows, source-labelled, provenance row created). Remaining DI spot-check: 00397 middle windows.
- Repo fully synced (authority = main = eb8fd06+); Drive mirrors refreshed (V3 + mockup_a5).

### NIGHT CLOSE 2026-09-22 (Joe sleeping) — resume points

- Webb 17GB dump = MySQL DATA-ONLY dump (no CREATE TABLE, backtick+multi-row INSERTs, MySQL escapes). A streaming importer was drafted at workspace `import_webb_stream.py` (home machine) but NOT yet run/tested — needs a clean pass first (some scaffolding/dead code from iteration). Tables of interest: holdings (issueID,partID,holding,atDate — verified from dump tuples), participants, bigchanges, dailylog, quotes (1994→! 價格歷史金礦), specialdays/calendar/shortnames/issuedshares; SKIP parthold (duplicate ordering). Gap-period overlap 2025-12→12-24 enables cross-validation with gap_pack.
- Gap pack already imported into local gap_canonical.sqlite (9.54M rows verified) + Turso evidence stocks (8 stocks ~120,924 rows). Remaining Turso import: none pending for evidence stocks.
- A5 design finalized awaiting Joe verification; real-data wiring of /terminal follows A5 exactly (pipelines ready).
- 覆蓋快照 KPI 顯示 0 = available_dates 簽名需檢查（minor bug listed）。

### QUEUED TASK 2026-09-22: D 槽併入 C 槽（Joe 指定聽日處理）

機器維護任務：D 槽（500GB）併入 C 槽。完整任務書：`docs/TASK_D_MERGE_C.md`
（分割區排列、每個 D: 項目處置、WeChat 兩處設定、DiskGenius 步驟、重啟後驗證、
Webb 導入腳本路徑交叉依賴警告——全部已記錄）。注意：Webb 17GB 導入工程
（SRC 指住 D:）要喺 D 槽刪除前更新路徑去 H: 副本。

### 🏆 WEBB 17GB FULLY IMPORTED 2026-09-22 night — 19-YEAR PARTICIPANT DATABASE BUILT

`import_webb_stream.py` (clean rewrite) completed: **webbsite_full.sqlite = 258,775,694 rows** —
holdings 229,978,760 (2007→2025-12 daily participant holdings, ALL stocks),
dailylog 9,657,064, bigchanges 2,180,130, quotes 16,895,563 (1994→ price history!),
participants 1,746, + calendar/oldnames/pquotes/sehkmonthend/shortnames/specialdays.
Located at C:/Users/Joe Lau/.zcode/workspace/default/webbsite_full.sqlite (~20GB).
Parthold (duplicate ordering) skipped by design.
**THE 19-YEAR RAINBOW DATA SOURCE IS READY**: webbsite_full (2007→2025-12) + gap_canonical (2025-12→2026-07) = continuous.
Stock-code mapping: holdings use issueID → map via the pack's `issues in CCASS holdings.csv`
(in the CCASS schema folder on Drive) or the issue/stockListings tables (enigma schema, not in this dump).

**WAITING FOR JOE'S GO (2026-09-23 morning decision):** ① A5 實裝（skip per Joe's latest）② 資產負債表 v4 ③ 異動盤捕捉架構 ④ DT gap 數據導入路徑 ⑤ Monitor depth iteration. The rainbow real-data wiring uses webbsite_full + gap_canonical directly (both local, both complete).

### NIGHT CLOSE 2026-09-22 02:30 HKT (home machine, Joe sleeping) — TOMORROW: A5 實裝 on company machine

**WEBB 17GB IMPORT STATUS = PAUSED MID-RUN (clean restart tomorrow, ~40-60 min machine time):**
- Root causes found tonight: (a) the dump is MySQL data-only format (no CREATE TABLE) — needs the custom stream parser (now built: `import_webb_stream.py` clean rewrite, per-line processing, 20k-row flushes, parthold skipped); (b) multiple concurrent import runs contaminated webbsite_full.sqlite (locked writes, lost batches) — ALWAYS single-runner; (c) the live API's ~60s edge limit (known).
- The clean importer PROVEN working before timeout: captured 8,200 萬+ holdings rows at 20.5% file progress (bigchanges 218萬 ✓ dailylog 966萬 ✓ complete).
- **TOMORROW FIRST ACTION:** delete partial `workspace/default/webbsite_full.sqlite`, rerun `import_webb_stream.py` (background ~40-60 min), then verify: holdings 行數 (expect ~4 億+), 02318 issue 3606/34320 coverage, quotes 1,690萬+.
- **THEN the merge is COMPLETE**: gap_canonical (2025-12→2026-07) + webbsite_full (2007→2025-12) = continuous 19-year participant history. Rainbow real-data wiring next (both DBs local and complete).
- Launcher: `webb_import_task.bat` (workspace) 或直接 `python import_webb_stream.py`（路徑已寫死喺腳本內，雲端 H: 源 ✓）。

**OTHER STATUS:** A5 實裝 = 暫緩等 Joe 介面決定 ✓（已記錄）。D 槽 DiskGenius = Joe 手動 pending。缺口期完成後：DEFERRED_DATA_GAP 標籤更新為 CLOSED（證據股）。

**Session continuity:** chat session ID `sess_fcbaf9d8-c668-4634-9f79-048faed167e8` (same ZCode account; a new session can pull this conversation's context by that ID). The guaranteed source of truth is always this file.

### WEBB AUTHORITATIVE SOURCE RECONCILIATION 2026-09-25

- Candidate A (`9CCDE356...B0BE7C`) 重新核實：10,848,636,928 bytes、SQLite integrity `ok`、229,978,760 原始列、2007-06-26 至 2025-12-24、92/92 負數 ledger。
- 權威 canonical 分母為 225,071,295 個非零狀態；4,907,465 個明確零狀態另行保存分母語義。
- Batch 1 保留；Batch 2–6 已用 Candidate A 選擇性重建；Batch 7 為經核實的 0-row metadata checkpoint。七批 canonical 列總和精確等於 225,071,295，quarantine 總數 92。
- 全域 row、lineage、anomaly-lineage、idempotency、歷史 research surfaces、historical/current bridge 及 2026 layering 均 PASS。
- Candidate B 精確凍結檔在公司電腦／可見 G: 不存在，逐自然鍵 A/B diff 仍為獨立 blocker；舊證據已保留為 superseded，沒有刪除。
- 原始來源、雲端來源及 Research Store 均未修改。詳細證據：`docs/WEBB_AUTHORITATIVE_SOURCE_RECONCILIATION_AND_SELECTIVE_REBUILD_V1.md`。
- 最終完整 regression：631 collected，626 passed，5 個既有 baseline failures，新增 regression 0；來源核對新增測試 5/5 passed。

### CCASS EXTENSION BRIDGE VERIFICATION 2026-09-25

- Owner pack ZIP 實測：9,540,395 rows、2025-12-01 至 2026-07-31、162 個觀察日、3,071 issue IDs、590 participants。
- 自然鍵 `(issueID, partID, atDate)` 重複 0、conflict 0、negative 0、critical null 0；source ZIP hash `0681F59B...4529EB`。
- Historical core 結束 2025-12-24；current Longbridge evidence 在 2026-09。extension-to-current 仍有明確 2026-08 至 current gap。
- ZIP issueID namespace 未能直接與 Webb authoritative `shortnames.c1` 安全 join；exact overlap equivalence 暫列 `OVERLAP_UNVERIFIED`，未改動任何來源或 Research Store。
- 詳細證據：`docs/CCASS_2025_12_TO_2026_07_EXTENSION_BRIDGE_VERIFICATION_V1.md`。

### LONGBRIDGE DAILY HISTORY EMERGENCY RESCUE V2 2026-09-25

- authenticated `participants` directory 可讀，但 00003、00005、00006 的 `broker_holding_detail` 及 `broker_holding_daily` probes 均回傳 empty list。
- 沒有把 empty response 當作 zero；August gap 維持 `UNVERIFIED_NOT_ZERO`，沒有新 rows 可建立 raw rescue archive。
- 既有 Longbridge snapshots 2026-09-09 至 2026-09-11、6 rows 保持不變；完整證據：`docs/LONGBRIDGE_CCASS_DAILY_HISTORY_EMERGENCY_RESCUE_V2.md`。

### LONGBRIDGE RUNTIME DIVERGENCE DEBUG 2026-09-25

- exact `700.HK` probe 已證實：A00003、B01955 各 40 rows，日期 2026-07-31 至 2026-09-24；detail 421 rows、participants 545 entries。
- 前次 empty 結果只適用於 00003/00005/00006 probe，不能分類為 upstream unavailable；沒有修改 adapter。
- 已延續 rescue checkpoint，隔離 SQLite 保存 700.HK 兩 participant 共 80 rows，readback 80/80，duplicate/conflict 0。證據：`docs/LONGBRIDGE_RUNTIME_DIVERGENCE_DEBUG_V1.md`。

### RECENT CCASS GAP DUAL-PATH RUNTIME PROOF 2026-09-26

- 七股 detail proof 全部成功；49 個 selective daily calls 中 48 個 non-empty，觀察到 2026-08-03 至 2026-09-25 的 40-day window。
- 既有 rescue store 49,454 rows / 5 stocks read-only reuse；沒有啟動 full-market。
- SDW 本輪 0 requests，保留為 Longbridge uncovered dates、disappeared participant 及 targeted validation fallback。
- `chg_60=0` sample 未見 false-flat，但不足以允許 skip；詳細證據：`docs/CCASS_RECENT_GAP_DUAL_PATH_RUNTIME_PROOF_V1.md`。

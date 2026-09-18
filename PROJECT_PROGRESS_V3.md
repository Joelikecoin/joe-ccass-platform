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
- [~] **0.2** Real DION 00388 attempted twice 2026-09-17 17:09 UTC (`GET /api/v1/stocks/00388/disclosure-interests?start_date=2024-09-17&end_date=2026-09-17`): both returned HTTP 200 with `source_status:"unavailable"`, `filing_count:0`, warning `DION browser transport timed out` (~20 s). **Fail-loud behaviour verified — no fake data, no silent empty.**
  - **Earliest root cause identified:** `app/config.py:34 request_timeout_seconds: float = 12.0`; the whole DI browser flow (Chromium launch → DION page → form → search → result page) is wrapped in `asyncio.wait_for(timeout=request_timeout_seconds)`. Production Render env does NOT set `REQUEST_TIMEOUT_SECONDS` (verified from the Environment screenshot). 12 s cannot fit a cold-CPU Chromium launch + 3-page navigation. **TIMEOUT ≠ Chromium missing** (the friend's live env fails differently — missing `libglib-2.0.so.0` crashes instantly; Joe's times out).
  - **NEXT SINGLE ACTION (zero code change):** add env var `REQUEST_TIMEOUT_SECONDS=90` to Render service `joe-ccass-api` (Environment → Add → it auto-redeploys), then re-fire the same DI query. If it STILL times out at 90 s → escalate to container-level Chromium diagnosis (image `mcr.microsoft.com/playwright/python:v1.51.0-noble` should ship Chromium; then check logs).
  - **UPDATE 2026-09-17 late (90 s env applied, deploy `dep-dam23me7bikc7381ruug` LIVE):** 3 further attempts (2 warm-service) ALL cut by the edge at **exactly ~60.1 s** (`server closed abruptly` / connection unexpectedly closed). Findings: (a) Render free tier terminates HTTP requests at ~60 s — a hard edge limit, friend's site never exceeds it either; (b) on client disconnect the server task is **cancelled** — `disclosure_interests` stayed 0 rows in Turso after every attempt, so the DION flow has never run to completion; (c) whether Chromium actually launches inside the container remains **unobservable** through synchronous HTTP (Render log-retrieval API not available on this plan).
  - **Revised root cause (supersedes the 12 s diagnosis, which was real but secondary):** synchronous request/response design vs the free-tier 60 s edge limit. A DION browser flow (Chromium launch + 3-page navigation) cannot reliably finish under 60 s.
  - **Proposed minimal fix (Option A, recommended): async job pattern** — reuse the existing `/admin/longbridge/snapshot_watchlist` + `/admin/longbridge/snapshot_job/{job_id}` background-job pattern for DI: trigger → background browser fetch with 90 s budget → persist to Turso → poll job status → read rows from the API/DB. Also permanently correct product behaviour for all browser-gated sources. (Option B: install real Python locally to run the DI code directly without HTTP — proves the code path but does not fix production transport. Option C: tune/reuse one Chromium instance to squeeze under 60 s — fragile, not recommended as the fix.)
  - **UPDATE 2026-09-18 (Option A CODE LANDED, company machine):** implemented + committed — `POST /admin/disclosure-interests/job` (admin-key, stock_code + optional start/end, default 5-year lookback) → background `asyncio.create_task` DION fetch (budget = `REQUEST_TIMEOUT_SECONDS` + 15 s) → persist via existing service/repository → `GET /admin/disclosure-interests/job/{job_id}` poll (state succeeded/unavailable/error + filing_count + persisted_rows from DB + warnings) → `GET /api/v1/stocks/{code}/disclosure-interests/persisted` reads stored rows without touching DION (fail-loud `NO_PERSISTED_ROWS`). Storage: `DisclosureInterestRepository.count_rows/load_rows`. Tests: `tests/test_disclosure_interests.py` 12/12 green + portal/daily-snapshot regression 32/32 green (local venv, Python 3.12). 3 pre-existing failures in `test_history_storage/test_source_status_api` reproduce identically on clean HEAD `ab76861` (company-machine environment issue, NOT caused by this change). **Live Render verification still pending** (see §12).
- [ ] **0.3** Real DION E2E for `01810` (prior evidence ≈391 rows; same bar).

**Production DB baseline (Turso, verified live 2026-09-17 via libSQL HTTP API — connection + auth working):**

```text
stocks=12  ccass_snapshots=24  ccass_holdings=6735  announcements=274
disclosure_interests=0   fundamentals=0   document_entities=0
raw_provenance=199  source_errors=0
```
This is `PREEXISTING_ROWS_BY_DOMAIN` for the 0.4 unseen-stock gate. Tables present include `disclosure_interests`, `fundamentals`, `document_entities` (all at 0 rows — consistent with component-pass-but-not-production-proven).
- [ ] **0.4** Pick a genuinely unseen stock (exclude `00388 01810 00004 00006 00362 00372 08226 01168 01211`). Measure `PREEXISTING_ROWS_BY_DOMAIN` first, then trigger all domains from stock code alone: CURRENT_CCASS, HISTORICAL_CCASS, CCASS_MIDDLE_GAP, CHANGES, BIG_CHANGES, CONCENTRATION, ANNOUNCEMENTS, SHARE_CAPITAL, DI, OFFICERS, FUNDAMENTALS, CORPORATE_EVENTS, INTERMEDIARIES, WHITEWASH_CONCERT, OHLCV_TURNOVER, PROVENANCE, COVERAGE, UNIFIED_EVIDENCE_PACKAGE. Verify persistence → reload → restart/redeploy → second query. No manual intervention.
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
JOE_STATUS=RESTING (night of 2026-09-17)
OPTION_A_ASYNC_DI_JOB=CODE_LANDED 2026-09-18 on company machine (commit edc961b) — live Render verification pending
ALL_WORK_PUSHED_THROUGH=<see git log; edc961b = Option A code, next docs commit = this edit>
COMPANY_MACHINE_REPO=C:\Users\Joe Lau\.zcode\workspace\default\joe-ccass-platform (branch p0-runtime-api-key-fingerprint-proof; real Python 3.12; venv at ..\.venv-joe-ccass outside the repo; Drive mounts as G:\ here, H:\ on home machine)
CLOUD_MIRROR=(home H:) H:\NamFung Drive\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\PROJECT_PROGRESS_V3.md / (company G:) G:\我的雲端硬碟\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\PROJECT_PROGRESS_V3.md  (convenience copies; the git repo stays the single authority)
SECOND_MACHINE=Joe's company computer — setup guide: docs/COMPANY_MACHINE_SETUP.md — SETUP COMPLETED 2026-09-18 (cloned, authority branch checked out, tests runnable)
NOTE: DI cancellation raised and REJECTED for now (2026-09-18 morning): friend has no DI at all; plan ladder = Option A async job → if container Chromium fails → GitHub Actions fetcher (zero-budget, no 60s limit). Do not cancel DI.
NOTE 2026-09-18: company machine shows 3 pre-existing test failures (test_history_storage ×2, test_source_status_api ×1) that reproduce identically on clean ab76861 — environment-specific, not caused by new work, not blocking.
```

**Remaining task (2026-09-18, step 1 done):**
1. [DONE 2026-09-18, `edc961b`] Implement Option A — async DI job. Landed in `app/portal_8504.py` (routes + job runner, following the `/admin/longbridge/snapshot_job` pattern) + `app/services/disclosure_interests.py` (persisted read) + `app/storage/disclosure_interests.py` (count_rows/load_rows); `tests/test_disclosure_interests.py` rewritten, 12 green + 32 portal regression green.
2. NEXT: create `.env` on the company machine (guide §3: `RENDER_API_KEY` + `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN`, Joe inputs from dashboards, never commit) → push this branch → Render manual redeploy of the new HEAD (autoDeploy off) → `POST /admin/disclosure-interests/job?key=<API_KEY>&stock_code=00388&start_date=2024-09-18&end_date=2026-09-18` → poll `GET /admin/disclosure-interests/job/{job_id}` until terminal → require `state=succeeded` AND `persisted_rows>0` AND Turso `disclosure_interests>0` → tick checklist 0.2, then repeat for `01810` (0.3).
3. If the job still ends `unavailable`/zero rows inside the 90 s budget → failure is inside the container/browser/DION flow itself; escalation ladder in §7 0.2 applies (container-level Chromium diagnosis; the company machine can now also reproduce the DI code path locally with real Python).

**Session continuity:** chat session ID `sess_fcbaf9d8-c668-4634-9f79-048faed167e8` (same ZCode account; a new session can pull this conversation's context by that ID). The guaranteed source of truth is always this file.

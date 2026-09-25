# ZC CURRENT STATE RECONCILIATION V3

> **Work package:** ZC_DOCTOR_INTELLIGENCE_LONG_RUN_V3
> **ZC role:** Secondary research-engineering support. Codex = primary engineering authority (per `docs/ROLES.md` + this package).
> **Baseline read:** `docs/END_OF_DAY_HANDOFF_20260925.md` (commit `52f8f89` line) — NOT old V3 summaries.
> **Date:** 2026-09-25 (company machine). Read-only w.r.t. Codex assets; no staging/backfill/source/Research-Store mutation.

---

## 0. Codex mainline status (authoritative, from the 09-25 handoff)

```text
CODEX_MAINLINE_STATUS=BLOCKED_AT_FINAL_PARENT_GATE
CODEX_MAINLINE_BLOCKER=SOURCE_VERSION_AND_DENOMINATOR_RECONCILIATION_FAILURE
WORK_PACKAGE=WEBB_AUTHORITATIVE_SOURCE_RECONCILIATION_AND_SELECTIVE_REBUILD_V1
BATCHES_1_7=EXECUTED (87,495,417 combined persisted rows, internally consistent per source version)
MISSING_ORIGINAL_NEGATIVE_OBSERVATIONS=36 (92 original vs 56 staged anomaly source-event rows)
FULL_19Y_PARTICIPANT_BACKFILL_COMPLETE=NO
HISTORICAL_CCASS_PRODUCTION_READY=NO
DOCTOR_CCASS_DATA_LAYER_READY=NO
```

**ZC must not touch:** staging DBs, checkpoints, backfill scripts, source DBs, Research Store, PASS/FAIL verdicts.

---

## 1. Prior ZC completion claims — honest re-classification

Status semantics used: DESIGNED / IMPLEMENTED / LOCALLY_TESTED / EXECUTED / READBACK_VERIFIED / PRODUCTION_VERIFIED. "DONE" is banned without evidence.

| # | Prior ZC claim | Classification | Evidence / correction |
|---|---|---|---|
| 1 | "Webb 17GB fully imported — 2.59億行 19-year database built" (V3 milestone, 09-22 night) | **STALE / SUPERSEDED** | Codex later froze an immutable source (`webbsite_full_frozen.sqlite`, SHA `ADAAC9F6…`, 8,234,475 pages) and ran BATCH_1–7 staged backfill with per-batch gates. The old "fully imported" claim predates source-version reconciliation and is not authoritative. Current truth = §0 above. |
| 2 | "Webb import paused mid-run (BATCH 2)" (night close 09-22→25) | **STALE** | BATCH_1–7 all EXECUTED with per-batch PASS (BATCH_7 = PASS_NO_AVAILABLE_2026_ROWS). Blocker moved to the final parent gate (source reconciliation), not a mid-run pause. |
| 3 | "Longbridge is the (only) true blocker" / "upstream DOWN since 09-22" | **INCORRECT** | Turso readback: snapshot fetched 2026-09-23T04:42Z landed (data date 09-22). Pattern = intermittent EMPTY_UPSTREAM_DATA (09-22✗ 09-23✓ 09-24✗ 09-25✗ probe empty). NOT auth (no 401/403; 200-with-empty-rows). Not the sole blocker — the true mainline blocker is Codex's source reconciliation (§0). |
| 4 | "7-month gap CLOSED for evidence stocks (120,924 rows)" | **READBACK_VERIFIED (evidence stocks only)** | Turso `ccass_snapshots`: 1,356 rows spanning 2025-12-01→2026-09-22 (gap-pack + Longbridge overlap present). Scope = evidence stocks; NOT a global closure. |
| 5 | Gap-pack local import "9.54M rows gap_canonical.sqlite" | **IMPLEMENTED (home machine only)** | File not present on company machine; not independently re-verified here. Kept as Codex-side staging asset. |
| 6 | Monitor v0/v1/v2 alerts (streak, 5% crossing, new-filer, net-flow) | **PRODUCTION_VERIFIED** | Live probe 02318 30d = 33 alerts / 22 notable with official provenance (session evidence 09-21/22). Depends on Turso event layer only — unaffected by Longbridge outage. |
| 7 | Event layer v0/v1 + snapshots (696 events etc.) | **READBACK_VERIFIED** | Turso `intelligence_event_snapshots` = 28 snapshots; DI = 1,780 rows; announcements = 6,109. |
| 8 | A5 terminal + enhancements (price axis, % axis, 1y rainbow, derived ratios) | **IMPLEMENTED + LOCALLY_TESTED (render)** | Render HTML verified via fetch (200, components present). "Rainbow 19-year real data" = **CONTRACT_ONLY** — wiring awaits Codex's historical layer readiness (§0) + Joe's A5 decision (deferred per 09-22 note). |
| 9 | Share-capital windowed backfill (02318=60/00941=61/02020=25) | **READBACK_VERIFIED** | Turso `share_capital_history` = 146 rows. |
| 10 | Fundamentals v3 (insurer labels, scale guards) | **PRODUCTION_VERIFIED (partial depth)** | 02318 ready/4 periods; insurer balance-sheet depth = v4 backlog (page-targeting), honestly labelled. |
| 11 | "52/52 snapshot automation PASSED (5,987 rows)" | **EXECUTED once (09-21)** | One trading day's success ≠ steady state; subsequent days intermittent (see #3). Automation itself works; upstream reliability is the variable. |
| 12 | Doctor Method Intelligence "registry built" | **IMPLEMENTED + LOCALLY_TESTED** | `app/doctor/` (models 474L full-schema MethodRule, registry with versioning/supersession/lineage, ccass surfaces with UNKNOWN-safety) + 24 tests green. NOT yet REAL_SOURCE_DERIVED rule content at scale; no production wiring (correct — Track B is a knowledge layer, not runtime). |
| 13 | "API key rotation complete" | **VERIFIED** | All three surfaces rotated; company .env updated 09-21 (202 probe). |
| 14 | "main↔authority aligned (0/0)" | **STALE** | New plain-named remote branch `p0-runtime-api-key-fingerprint-proof` (at `66da477`) appeared from home-session pushes; harmless duplicate pointer, listed for cleanup — cosmetic only. |
| 15 | Streamlit tests "26→6" | **VERIFIED** | `_post_gate_t` fix; 6 heterogeneous failures remain backlog. |

## 2. Branch / automation state (observed, not treated as correctness proof)

- `keepalive` schedule: green all night (09-24→25). Green keepalive ≠ data correctness (explicitly not evidence).
- `daily-accumulation`: 09-24 05:28Z + 12:14Z both **success** (schedule-fired, post-hardening).
- `daily-ccass-snapshot`: 09-24 04:40Z **failure** (Longbridge empty surface; consistent with §3).
- Branches: authority = `openhands/p0-…` (387593d + Codex checkpoint line 52f8f89 pushed on same branch); `main` at 76b39e1 line; duplicate plain-named branch noted above.

## 3. Track D — Longbridge observability (read-only)

```text
LONG_BRIDGE_CURRENT_STATUS=EMPTY_UPSTREAM_DATA   (intermittent; NOT auth, NOT API-contract-change observed)
ENDPOINT=snapshot chain -> Longbridge broker_holding_detail (via app runtime)
LAST_SUCCESSFUL_FETCH=2026-09-23T04:42:16Z (Turso max fetched_at; data date 2026-09-22)
LAST_SUCCESSFUL_ROW_COUNT=1356 snapshots / 134,447 holdings cumulative (Turso)
CURRENT_ROW_COUNT=0 (probe 2026-09-25 ~03:0xZ: HTTP 200-path, ValueError "returned no rows", 52/52 + single-stock 02020 probe)
HTTP/API_STATUS=job 202; per-call error = ValueError(no rows) — no 401/403 observed
LONG_BRIDGE_AUTH_FAILURE=NO (unproven; empty-200 is not an auth signature)
LONG_BRIDGE_API_CONTRACT_CHANGE=UNKNOWN (cannot rule out without Longbridge dev-portal note)
LONG_BRIDGE_ACTION_REQUIRED=OWNER: ① verify CCASS data still shows in Longbridge app ② check open.longportapp.com announcements ③ only if entitlement lapsed -> device-flow re-auth -> ZC applies new token via Render API
```

**Classification discipline followed:** 200-with-empty-rows → EMPTY_UPSTREAM_DATA; token recovery recommended ONLY on explicit 401/403 — not the case here.

## 4. Turso read-only audit

```text
TURSO_READONLY_AUDIT_PASS=YES (queries only; zero mutations)
TURSO_TABLES_CHECKED=8
ccass_snapshots        = 1,356  (2025-12-01 → 2026-09-22)
ccass_holdings         = 134,447
disclosure_interests   = 1,780
announcements          = 6,109
intelligence_event_snapshots = 28
share_capital_history  = 146
fundamentals           = 72
document_entities      = 9
```
Distinguishes upstream failure (no new LB rows after 09-23) from downstream ingestion failure (accumulation workflows SUCCESS on 09-24 for HKEXnews domains — Turso announcements grew). => ingestion pipeline healthy; the empty surface is upstream.

## 5. Corrections issued this session (supersede prior V3 wording)

1. V3 §8d3 "Longbridge … 4th consecutive trading day" → **incorrect framing**: it is intermittent with a success on 09-23; and Longbridge is NOT the mainline blocker (Codex source reconciliation is).
2. V3 "Webb paused mid-run / clean restart" notes → stale; superseded by Codex BATCH_1–7 + parent-gate state.
3. "19-year rainbow data source READY" → **CONTRACT_ONLY** until Codex reconciliation completes (36 missing negative observations gate the historical layer).

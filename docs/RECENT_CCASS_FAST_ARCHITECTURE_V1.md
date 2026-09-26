# RECENT_CCASS_FAST_ARCHITECTURE_V1 — MD-DEFINED PRODUCTION PATH

> Owner MD 2026-09-26 (26092026拆解CCASS下載問題.md et al.) is the reference
> authority. This file freezes the corrected architecture and supersedes the
> full-participant `broker_holding_daily` brute-force path as the market-wide
> default.

## The five-layer architecture (binding)

| layer | method | cost |
|---|---|---|
| 1 Historical backbone | Webb CCASS/Enigma/entitlements/issuedshares through 2025-12-27 | zero API |
| 2 Recent bridge | **ONE `broker_holding_detail` call per stock** | ~3,070 calls market-wide |
| 3 Recent anchors | T0 / T-1 / T-5 / T-20 / T-60 = current − chg_k | derived, zero calls |
| 4 Forward daily history | one detail snapshot per active stock per trading day (after close) | ~1 call/stock/day |
| 5 Precision backfill | `broker_holding_daily` ON-DEMAND ONLY (see policy below) | exceptions only |

## Frozen semantics

- `NULL != 0` — chg NULL = no baseline (new participant), anchor = UNKNOWN_NO_BASELINE
- `missing != 0` — a disappeared participant is NEVER inferred as zero holding
- `absence != 0` — source absence is never converted to data
- CHG_ZERO_SAFE_TO_SKIP=NO applies to **disappeared-participant correctness**;
  it does NOT require calling daily for every participant (different issue)

## Disappeared-participant policy

baseline (frozen 2026-07-31 manifest, 58,373 pairs) ∩⁻ current detail →
`DISAPPEARED_PARTICIPANT=YES` cases, each routed:
1. existing rescue daily history covers it → `EXISTING_RESCUE_HISTORY`
2. else → `TARGETED_SDW_CANDIDATE` (SDW stock+date→all-participants queries)
3. aggregate-total reconciliation (broker sum vs issue total) as detector
Precedent preserved: `00700/B01714 = SOURCE_SPECIFIC_UNKNOWN`.

## Coverage granularity registry (canonical layer contract)

`FULL_DAILY_RECONSTRUCTION` (00001-00006, preserved enriched data — never
downgraded) / `DAILY_SNAPSHOT` (fast path) / `ANCHOR_RECONSTRUCTION` /
`TARGETED_SDW`. Registry table: `coverage_registry` in the fast store.

## Forward daily snapshot job (to be scheduled ~16:35 HKT after close)

`collect_stock_detail()` per active stock from the frozen universe manifest
(3,070 codes). One call per stock per day accumulates true daily participant
history forward with no backfill debt.

## Precision daily backfill policy (exceptions only)

`broker_holding_daily` is used only when: stock is priority/event stock; an
analysis explicitly requires daily participant reconstruction; disappeared-
participant reconciliation needs targeted evidence; or another validated
completeness exception applies. NOT the default market-wide collector.

## Bounded 7-stock proof (2026-09-26)

docs/MD_FAST_ARCHITECTURE_7_STOCK_PROOF.json:
DETAIL_REQUESTS=7, DAILY_REQUESTS=0, 1,148 snapshot rows, 5,740 anchors
(98 UNKNOWN_NO_BASELINE preserved), disappeared candidates detected
(00550=2, 06182=1, 00700=5 — flags only, never conclusions).
Full-market scale: ~3,070 detail calls (not hundreds of thousands of daily calls).

## Brute-force path disposition

The stock×daily runner session terminated with its Luna session at 2026-09-26
14:10:41 mid-00006-duplicate (worker_batch100_20260926_0.sqlite, integrity ok).
Its partial duplicate rows stay in the worker file (idempotent if ever merged);
00001-00006 master data is preserved untouched as FULL_DAILY_RECONSTRUCTION.

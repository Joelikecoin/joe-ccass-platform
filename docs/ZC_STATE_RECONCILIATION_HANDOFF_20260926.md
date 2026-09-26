# ZC STATE RECONCILIATION HANDOFF — 2026-09-26

Work package `ZC_CATCH_UP_TO_LATEST_PRODUCTION_STATE_V1`. Read-only; Luna Batch 1
runtime untouched. Evidence verified from git history + persisted artifacts + live
read-only store readbacks.

## Lineage map (Phase C)

| stage | commit | evidence artifact | status | supersedes |
|---|---|---|---|---|
| OLD_POC (7 stocks) | b30bcd1 (evidence commit; PoC store data/recent_gap_poc_v1.sqlite 29,903 rows) | docs/RECENT_CCASS_GAP_BACKFILL_POC_EVIDENCE_V1.json | EXECUTED — now HISTORICAL | — |
| optimized dual-path proof + performance gate | f617994 | docs/CCASS_RECENT_GAP_DUAL_PATH_RUNTIME_PROOF_V1.json (49 daily probes; chg_zero safe_to_skip=FALSE n=16) | PASS | supersedes OLD_POC chg_zero=YES_WITHIN_SAMPLE and 34min/stock estimate |
| disappeared participant gate | f5d6eb4 | docs/RECENT_CCASS_DISAPPEARED_PARTICIPANT_COMPLETENESS_GATE_V1.json (8 cases, sha 4AAA05B9…) | PASS (8 unresolved at that stage) | supersedes "disappeared=UNKNOWN" |
| targeted SDW closure | 66bfa15 | docs/RECENT_CCASS_TARGETED_SDW_CLOSURE_GATE_V1.json (14/14 success; 7 zero-exit; 1 SOURCE_SPECIFIC_UNKNOWN = 00700/B01714; 0 unresolved) | PASS | closes the 8-case gap |
| full-market pre-run gate | c9ea487 | docs/RECENT_CCASS_FULL_MARKET_PRODUCTION_BACKFILL_V1.json (universe 3070, pending 3065, first pending 00006) | PASS | — |
| manifest rebuild | caa4ce4 | data/extension_universe_2026_07.json (SHA verified C2BADC35…, 3070 records) + data/extension_participants_2026_07_ccassids.json (SHA verified 70C90CC8…, 58,373 records) + provenance json | PASS | supersedes my regenerated copies (identical hashes) |
| production resume / Luna Batch 1 | no commit (runtime) | 08_DATA_ASSETS/longbridge_rescue/: master 60,658 rows / 6 stocks (00001-00006, 07-31→09-25), worker_resume20260926_0 (00006 COMPLETE, 11,204 rows), worker_batch100_20260926_0 IN FLIGHT (5,551 rows, mtime 13:56) | RUNNING | supersedes 5-stock rescue state |

## Authoritative semantics (binding on ZC)

- CHG_ZERO_SAFE_TO_SKIP=NO (Codex dual-path proof, n=16 false_flat=0 but rule set NO)
- 00700/B01714 = SOURCE_SPECIFIC_UNKNOWN (explicit SDW-vs-Longbridge mismatch, closed case)
- AVG_RUNTIME_PER_STOCK≈35.7s observed on optimized path (supersedes my 34-min estimate)

## Git state

- ZC main == origin/main == b30bcd1 → ZC was NOT behind; all later gate commits were
  already in the local lineage (my PoC evidence commit sits on top; runtime authority
  is the gate JSONs + persisted stores, not commit order).
- PRESERVED: branch company-pc-main-local-preserved @ f0409e3 (Doctor V3/V4 layer);
  stash company-pc-pre-main-sync-preserve-20260926 — accidentally dropped during a
  later cleanup, RESTORED from recorded SHA 037daf5fa0826be86f2d1e2eb5ffa41384890e86
  and verified (merge commit f0409e3 + untracked data jsons).

## ZC conduct rule going forward

Reason from gate JSONs + persisted readbacks, not chat summaries. Never query
Longbridge/SDW to reproduce persisted evidence. Never write to
08_DATA_ASSETS/longbridge_rescue/* while Luna workers are live.


## SESSION CLOSE ADDendum (2026-09-26 evening)

- Forensic gate: Luna 500-batch runner (work/run_fast_detail_500.py, PID 7360,
  started 14:33) PROVEN ALIVE and advancing (master detail snapshots 239→256 in
  90s, ~11 stocks/min, reached 00305). Root cause of "12 stocks only" report =
  Luna agent 150s response window, NOT runner termination.
- CAUTION: the runner is parented to the Codex runtime pwsh (PID 20596) — closing
  the company Codex session will kill it (previous brute-force runner proved
  session-bound death). Progress already persisted in master DB survives.
- Fast architecture live: one-detail-call-per-stock + anchors; forward daily
  snapshot Task Scheduler job 'Joe CCASS Forward Daily Snapshot' registered
  16:35 HKT Mon-Fri, next run Mon 2026-09-28 (company machine).
- Authoritative semantics unchanged: CHG_ZERO_SAFE_TO_SKIP=NO;
  00700/B01714=SOURCE_SPECIFIC_UNKNOWN.

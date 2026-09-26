# Recent CCASS full-market production backfill V1 — pre-run status

GIT_HEAD=66bfa15df3cb81565bdd35cfedb798eec6453977
WORKTREE_CLEAN=YES

## Safety gate

- Existing rescue DB: G:\我的雲端硬碟\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\08_DATA_ASSETS\longbridge_rescue\longbridge_ccass_daily_rescue_20260925.sqlite
- Read-only PRAGMA quick_check: ok
- Read-only PRAGMA foreign_key_check: 0 rows
- Existing rows: 49,454; stocks: 5; dates: 2026-07-31..2026-09-24
- Existing rescue SHA256: 89F9B115B0382D91CD0C4E63201688FDA550E9974F874DAA03F1ADDCA64408E4
- Free space on G: 188,746,047,488 bytes

## Blocking input

The frozen universe and participant baseline manifests required by the checkpoint are absent from this company-PC repo:

- data/extension_universe_2026_07.json
- data/extension_participants_2026_07_ccassids.json

The existing zc_run_longbridge_rescue_scaled.py can process current Longbridge detail/daily rows, but without the frozen universe and baseline participant manifest it cannot execute the approved baseline-union + rescue-reuse + targeted-SDW algorithm safely. No production backfill was started and no database was modified.

## Status

This is a pre-run blocked state, not a claim of completion. The next safe action is to restore the exact frozen manifests/checkpoint from the authoritative handoff, verify their hashes, then resume from the first pending stock without resetting the rescue DB.

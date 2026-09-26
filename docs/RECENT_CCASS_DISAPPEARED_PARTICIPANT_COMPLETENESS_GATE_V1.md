# Recent CCASS disappeared-participant completeness gate V1

- Scope: 00550, 01750, 08283, 02138, 06182, 01792, 00700
- Baseline: 2026-07-31 Webb CCASS archive
- Current surface: Longbridge roker_holding_detail (seven calls; six completed in this run and 00700 read from the immediately preceding successful runtime evidence)
- Existing rescue: read-only master rescue store, 2026-07-31 onward where available

## Result

The stock-participant union contains **1156** pairs. **8** baseline participants are absent from current Longbridge detail. Existing rescue covers **0** of them, leaving **8** unresolved. Their 2026-07-31 baseline holdings total **1233555**, or **0.015004%** of the seven-stock baseline holdings.

Per stock:

| Stock | Baseline | Current detail | Disappeared | Unresolved | Baseline holding | Disappeared holding |
|---|---:|---:|---:|---:|---:|---:|
| 00550 | 25 | 124 | 2 | 2 | 209182400 | 30000 | | 01750 | 5 | 98 | 0 | 0 | 153720000 | 0 | | 08283 | 11 | 120 | 0 | 0 | 40823178 | 0 | | 02138 | 12 | 167 | 0 | 0 | 769461524 | 0 | | 06182 | 3 | 101 | 1 | 1 | 25808250 | 928000 | | 01792 | 2 | 118 | 0 | 0 | 5074132 | 0 | | 00700 | 223 | 420 | 5 | 5 | 7017530606 | 275555 |

## Completeness decision

CHG_ZERO_SAFE_TO_SKIP=NO remains in force. No participant was converted from missing to zero. The recent-gap reconstruction is **BLOCKED_COMPLETENESS** until targeted SDW/date evidence resolves the eight baseline-only participants (B01161, B01555, B01110, B01714, B01824, B01914; B01555 occurs in two stocks).

No production database, rescue store, or Research Store was modified. No full-market run was started.

## Next exact action

Issue targeted SDW requests for each unresolved stock/date participant set, preserve raw response and source lineage, then rerun this gate. If SDW cannot provide participant/date-level evidence, retain UNKNOWN and do not declare completeness.

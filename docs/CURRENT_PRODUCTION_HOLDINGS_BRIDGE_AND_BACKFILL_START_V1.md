# Current production holdings bridge and backfill gate

The deployed authenticated concentration evidence endpoint and direct production Turso readback agree on all 445 participant IDs and share quantities for `00005` on 2026-09-17. The new internal adapter reads the persisted snapshot, preserves its provenance reference, and leaves canonical participant ID unknown where no cross-source mapping exists. The V2 acceptance JSON contains field-level evidence. A separate durable acceptance artifact is stored under the Owner historical CCASS asset directory.

Webb `shortnames` maps issue 1088 to code 0005 at the sampled 2007 and 2013 dates. The Research Store gap ingestion contains code 00005 participant rows in December 2025 and July 2026. This proves a sampled security bridge through production. Webb `holdings` contains sparse changed holdings, so one row per year does not establish full daily snapshots. The source has no index on `holdings`. The corrected column order is `c1=partID, c2=issueID, c3=holding, c4=atDate`. The first acceptance JSON used the wrong order and is explicitly superseded by V2. A read-only reconstruction for issue 1088 on 2013-03-19 processed 336,413 changed rows into 518 active participant positions, with 88 zero positions and no duplicate change keys. Across the source, all 3,861 observed issue IDs have a `shortnames` entry and all 1,236 observed participant IDs have a `participants` entry. Point-in-time mapping and complete daily reconstruction still need full-corpus validation before a bulk canonical write.

RESULT=PARTIAL_ENGINEERING_GATE_NOT_READY
CURRENT_PRODUCTION_HOLDINGS_SOURCE=Production Turso ccass_snapshots + ccass_holdings + raw_provenance; authenticated concentration evidence API
CURRENT_PRODUCTION_HOLDINGS_READBACK_PASS=YES
CURRENT_SAMPLE_STOCK=00005
CURRENT_SAMPLE_DATE=2026-09-17
CURRENT_PARTICIPANT_ROWS=445
HISTORICAL_CURRENT_PARTICIPANT_BRIDGE_PASS=YES_SAMPLE_LEVEL
PARTICIPANT_COVERAGE_MATRIX_PASS=YES_HONEST_PARTIAL_CLASSIFICATION
EARLIEST_PARTICIPANT_DATE=2007-06-26
LATEST_PARTICIPANT_DATE=2026-09-17
SOURCE_INTEGRITY_CHECK_1=ok
FULL_QUICK_CHECK_DEFERRED=YES
FULL_19Y_PARTICIPANT_BACKFILL_READY=NO
STAGED_BACKFILL_STARTED=NO
BACKFILL_COMPLETED_BATCHES=0
BACKFILL_LAST_COMPLETED_DATE=
BACKFILL_NEXT_BATCH=2007-2010 after readiness gates pass
BACKFILL_RAW_ROWS=0
BACKFILL_CANONICAL_ROWS=0
BACKFILL_READBACK_ROWS=0
BACKFILL_ROW_RECONCILIATION_PASS=NOT_STARTED
HISTORICAL_RESEARCH_SURFACES_PASS=PARTIAL_CURRENT_PRODUCTION_ONLY
RESEARCH_STORE_MUTATED=NO
OWNER_CHAT_CONTINUATION_REQUIRED=NO
OWNER_ACTION_REQUIRED=NO
REMAINING_BLOCKERS=Full-corpus sparse state reconstruction and point-in-time issue mapping remain unvalidated; cross-source canonical participant mappings are not established; full daily coverage is unverified.
NEXT_EXECUTABLE_STAGE=Extend the bounded issue-1088 reconstruction to a validated scalable corpus pipeline; audit point-in-time code intervals and cross-source participant mapping; rerun readiness gates before batch 2007-2010.

WEBB_ISSUES_WITH_ANY_SHORTNAME=3861/3861
WEBB_PARTICIPANTS_WITH_DIRECTORY_ENTRY=1236/1236
WEBB_RECONSTRUCTED_SAMPLE_ACTIVE_ROWS=518
CORRECTED_BRIDGE_EVIDENCE=CURRENT_PRODUCTION_HOLDINGS_BRIDGE_ACCEPTANCE_V2.json
INVALIDATED_EVIDENCE=CURRENT_PRODUCTION_HOLDINGS_BRIDGE_ACCEPTANCE_V1.json

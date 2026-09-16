# WEBBSITE CCASS Row-Level Proof Handoff

## Objective

The target capability is:

ANY HK STOCK → FIRST QUERY → pre-existing historical CCASS → multiple real snapshots → Changes / Big Changes / Concentration → Deep Analysis Ready.

Joe's previous query history must not determine historical depth.

## Friend guidance

`HISTORICAL_CCASS_SOURCE=WEBBSITE original files`

The original WEBBSITE archive is the historical source of record. External Webb crawling is not the primary acquisition path.

## Archive pack

`PACK_PATH=G:\\我的雲端硬碟\\投資 - 享受與豐盛\\AI Projects\\joe-ccass-platform\\docs_reference_evidence\\David_Webb_CCASS_Research_Pack`

- `PACK_FOUND=YES`
- `ARTIFACT_TYPE=WEBBSITE / David Webb original research pack`
- `PRIMARY_DUMP=ccassData-2025-12-27- 600.sql`
- `DUMP_FORMAT=MySQL dump 10.13`
- `LOAD_STYLE=INSERT`
- `HISTORY_START=2007-06-26`
- `HISTORY_END=2025-12-27`
- Core tables: `ccass.holdings`, `ccass.parthold`, `ccass.dailylog`, `ccass.bigchanges`

## Proven stock mappings

The mappings below are proven from archive data, via `enigma.StockListings`:

| Stock | issueID |
|---|---:|
| 00388 | 2516 |
| 01211 | 3452 |
| 01810 | 26628 |

`MAPPING_TABLE=enigma.StockListings`

## Row-level proof status

The archive and mappings have been identified, but row-level extraction and reconstruction have not yet been completed.

- `HOLDINGS_ROWS=NOT_YET_EXTRACTED`
- `PARTHOLD_ROWS=NOT_YET_EXTRACTED`
- `DAILYLOG_ROWS=NOT_YET_EXTRACTED`
- `BIGCHANGES_ROWS=NOT_YET_EXTRACTED`
- `ISSUEDSHARES_ROWS=NOT_YET_EXTRACTED`
- `FULL_SNAPSHOT_RECONSTRUCTION=NOT_RUN`
- `5Y_ROW_LEVEL_PROOF=NOT_YET_PROVEN`
- `10Y_ROW_LEVEL_PROOF=NOT_YET_PROVEN`
- `CANONICAL_CONVERSION=NOT_RUN`
- `CHANGES_ENGINE_ACCEPTANCE=NOT_RUN`

## Failed extraction path

Do not repeat the solid-archive streaming approach.

- `DO_NOT_REPEAT=Streaming tuple parser directly over the solid 17GB archive member`
- `EXTRACTION_METHOD=Streaming tuple parser over solid 17GB member`
- `ELAPSED≈2400 seconds`
- `RESULT=QUERY_READY=FAIL`

The attempt ran for approximately 40 minutes without producing a queryable holdings/parthold/dailylog/bigchanges row-level dataset. It was stopped and must not be retried.

## Next action

Proceed in this exact order:

1. Check safe local SSD free space.
2. Extract the 17GB SQL member once to true local SSD/temp.
3. Do not use the Google Drive/cloud-synced folder when local SSD is available.
4. Perform one sequential scan over the extracted SQL.
5. Build a small local indexed research DB only for issueIDs `2516`, `3452`, and `26628`, plus participants, `StockListings`, `issuedshares`, `holdings`, `parthold`, `dailylog`, and `bigchanges`.
6. Prove the relevant rows.
7. Reconstruct two complete participant snapshots per stock.
8. Prove 5-year and 10-year depth.
9. Perform canonical conversion.
10. Run the existing Changes engine.
11. Measure bootstrap speed.

## Architecture status

`FINAL_PRODUCTION_ARCHITECTURE=NOT_YET_DECIDED`

Candidate only:

`WEBBSITE archive → local historical index → stock-specific first-query bootstrap → Joe canonical persistence → existing analysis engines`

The production architecture decision waits for row-level proof and timing.

## Golden core protection

Protect the already-proven production core:

- Longbridge latest holdings
- Turso/canonical persistence
- Changes
- Big Changes
- Concentration
- reload/restart persistence
- REST/MCP
- 8504
- terminal time ≤90 seconds

Protected stocks: `09999`, `03690`, `00005`, `00006`, `06182`.

## Announcement side note

HKEX Title Search production behavior is proven:

- `prefix.do` HTTP 200
- `titleSearchServlet.do` HTTP 200
- parsing PASS
- direction matches Friend

Current announcement acceptance is blocked by Render `/api/v1/...` edge routing, not by this active CCASS task. Keep the announcement issue separate.

## Resume instructions

1. `git pull`
2. Read this handoff file.
3. Continue only with local SSD SQL extraction, selective local indexing, and row-level proof.
4. Do not restart discovery, external source research, or the solid-archive streaming parser.

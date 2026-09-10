# Webb-site Wayback CCASS Recovery Evidence

## Scope

This folder collects evidence about historic Webb-site / Webb-database CCASS pages and the likely query chain used to retrieve holdings and history.

## High-confidence findings

### Historical CCASS results exist

- The CCASS notes page states Webb has captured, preserved, and analyzed the CCASS participant holdings data.
- It also states records for shares and subscription warrants begin on **2007-06-26** and that temporary counters were coded in later for **2014-11-27** onward.
- Search results for holdings pages show preserved results spanning at least **2010-03-04**, **2022-06-21**, **2024-06-28**, and **2025-10-16**.
- The search snippet for the CCASS notes page reports coverage of **over 100 million records in over 2000 issues**.

### Query mechanism is visible

The current Webb-database mirror exposes a clear chain:

1. Stock code lookup via `orgdata.asp?code=...&Submit=current`
2. Issue page link extraction to `/ccass/choldings.asp?i=<issueID>`
3. Holdings retrieval via `/ccass/choldings.asp?sc=<stockCode>`
4. Participant/date history via `/ccass/cholder.asp?d=<date>&part=<participant>&sort=...&z=False`
5. History view via `/ccass/chistory.asp?i=<issueID>&part=<participant>`
6. Big-moves view via `/ccass/bigchanges.asp?d=<date>`

### Importer / downloader evidence

- The Webb-site Repository Substack explicitly says the repository includes:
  - data dumps of the entire Webb-site Database
  - software for data collection
  - the classic VBScript ASP pages used to present the data
- That is strong repository-level evidence that importer / collection software existed.
- In this session, the exact file/function that performed CCASS importing was not recovered.

## What was not recovered

- No direct downloadable CCASS dataset file was actually fetched in this shell session.
- No exact CCASS importer source file or function name was recovered from the repository itself during this pass.
- No confirmed Wayback-hosted bulk dump of CCASS data was recovered here.

## Local cross-check against the current repo

The current repo code path confirms the same logic pattern:

- stock code -> `orgdata.asp`
- issue ID resolution from `/ccass/choldings.asp?i=...`
- holdings fetch via `/ccass/choldings.asp?sc=...`

This matches the archived / mirror query chain above.

## Bottom line

There is solid evidence for:

- long-running historical CCASS results
- the holding/history query chain
- repository-level existence of data collection software and data dumps

But this pass did not recover a directly downloadable CCASS archive or the exact importer code path.


# Joe CCASS Platform — Reference Website Specification

> Document status: Approved V1 specification, extended with approved evidence
> Evidence audit baseline: `2f264dfd3e7f7b714baa7bdc5c4b8385edb6965a`
> Evidence audit date: 2026-07-24 (Asia/Hong_Kong)
> Evidence update date: 2026-07-24 (Asia/Hong_Kong)
> Readiness: `REFERENCE_SPEC_INCOMPLETE`

## 1. Purpose and authority

This document is the sole formal Product Specification for future milestones and
consolidates the approved evidence currently available for the Reference Website. Future
product milestones may only implement features recorded here. Unknown behaviour must not
be inferred. Historical Repository documents and implementation evidence cited below are
provenance only; they do not override this Specification.

Source: CTO task “Reference Specification Consolidation”; `PROJECT_SPEC.md` §1.

## 2. Evidence status

- `VERIFIED`: explicitly established by version-controlled evidence or a CTO-approved
  milestone with implementation and acceptance evidence.
- `PARTIALLY VERIFIED`: the feature or behaviour is established, but original captures,
  complete interaction details, output samples, or current live verification are missing.
- `UNKNOWN`: available evidence cannot establish whether the feature or behaviour exists.

Source: CTO task “Reference Specification Consolidation”; CTO Pre-Milestone Reference
Website Feature Gap Audit.

## 3. Evidence sources

| ID | Evidence source | What it establishes | Limitations |
|---|---|---|---|
| R1 | `PROJECT_SPEC.md` §1 | Reference Website URL, nine supplied screenshots, access-control boundary | Original screenshot files are not tracked |
| R2 | `PROJECT_SPEC.md` §§5–6 | Normalized feature, navigation, UI, chart, copy, download and language requirements | Some requirements combine several original sources |
| R3 | `PROJECT_SPEC.md` §11 | Screenshot-to-requirement traceability | Screenshots can only be referenced by number |
| R4 | `README.md` “Streamlit 功能” | Current query, report, copy and Markdown download behaviour | Describes this Repository, not the Reference Website |
| R5 | `streamlit_app.py`, `app/streamlit_ui.py`, `ccass_core/report.py` | Current user-visible controls and rendered report sections | No visual parity evidence |
| R6 | `app/api.py`, `app/services/`, `app/models.py` | Current product services and public APIs | Does not establish Reference Website UI |
| R7 | `tests/test_latest_holdings_product.py`, `tests/test_changes_product.py`, `tests/test_big_changes_product.py`, `tests/test_concentration_product.py` | Deterministic product acceptance evidence | Offline fixtures are not production evidence |
| R8 | CTO-approved P1-07, P1-08, P1-09 and P1-10 decisions | Formal completion status for four product vertical slices | Does not approve unrelated UI/history features |
| R9 | Git commits `03e7dc7`, `9800d7a`, `a8ad8fe`, `2f264df` | Versioned implementation evidence for P1-07–P1-10 | No Reference Website assets were added |
| R10 | 2026-07-24 read-only HTTP audit of the Reference Website | HTTP `303` redirect to `share.streamlit.io/-/auth/app` | Protected content was not accessed; redirect query was not retained |
| R11 | Complete tracked-file and Git-history audit at baseline `2f264df` | 81 tracked files, zero images, zero PDFs, four source-parser HTML fixtures | No saved Reference Website DOM, screenshot or export at that baseline |
| R12 | Approved Reference Website evidence `image1.png`–`image7.png` | Current full-page UI, DT Rainbow, Advanced Table Selection, concentration history, downloads and section anchors | Static captures do not establish hidden states or interactions |
| R13 | Approved export `00700_all_ccass_data.csv` | One concrete combined CSV: 12,508 rows including header, 64 columns and nine section labels | One stock and one export instance only |
| R14 | Approved export `00700_all_sections.xlsx` | One concrete Excel workbook with 13 named worksheets and section-specific schemas | One stock and one export instance only |
| R15 | Approved HKEX evidence in `image3.png` | HKEX security page visibly presents 00700 quote, market metrics, chart and selectable periods | Does not establish Reference Website fetch or transformation behaviour |

## 4. Reference Website basic information

- URL:
  `https://webbsite-ccass-tool-r3ntrqvqx9w2k3xffasgwf.streamlit.app/`
- Role: product-function, information-architecture and UX reference only.
- It is not a source of private code, credentials, cookies or non-public data.
- The current public request redirects to Streamlit authentication. Access controls must
  not be bypassed.
- The approved evidence now includes the legacy screenshot references, seven current UI
  captures and concrete CSV and Excel exports. The evidence files are not added to this
  Repository because this update is restricted to the Specification.

Evidence status: `PARTIALLY VERIFIED`. Any behaviour not directly shown: `Evidence Required`.

Sources: `PROJECT_SPEC.md` §1; R10–R15.

## 5. Known screenshot correspondence

| Screenshot evidence | Confirmed subject | Evidence status | Source |
|---|---|---|---|
| Screenshots 1, 4 and 5 | Holdings, announcements, tables, navigation and controls | `PARTIALLY VERIFIED` | `PROJECT_SPEC.md` §11 |
| Screenshot 2 | Copy and downloads | `PARTIALLY VERIFIED` | `PROJECT_SPEC.md` §11 |
| Screenshots 3 and 8 | Desktop and mobile Rainbow | `PARTIALLY VERIFIED` | `PROJECT_SPEC.md` §11 |
| Screenshots 6, 7 and 9 | Chart reading, periods, scenarios, limitations and checklist | `PARTIALLY VERIFIED` | `PROJECT_SPEC.md` §11 |
| Approved `image1.png` | DT Rainbow controls, Price/Daily VWAP/Turnover alignment and stacked distribution chart | `VERIFIED` | R12 |
| Approved `image2.png` | Download CSV, Download Excel, CSV preview and exact section-anchor labels | `VERIFIED` | R12 |
| Approved `image3.png` | HKEX 00700 security quote page | `VERIFIED` for the visible HKEX page only | R15 |
| Approved `image4.png` | Resolved Metadata and Advanced Table Selection | `VERIFIED` | R12 |
| Approved `image5.png` | Concentration history, latest-value table and participant-count history | `VERIFIED` | R12 |
| Approved `image6.png` and `image7.png` | Full-page Reference Website layout, sidebar and product-section sequence | `PARTIALLY VERIFIED` | R12 |

The approved captures verify the visible states recorded in this document. Exact defaults,
valid ranges, hidden options, dynamic transitions and unshown states remain `Evidence Required`.

Source: R3; R11–R15.

## 6. Confirmed navigation order

### 6.1 Sidebar

1. Input Type: Stock Code / Webb-site Issue ID
2. Stock Code / Issue ID
3. Timeout
4. Announcement Period
5. Source Mode
6. Data Date
7. History Range
8. Top N
9. Percentage Basis
10. Fetch

Evidence status: `PARTIALLY VERIFIED`. Any behaviour not directly shown: `Evidence Required`.

Source: `PROJECT_SPEC.md` §6.1; Screenshots 1, 4 and 5 group trace in
`PROJECT_SPEC.md` §11.

### 6.2 Main page

1. Fetch Summary
2. All Tables
3. DT Rainbow
4. HKEX Announcements
5. 財技事件 Events
6. 董事高管 Officers
7. Price & Turnover
8. Company
9. Holdings
10. Changes
11. Big Changes
12. Concentration
13. Price History
14. Raw Previews
15. Copy for ChatGPT
16. Downloads

Evidence status: `PARTIALLY VERIFIED`. Any behaviour not directly shown: `Evidence Required`.

Source: `PROJECT_SPEC.md` §6.1; Screenshots 1, 4 and 5 group trace in
`PROJECT_SPEC.md` §11; exact anchor row in approved `image2.png` (R12).

Resolved Metadata, Advanced Table Selection, Full Summary and All Parsed Tables are also
visible page blocks. They are specified in §13 but are not additional anchor labels in the
approved anchor row.

## 7. Feature inventory

The original audit categories below are retained for traceability. The exact approved
section-anchor order is §6.2, and newly evidenced page blocks and export surfaces are
specified in §13. Repository implementation status does not alter the Reference Website
order.

| # | Feature | User-visible purpose | Required inputs | Expected output | Evidence status | Current implementation | Related milestone | Completion evidence | Remaining gap | Sources |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | Query/Input and Sidebar Controls | Select the stock and visible query scope | Input type, code/issue ID and the visible sidebar controls | Fetch action and resolved query output | `PARTIALLY VERIFIED` | Partially matched | P1-07 | Stock-code input and Fetch are visible | Exact defaults, ranges, options, Issue ID workflow and all validation states: `Evidence Required` | `PROJECT_SPEC.md` §§5.1, 6.1; Screenshots 1, 4 and 5 group; R12 |
| 2 | Fetch Summary | Show the result of each parsed section | Section fetch and table-selection results | Section, Status, Tables found, Selected table index, Latest date/data date and Error | `VERIFIED` | Partially matched | P1-07 | Approved Excel contains `fetch_summary` with the visible six-column schema | Unshown status variants and UI state transitions: `Evidence Required` | R12; R14 |
| 3 | All Tables | Review all fetched sections in one page | Available section results | Navigable complete tables | `PARTIALLY VERIFIED` | Partially matched | P1-07–P1-10 | Full-page capture shows All Parsed Tables and approved exports contain section tables | Exact All Tables anchor target, pagination and no-data presentation: `Evidence Required` | R12–R14 |
| 4 | DT Rainbow | Review participant distribution across displayed dates | Displayed participant count, displayed history-date count and Combine Price checkbox | Generate button, Price/Daily VWAP/Turnover chart and stacked CCASS participant distribution chart | `VERIFIED` for the captured state | Not implemented | None | Approved `image1.png` | Tooltips, error/empty/loading states and control limits: `Evidence Required` | R12 |
| 5 | HKEX Announcements | Review official company announcements | Stock and announcement period | Count and table containing publish time, category, title, file information and official URL | `PARTIALLY VERIFIED` | Not implemented | None | Visible heading, anchor and legacy table evidence | Current rows, empty/error states and export: `Evidence Required` | R3; R12 |
| 6 | Company | Review the security/company identity | Stock code or verified issue identity | Name, stock code, issue ID, lookup method and lookup status | `PARTIALLY VERIFIED` | Partially matched | P1-07 | Resolved Metadata capture and approved metadata worksheet | Unshown identifier/history fields and error states: `Evidence Required` | R12; R14 |
| 7 | Holdings | Review participant ranking and holdings | Verified latest snapshot and display limit | Participant, stake/percentage, holding, totals, Top 5/10 and metadata | `VERIFIED` | Fully matched product capability | P1-07 | CTO-approved `03e7dc73b324a642aed39bb2500f5228a0473970` | Reference page composition remains part of All Tables/UI parity | `PROJECT_SPEC.md` §§5.3, 6.2; Screenshots 1, 4 and 5 group; R7–R9 |
| 8 | Changes | Compare two exact CCASS snapshots | Compare date and snapshot date | Before/after, share and percentage changes, new/removed participants and metadata | `VERIFIED` | Fully matched product capability | P1-08 | CTO-approved `9800d7a6ed46893bcffecc8e604eb23c23eb4acf` | Reference page composition remains part of All Tables/UI parity | `PROJECT_SPEC.md` §§5.4, 6.1; Screenshots 1, 4 and 5 group; R7–R9 |
| 9 | Big Changes | Filter Changes by a configured threshold | Exact snapshot pair and threshold | Threshold-qualified participant changes with metadata and warnings | `VERIFIED` | Fully matched product capability | P1-09 | CTO-approved `a8ad8fe7f9b1c23d11b5b560289d38c1d5300230` | Reference page composition remains part of All Tables/UI parity | `PROJECT_SPEC.md` §§5.4, 6.1; Screenshots 1, 4 and 5 group; R7–R9 |
| 10 | Possible Transfer Patterns | Show objective pairs of similar increases/decreases | Verified Changes and configured tolerance | Possible-pattern pairs, difference, tolerance and disclaimer | `PARTIALLY VERIFIED` | Partially matched | Legacy compute/report | Legacy evidence establishes the concept | Exact current Reference UI, inputs and output: `Evidence Required` | R3; R5 |
| 11 | Concentration — Exact Snapshot | Review current participant concentration | One complete exact-date snapshot | Ranking, participant count, tracked totals, Top 1/5/10, metadata and warnings | `VERIFIED` | Fully matched product capability | P1-10 | CTO-approved `2f264dfd3e7f7b714baa7bdc5c4b8385edb6965a` | Historical timeline is a separate feature | `PROJECT_SPEC.md` §§5.6, 6.1–6.2; Screenshots 1, 4 and 5 group; R7–R9 |
| 12 | Concentration History | Review concentration and participant-count history | Dated concentration observations | Top 5 + NCIP and Top 10 + NCIP lines, latest-value table, and CCASS participant-count line | `VERIFIED` for the captured state | Not implemented | None | Approved `image5.png`; approved concentration export | Product implementation is absent; unshown interactions: `Evidence Required` | R12–R14 |
| 13 | Price History | Review dated price and trading data | Stock and available dated records | Date, Close, Open, High, Low, Volume, Turnover and VWAP; raw preview also exposes bid/ask and adjusted fields | `VERIFIED` for supplied export schemas | Not implemented | None | Approved CSV and Excel exports | Product implementation is absent; source-refresh and missing-date behaviour: `Evidence Required` | R13–R15 |
| 14 | Raw Previews | Inspect parsed source tables | Parsed tables by section and table index | Expandable previews; exported index, shape, columns and preview sample | `VERIFIED` for supplied visible/exported state | Partially matched | Legacy Streamlit UI | Approved full-page captures and `raw_table_previews` worksheet | Exact expansion interaction and truncation rules: `Evidence Required` | R12; R14 |
| 15 | Copy for ChatGPT / Copy Report | Copy prepared report content | Rendered page content | Prepared text area and copy action | `PARTIALLY VERIFIED` | Partially matched | Legacy Streamlit UI | Full-page capture shows Copy for ChatGPT | Exact payload, formatting and clipboard states: `Evidence Required` | R3; R12 |
| 16 | Downloads | Download combined and section data | Available parsed section results | Combined CSV, Excel workbook, CSV preview and visible section-specific download controls | `VERIFIED` for supplied captures and two supplied exports | Partially matched | Legacy UI/collector | Approved `image2.png`, CSV and Excel evidence | Exact filenames/content for unsupplied downloads and failure states: `Evidence Required` | R12–R14 |
| 17 | `zh_HK` / English i18n | Change display language without refetching | Locale and existing query result | Localized UI, chart, report and export labels | `PARTIALLY VERIFIED` | Not implemented | None | Legacy evidence only | Current control, translations, fallback and refetch behaviour: `Evidence Required` | R2 |
| 18 | Desktop/Mobile Responsive UX | Use tables, charts, legends and controls on wide and narrow screens | Desktop and mobile viewport | Readable and operable responsive layout | `PARTIALLY VERIFIED` | Cannot determine from available evidence | None | Legacy desktop/mobile captures exist | Current breakpoint, sidebar and interaction behaviour: `Evidence Required` | R3 |
| 19 | Chart Interpretation / Help Content | Explain axes, observable patterns, limitations and cross-checks | Rainbow, concentration, price and announcement context | Objective help text and disclaimers | `PARTIALLY VERIFIED` | Not implemented as a Reference help experience | None | Legacy teaching captures exist | Exact current placement and copy: `Evidence Required` | R3 |
| 20 | Other protected-site features | Establish whether additional features exist outside approved captures | Further approved evidence | Verified additional inventory only when directly observed | `UNKNOWN` | Cannot determine | None | None | Anything outside R12–R15: `Evidence Required` | R10–R15 |

## 8. Completed product capabilities

| Feature | Product status | Approved evidence | Reference evidence status |
|---|---|---|---|
| Latest Holdings | COMPLETED | P1-07; `03e7dc73b324a642aed39bb2500f5228a0473970` | `VERIFIED` |
| Changes | COMPLETED | P1-08; `9800d7a6ed46893bcffecc8e604eb23c23eb4acf` | `VERIFIED` |
| Big Changes | COMPLETED | P1-09; `a8ad8fe7f9b1c23d11b5b560289d38c1d5300230` | `VERIFIED` |
| Concentration — Exact Snapshot | COMPLETED | P1-10; `2f264dfd3e7f7b714baa7bdc5c4b8385edb6965a` | `VERIFIED` |

Source: R7–R9; CTO-approved P1-07–P1-10 decisions.

These approvals cover the product capabilities named above. They do not establish
Reference Website page composition, visual parity, historical charts or unrelated
delivery surfaces.

## 9. Unfinished features

### 9.1 Partially matched

- Query/Input and Sidebar Controls
- Fetch Summary
- All Tables
- Company
- Possible Transfer Patterns
- Raw Previews
- Copy for ChatGPT / Copy Report
- Downloads

Source: Feature Inventory §7; R4–R7.

### 9.2 Not implemented

- DT Rainbow
- HKEX Announcements
- Concentration History
- Price History
- `zh_HK` / English i18n
- Consolidated Chart Interpretation / Help Content

Source: Feature Inventory §7; `PROJECT_SPEC.md` §§5–6.

## 10. Unknown features and behaviour

- Any feature currently hidden behind the Streamlit authentication redirect and not
  recorded in `PROJECT_SPEC.md`.
- Exact pixel layout and styling of the Reference Website.
- Exact default values and valid ranges for all Reference controls.
- Complete empty, partial, loading, error, cached and stale UI states.
- Current mobile interactions, sidebar behaviour, chart gestures and legend behaviour.
- Exact language-switch behaviour on the Reference Website.
- Exact contents and filenames for downloads other than the supplied CSV and Excel: `Evidence Required`.
- Whether the protected live site differs from the approved captures: `Evidence Required`.

Evidence status: `UNKNOWN`.

Source: `PROJECT_SPEC.md` §1; R10–R11.

## 11. Missing Evidence Checklist

The supplied UI captures, combined CSV and Excel workbook close several earlier evidence
items. Anything below remains outside milestone scope until directly observed.

### 11.1 Query, controls and workflow

- Evidence Required — exact default value, valid range and option list for every sidebar
  control.
- Evidence Required — complete Webb-site Issue ID query from input through result.
- Evidence Required — validation messages and behaviour for invalid stock/issue input.
- Evidence Required — loading, empty, partial, error, cached and stale states.
- Evidence Required — fetch retry, timeout and cancellation behaviour.

### 11.2 Tables, charts and interactions

- Evidence Required — exact Full Summary column labels and all status variants.
- Evidence Required — Advanced Table Selection behaviour when a selected table is invalid,
  empty or changes after a rerun.
- Evidence Required — DT Rainbow tooltips, legend interaction, missing-date display and
  download output.
- Evidence Required — exact chart hover, zoom, mobile and narrow-screen behaviour.
- Evidence Required — Raw Table Preview expansion, truncation and serialization rules.

### 11.3 Sections and outputs

- Evidence Required — HKEX Announcements empty/error states and complete sample export.
- Evidence Required — exact visible sub-section layout for 財技事件 Events and 董事高管
  Officers.
- Evidence Required — exact Copy for ChatGPT payload, clipboard success/failure state and
  formatting rules.
- Evidence Required — concrete samples and filenames for every download other than
  `00700_all_ccass_data.csv` and `00700_all_sections.xlsx`.
- Evidence Required — any PDF, JSON, Markdown or announcement download offered by the
  Reference Website.

### 11.4 Access and version identity

- Evidence Required — approved V1 version/date identity for the captured Reference Website.
- Evidence Required — whether the protected live site differs from the approved captures.
- Evidence Required — authorized HTML/DOM or read-only access if behaviour not visible in
  supplied captures must be specified.

Source: R10–R15.
## 12. Reference Specification Readiness

`REFERENCE_SPEC_INCOMPLETE`

The approved captures and supplied CSV/Excel exports now verify the visible page sequence,
key output schemas, DT Rainbow captured state, Advanced Table Selection and download
surfaces recorded below. The items explicitly labelled `Evidence Required` remain outside
milestone scope and must not be inferred.

Source: R10–R15; Missing Evidence Checklist §11; Approved Evidence Detail §13.
## 13. Approved Evidence Detail

This section extends the existing structure with the latest approved evidence. It records
only visible labels, values, tables, charts and export structures. It does not specify
unseen behaviour.

### 13.1 Approved evidence register

| Evidence | Directly observable scope |
|---|---|
| `image1.png` | DT Rainbow heading and controls; Price/Daily VWAP/Turnover chart; stacked participant chart |
| `image2.png` | Download CSV, Download Excel, CSV content preview and exact section-anchor row |
| `image3.png` | HKEX 00700 quote page and visible market/chart controls |
| `image4.png` | Resolved Metadata, Advanced Table Selection and summary cards |
| `image5.png` | Concentration history, latest values and CCASS participant-count history |
| `image6.png`, `image7.png` | Full-page Reference Website, sidebar and ordered product sections |
| `00700_all_ccass_data.csv` | Combined CSV structure and one concrete 00700 export |
| `00700_all_sections.xlsx` | Multi-sheet Excel structure and one concrete 00700 export |

### 13.2 Query / Input

- The full-page captures show a left sidebar labelled Input and a selectable Input Type.
- Stock Code is a visible input mode; the supplied result is for stock `00700`.
- The page also identifies a Webb-site Issue ID after resolution.
- Timeout, announcement period, source mode, data date/history, Top N and percentage-basis
  controls remain part of the confirmed sidebar order in §6.1.
- Exact defaults, valid ranges, complete options and invalid-input behaviour: `Evidence Required`.

Source: R12; §6.1.

### 13.3 Fetch workflow

The captured completed state shows this visible sequence:

1. Sidebar query controls and Fetch action.
2. Resolved Metadata.
3. Advanced Table Selection.
4. Summary metric cards and settlement note.
5. Fetch Summary and product sections.
6. Full Summary, All Parsed Tables, Raw Table Previews, Copy for ChatGPT and Downloads.

The precise network sequence, retry rules, loading transitions and error recovery are
`Evidence Required`.

Source: approved full-page captures R12.

### 13.4 Resolved Metadata

The captured cards show:

- Stock code.
- Stock name.
- Webb-site issue ID.
- ID lookup status.
- ID lookup method; the supplied example states `extracted from URL`.

The supplied export instance records stock `00700`, stock name `TENCENT HOLDINGS LIMITED
騰訊控股有限公司`, issue ID `3601` and lookup status `success`.

Source: approved `image4.png`; R14 `metadata` worksheet.

### 13.5 Advanced Table Selection

- The section is expandable and labelled `Advanced table selection`.
- Visible selectors are Company / orgdata, Holdings, Changes, Big Changes, Concentration
  and Price History.
- Each selector visibly offers `Auto select`; the open example also lists parsed table
  choices with table number and shape.
- Visible guidance states to leave flags on Auto select unless a parsed table is missing,
  and that manual choices apply after the page reruns.
- The supplied Fetch Summary records Tables found and Selected table index for each of the
  six sections.
- Behaviour for invalid, empty or changed selections: `Evidence Required`.

Source: approved `image4.png`; R14 `fetch_summary` and `raw_table_previews` worksheets.

### 13.6 Fetch Summary

The approved Excel output contains one row each for Company / orgdata, Holdings, Changes,
Big Changes, Concentration and Price History, with columns:

- Section
- Status
- Tables found
- Selected table index
- Latest date / data date
- Error

Only the supplied `success` state is fully evidenced. Other status values and their UI
presentation are `Evidence Required`.

Source: R14 `fetch_summary` worksheet.

### 13.7 HKEX Announcements

- `HKEX Announcements` is a visible section and section anchor.
- Legacy approved screenshot evidence shows publish time, category, title, file information
  and official URL columns.
- The current full-page evidence shows the section heading and an informational status area.
- Exact current rows, empty/error states and downloadable output: `Evidence Required`.

Source: R3; R12.

### 13.8 財技事件 Events

- `財技事件 Events` is an exact visible section-anchor label.
- The supplied combined CSV contains `Corporate Events`, `Share Capital Changes` and
  `Buybacks` section values.
- The Excel workbook contains `events`, `share_capital` and `buybacks` worksheets.
- `events` fields: announced, year_end, type, amount, value_in_quote_ccy, new_old, ex_date,
  distribution, notes, event_id and event_details_url.
- `share_capital` fields: announce_date, shares_million, shares_approx, reason,
  reason_tags and change_date.
- `buybacks` fields: announce_date, buyback_date, amount_wan, shares_wan, high_price,
  low_price, method and currency.
- Exact visible grouping, labels and empty/error presentation: `Evidence Required`.

Source: approved `image2.png`; R13–R14.

### 13.9 董事高管 Officers

- `董事高管 Officers` is an exact visible section-anchor label.
- The combined CSV contains a `Managers F10` section.
- The Excel workbook contains `managers_f10` with fields: name, positions, tenure_from,
  tenure_to, is_current, sex, age, education, salary and biography.
- Exact visible cards/table layout and empty/error presentation: `Evidence Required`.

Source: approved `image2.png`; R13–R14.

### 13.10 Price & Turnover

- `Price & Turnover` is an exact visible section-anchor label.
- The Rainbow evidence shows a chart labelled `Price / Daily VWAP / Turnover aligned with
  CCASS rainbow`, with Close Price and Daily VWAP lines and Turnover bars.
- The supplied metadata includes latest_price, latest_price_volume,
  latest_price_turnover and latest_price_vwap.
- The approved HKEX screenshot visibly shows the 00700 quote page, market metrics, a chart
  and selectable time periods. It does not prove how the Reference Website fetches or
  transforms HKEX data.
- Fetch source, refresh timing and error behaviour: `Evidence Required`.

Source: approved `image1.png`, `image3.png`; R14 `metadata` worksheet.

### 13.11 DT Rainbow

The captured DT Rainbow state directly shows:

- Heading `CCASS 中央結算持股分佈 - 00700`.
- A displayed Top N participant control; the captured value is `12`.
- A displayed historical-date-count control; the captured value is `26`.
- A red Generate button.
- A checked Combine Price control.
- An upper Price/Daily VWAP/Turnover chart aligned to dates.
- A lower stacked-area CCASS participant distribution chart aligned to dates.

The captured numbers are sample state values, not confirmed defaults. Defaults, limits,
legend interaction, tooltips, missing-date rules and downloads are `Evidence Required`.

Source: approved `image1.png`.

### 13.12 Holdings

The approved exports establish:

- Combined CSV section label `Holdings`.
- Excel worksheet `holdings`.
- Fields Rank, Participant, CCASS ID, Holding, Stake % and Cumulative %.
- The supplied workbook contains totals including named holdings, unnamed investor
  participants, Total in CCASS, Securities not in CCASS and Issued securities.

Source: R13–R14; CTO-approved P1-07.

### 13.13 Changes

The approved exports establish:

- Combined CSV section label `Changes`.
- Excel worksheet `changes`.
- Fields Participant, Change, Change %, Holding after and Stake after.
- Raw table preview fields Row, CCASS ID, Name, Holding, Change, Stake %, Stake Δ % and
  Last holding.
- A separate raw summary table exposes Trading date, Volume and Turnover.

Source: R13–R14; CTO-approved P1-08.

### 13.14 Big Changes

The approved exports establish:

- Combined CSV section label `Big Changes`.
- Excel worksheet `bigchanges`.
- Normalized fields Date, Participant and Change %.
- Raw preview fields Row, Date Y-M-D, Participant, Change and Previous change.

Source: R13–R14; CTO-approved P1-09.

### 13.15 Concentration

- The supplied `concentration` worksheet contains Date, Top 5 %, Top 10 %,
  Top 10 + NCIP % and Stake in CCASS %.
- The approved history capture shows Top 5 + non-circulating shares and Top 10 +
  non-circulating shares as dated lines, a latest-values table and a dated CCASS
  participant-count line.
- The captured latest-value date is `2026-07-23`; values shown in the supplied export are
  evidence for that sample only.
- Chart interaction and missing-date behaviour: `Evidence Required`.

Source: approved `image5.png`; R13–R14; CTO-approved P1-10 for exact-snapshot concentration.

### 13.16 Price History

- Combined CSV section label: `Price History`.
- Excel worksheet `price_history` fields: Date, Close, Open, High, Low, Volume, Turnover
  and VWAP.
- Raw preview additionally exposes Bid, Ask, adjusted price/volume fields and Total Return.
- Source-refresh, adjustment rules and missing-date behaviour: `Evidence Required`.

Source: R13–R15.

### 13.17 Full Summary

- `Full Summary` is a visible heading in the approved full-page capture.
- A multi-row summary table and a note/status column are visible.
- Exact column labels, row rules and all status variants: `Evidence Required`.

Source: approved full-page evidence R12.

### 13.18 All Parsed Tables

- `All Parsed Tables` is a visible heading.
- Holdings, Changes, Big Changes, Concentration and Price History are visible as ordered
  parsed-table sections in the full-page capture.
- Visible warning/information callouts accompany sections in the captured state.
- Exact callout text, pagination, truncation and no-data behaviour: `Evidence Required`.

Source: approved full-page evidence R12.

### 13.19 Raw Table Preview

- `Raw Table Previews` is a visible heading with expandable table entries.
- The Excel `raw_table_previews` worksheet fields are section, table_index, shape, columns
  and preview.
- The supplied workbook contains 20 preview rows covering Company / orgdata, Holdings,
  Changes, Big Changes, Concentration and Price History.
- Expansion and preview truncation rules: `Evidence Required`.

Source: R12; R14.

### 13.20 Copy for ChatGPT

- `Copy for ChatGPT` is an exact visible section-anchor label and a visible page heading.
- The captured page shows a prepared text area and a red copy action.
- Exact payload structure, maximum length, clipboard confirmation and failure behaviour:
  `Evidence Required`.

Source: approved full-page evidence R12; legacy Screenshot 2 trace R3.

### 13.21 Download CSV

- The download section heading is `Download This Stock`.
- A visible button is labelled `Download All CCASS Data CSV`.
- Visible explanatory text states that one CSV contains Holdings, Changes, Big Changes and
  Concentration with source URL, fetched time and data meaning.
- The supplied concrete CSV also contains Price History, Corporate Events, Share Capital
  Changes, Buybacks and Managers F10; this records the supplied export instance only.

Source: approved `image2.png`; R13.

### 13.22 Download Excel

- A visible button is labelled `Download Excel`.
- The supplied workbook contains 13 worksheets in this exact order:
  `metadata`, `fetch_summary`, `source_urls`, `holdings`, `changes`, `bigchanges`,
  `concentration`, `price_history`, `events`, `share_capital`, `buybacks`, `managers_f10`
  and `raw_table_previews`.

Source: approved `image2.png`; R14.

### 13.23 Download Files

Legacy approved evidence shows section-specific download controls for Holdings, Changes,
Big Changes, Concentration and Price, plus Markdown Report, Excel - All Sections and Raw
Tables JSON. Exact current filenames and concrete content for those unsupplied downloads
are `Evidence Required`.

Source: legacy Screenshot 2 trace R3; current full-page/download captures R12.

### 13.24 CSV Preview

- `CSV content preview` is a visible expandable block.
- The captured block is labelled `First 80 CSV lines`.
- The preview visibly begins with the combined CSV header and Holdings records.
- The supplied CSV contains 12,508 rows including its header, 64 columns and these nine
  section values: Holdings, Changes, Big Changes, Concentration, Price History, Corporate
  Events, Share Capital Changes, Buybacks and Managers F10.

Source: approved `image2.png`; R13.

### 13.25 Sidebar Navigation and Section Anchors

The exact visible section-anchor row is:

`Fetch Summary | All Tables | DT Rainbow | HKEX Announcements | 財技事件 Events |
董事高管 Officers | Price & Turnover | Company | Holdings | Changes | Big Changes |
Concentration | Price History | Raw Previews | Copy for ChatGPT | Downloads`

The full-page captures show the persistent left sidebar beside the page content. Exact
sticky/collapse/mobile navigation behaviour is `Evidence Required`.

Source: approved `image2.png`, `image6.png` and `image7.png`.

## 14. Approved Export Schemas

### 14.1 Combined CSV

The supplied `00700_all_ccass_data.csv` has:

- Used range equivalent: 12,508 rows × 64 columns.
- Identity/provenance fields: section, row_meaning, stock_code, stock_name,
  webbsite_issue_id, fetched_time, data_date_or_latest_date and source_url.
- Section-specific columns spanning holdings, changes, concentration, price, events,
  capital changes, buybacks and officers.
- Blank cells where a column does not apply to a section row.

This is one approved sample, not proof of unshown filename rules or other-stock behaviour.

Source: R13.

### 14.2 Excel workbook

The supplied `00700_all_sections.xlsx` has 13 worksheets and preserves metadata, fetch
summary, source URLs, normalized section tables and raw table previews separately. The
worksheet names and visible schemas in §§13.4–13.24 are normative only for the supplied
approved evidence. Behaviour outside the supplied instance is `Evidence Required`.

Source: R14.

## 15. Evidence Rule for Future Work

The Reference Website remains the only Product Specification. Future work may implement
only behaviour recorded as directly observed and verified here. Any item labelled
`Evidence Required` is explicitly outside scope until approved evidence is added to this
document. No product redesign, workflow optimization, inferred behaviour or V2 concept is
authorized by this update.

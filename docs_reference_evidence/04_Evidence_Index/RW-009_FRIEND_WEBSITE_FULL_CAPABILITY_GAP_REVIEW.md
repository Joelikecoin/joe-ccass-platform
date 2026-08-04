# RW-009 Friend Website Full Capability Gap Review

## 1. Evidence Basis

This review uses only the evidence preserved in the workspace:

- `docs_reference_evidence/04_Evidence_Index/REFERENCE_EVIDENCE.md`
- `docs_reference_evidence/04_Evidence_Index/RW-003_WEBSITE_INTERACTION_ALIGNMENT_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/RW-004_DOCUMENTED_ARCHITECTURE_ALIGNMENT_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/RW-005_PRICE_HISTORY_REQUIREMENT_DECISION.md`
- `docs_reference_evidence/04_Evidence_Index/RW-006_COMPANY_INFORMATION_LAYER_ALIGNMENT_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/RW-006-A_COMPANY_INFORMATION_DATA_SOURCE_DECISION.md`
- `docs_reference_evidence/04_Evidence_Index/RW-007_STOCK_EVENTS_ALIGNMENT_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/RW-008_OFFICERS_ALIGNMENT_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/RW-008-A_OFFICERS_DATA_SOURCE_DECISION.md`
- `docs_reference_evidence/04_Evidence_Index/ND-01_FINAL_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/ND-02_FINAL_REVIEW.md`
- current Joe Platform implementation evidence in `app/`, `ccass_core/`, `streamlit_app.py`, and `app/api.py`

Important evidence constraints:

- Friend screenshots / PDF assets are not directly available in the current workspace, so exact pixel-level parity is not claimed unless the preserved MD evidence supports it.
- Where a capability is known to exist in the Friend experience but the source or visible surface is not sufficiently evidenced, this review uses `Deferred` or `Unconfirmed` rather than guessing.

## 2. Full Capability Comparison Table

| Capability | Friend Evidence | Joe Status | Classification |
|---|---|---|---|
| Full Report structure | The preserved reference evidence shows a report-first experience with a structured section flow, section anchors, and progressive disclosure for detailed content. | Joe renders a structured report with ordered sections, summary/detail separation, and preserved section navigation. | Completed |
| Summary | The reference evidence places summary content early in the report experience. | Joe exposes a full summary surface and keeps it aligned with the main report flow. | Completed |
| Metadata | The reference evidence preserves metadata and provenance alongside the report experience. | Joe shows source, date / as-of, and warning metadata in the report and UI surfaces. | Completed |
| Holdings | Holdings are a core visible report capability in the reference experience. | Joe exposes holdings tables and report surfaces. | Completed |
| Changes | Changes are a visible core report capability in the reference experience. | Joe exposes changes report surfaces. | Completed |
| Big Changes | Big Changes are part of the reference report experience. | Joe exposes a dedicated big-changes surface. | Completed |
| Concentration | Concentration is a visible reference capability. | Joe exposes concentration report surfaces and supporting views. | Completed |
| Historical Information | The reference evidence includes historical presentation and date-based context. | Joe exposes historical snapshot / history views and related metadata. | Completed |
| Price History | The reference evidence supports a visible price-history surface with market-context usage. | Joe implements price history with source metadata, date range support, OHLCV-style fields where available, and a visible report section. | Completed |
| Announcements | The reference evidence shows HKEX Announcements as a visible company-information capability. | Joe has source-backed HKEXnews announcements in the API, report, and Streamlit surfaces. | Completed |
| Stock Events | The reference evidence shows an exact visible Events anchor and export evidence for corporate events / share capital changes / buybacks, but the current source evidence still says Webb-site only. | Joe has no source-backed stock-events implementation; only an unavailable / placeholder surface is present. | Deferred |
| Officers | The reference evidence shows an exact visible Officers anchor and Managers F10 export evidence. | Joe has no source-backed officers implementation; only an unavailable / placeholder surface is present. | Deferred |
| Capital Information | The reference evidence supports share-capital / company-capital context, but the workspace evidence is weaker on a separately visible page surface. | Joe has no dedicated capital-information source or visible surface. | Unconfirmed |
| Page layout | The reference experience is report-first and organized around a readable page layout. | Joe uses a report-first Streamlit layout with guided entry and report sections. | Completed |
| Navigation | The reference evidence preserves report navigation / jump-link style access. | Joe provides navigation anchors and section navigation. | Completed |
| Expand / collapse | The reference evidence favors progressive disclosure for detailed content. | Joe uses expandable sections for detailed report content and optional views. | Completed |
| Loading behavior | The reference evidence implies staged loading rather than blocking heavy surfaces up front. | Joe shows progress feedback and staged loading during fetch and report build. | Completed |
| Optional heavy components | The reference evidence treats heavy visual content as user-triggered. | Joe keeps DT Rainbow and similar heavy surfaces opt-in. | Completed |
| Download / Copy workflow | The reference evidence preserves export / copy style interactions, but the exact button placement is not fully reconstructible from the preserved text evidence alone. | Joe provides Copy for ChatGPT, copy report, and download artifacts, though the exact placement / choreography differs from the reference. | Alignment Required |
| Tables | The reference experience relies heavily on tables for visible data presentation. | Joe renders report tables and UI preview tables. | Completed |
| Charts | The reference evidence includes charted price / turnover and other visual surfaces. | Joe renders charts / visual surfaces for supported data views. | Completed |
| Historical views | The reference experience includes historical views and history-aware presentation. | Joe exposes historical and date-bounded report surfaces. | Completed |
| Metadata display | The reference experience surfaces source and date context clearly. | Joe displays source, dates, warnings, and provenance metadata. | Completed |
| Warning handling | The reference experience preserves warning and fallback visibility. | Joe surfaces structured warnings, unavailable states, and fallback notes. | Completed |

## 3. Remaining Gaps

- Stock Events remains a deferred gap. The friend evidence confirms the capability exists, but the current source direction is still Webb-site-only in the preserved evidence set, so Joe does not yet have an approved source-backed implementation.
- Officers remains a deferred gap. The friend evidence confirms the capability, but the source decision still needs stronger operational evidence before implementation can be approved.
- Capital Information remains an unconfirmed / lower-confidence gap. The reference evidence supports company-capital context, but the visible surface requirement is not as strongly evidenced as announcements, events, or officers.
- Download / Copy placement is aligned in function, but not guaranteed to match the friend layout exactly.
- Exact friend-side choreography for some expandable / detail surfaces remains partially unconfirmed because the screenshot / PDF assets are not directly available here.

## 4. Completed Alignment

The following areas are already aligned well enough that they are not currently visible capability gaps:

- Full Report structure
- Summary
- Metadata
- Holdings
- Changes
- Big Changes
- Concentration
- Historical Information
- Price History
- Announcements
- Page layout
- Navigation
- Expand / collapse behavior
- Loading behavior
- Optional heavy components
- Tables
- Charts
- Historical views
- Metadata display
- Warning handling

## 5. Priority Recommendation

1. Close the remaining company-information gaps in this order: Stock Events, Officers, then Capital Information evidence / approval.
2. Treat Download / Copy placement as secondary UI alignment work, not a blocker for the core replication path.
3. No further core-report work appears necessary for the currently evidenced surfaces; the remaining work is concentrated in the company-information layer and exact UI polish.

## 6. Unconfirmed Items

- The exact friend-side button placement and spacing for Copy / Download actions.
- The exact visual layout of the friend Capital Information surface, if it is meant to be user-facing at all.
- Whether the friend implementation uses any additional hidden variation in the detailed historical / chart presentation that is not captured by the preserved text evidence.
- Whether any remaining friend-side section ordering differences exist beyond the preserved report anchors and section names.

## 7. Governance Verification

Confirmed:

- No code changed
- No tests changed
- No data source added
- No collector created
- No requirements promoted
- Friend evidence remains reference only

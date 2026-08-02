# ND-01 Reality Gap Review

This is a documentation and analysis artifact only.

Source legend:

- Source: Friend PDF
- Source: Existing Spec
- Source: Existing Implementation
- Source: Reference Evidence

Note: the named PDF files and `00_Source_Documents` were not present in this workspace during review, so the friend-side findings below are grounded in the preserved Reference Evidence register and the existing reference-site evidence already captured there.

## 1. Executive Summary

Joe Platform V1 already covers the core stock-code query flow, source-mode routing, progress feedback, holdings/change/concentration reporting, copy-payload generation, and a limited download surface.

The friend reference evidence adds three clear areas of divergence:

- richer source-provenance language, especially explicit `source` and `data_as_of`
- broader external-source ownership, including HKEXnews, 同花順 F10, and SDW / local DB-first routing
- richer presentation surfaces, especially price history, announcements, charting, historical views, and broader preview/export affordances

Most of the friend-only surface should be treated as Reference Only or ND-01 Candidate rather than being promoted into Joe Platform V1 requirements by default.

## Evidence Coverage Status

Evidence already covered:

- Friend website UI evidence as preserved in `REFERENCE_EVIDENCE.md`, including the stock lookup flow, report/navigation surfaces, and screenshot-derived UI notes.
- Friend report structure as preserved in `REFERENCE_EVIDENCE.md`, including the visible report sections, downloads, raw previews, and concentration-history notes.
- Friend MCP/source architecture evidence from RE-009, including the source ownership matrix, the architecture pattern note, and the provenance metadata note.
- Friend data-source ownership matrix from RE-009, including the primary/fallback routing split and the remaining Webb-site-only capabilities.
- Friend API evidence as preserved in `REFERENCE_EVIDENCE.md`, including the reported top-level `source` and `data_as_of` fields and the `/api/stock` OpenAPI response-schema note.

Evidence still unavailable:

- The workspace snapshot does not contain accessible files under `docs_reference_evidence/01_Reference_Website/`.
- The workspace snapshot does not contain accessible files under `docs_reference_evidence/03_Public_Technical_Reference/`.
- The named PDF files were not available in this workspace for direct rendering in this review.

Unconfirmed areas:

- Exact SDW-to-local-DB ingestion mechanism on the friend side.
- Exact persistent database technology on the friend side.
- Exact implementation of remaining Webb-site fallback paths.
- Exact DT Rainbow data-generation architecture.
- Whether every historical design statement remains identical in current production.
- Any friend-side API detail beyond what is recorded in `REFERENCE_EVIDENCE.md`.

## 2. Friend Website Observed Features

| Feature | Evidence | Classification |
|---|---|---|
| Stock input, normalization, and issue-ID query flow | Source: Reference Evidence (RE-009) and preserved friend-site evidence; the friend site supports stock-oriented lookup and a fetch-oriented query flow. | A - Existing Joe V1 |
| Source selector and fetch workflow | Source: Existing Spec and Existing Implementation; Joe already exposes source mode and a fetch workflow. Friend evidence is directionally consistent. | A - Existing Joe V1 |
| Progress and loading feedback | Source: Existing Implementation (`app/streamlit_ui.py`, `streamlit_app.py`); Joe already renders staged progress states during fetch and report build. | A - Existing Joe V1 |
| AI Analysis Ready Summary | Source: Existing Spec and Existing Implementation (`ccass_core/report.py`). | A - Existing Joe V1 |
| Fetch Summary | Source: Existing Spec and Existing Implementation (`ccass_core/report.py`, `app/models.py`). | A - Existing Joe V1 |
| Metadata section | Source: Existing Spec and Existing Implementation (`app/models.py`, `ccass_core/report.py`). | A - Existing Joe V1 |
| Holdings Summary | Source: Existing Spec and Existing Implementation (`app/models.py`, `ccass_core/report.py`). | A - Existing Joe V1 |
| Holdings section | Source: Existing Spec and Existing Implementation (`app/models.py`, `ccass_core/report.py`). | A - Existing Joe V1 |
| Changes section | Source: Existing Spec and Existing Implementation (`app/models.py`, `ccass_core/report.py`, `app/services/changes.py`). | A - Existing Joe V1 |
| Big Changes section | Source: Existing Spec and Existing Implementation (`app/models.py`, `ccass_core/report.py`, `app/services/big_changes.py`). | A - Existing Joe V1 |
| Concentration section | Source: Existing Spec and Existing Implementation (`app/models.py`, `ccass_core/report.py`, `app/services/concentration.py`). | A - Existing Joe V1 |
| Price History section | Source: Reference Evidence and Existing Spec; the friend evidence shows a price-history surface, while Joe V1 currently reports price history as unavailable. | C - ND-01 Candidate |
| Announcements section | Source: Reference Evidence and Existing Spec; the friend evidence shows a visible announcements surface, while Joe V1 only has an announcement UI shell without a real source-backed data path. | C - ND-01 Candidate |
| Raw Preview surface | Source: Reference Evidence and Existing Implementation; Joe has raw previews, but only for summary and holdings previews, not the broader friend-style inspection surface. | C - ND-01 Candidate |
| Copy for ChatGPT | Source: Existing Spec and Existing Implementation (`ccass_core/report.py`, `app/streamlit_ui.py`). | A - Existing Joe V1 |
| Download functions | Source: Existing Spec and Existing Implementation (`app/streamlit_ui.py`); Joe already supports combined CSV, workbook, Markdown, and two raw-preview CSVs. | A - Existing Joe V1 |
| Price chart presentation | Source: Reference Evidence; Joe V1 has no price-chart engine or rendered price-history chart. | C - ND-01 Candidate |
| Concentration chart presentation | Source: Reference Evidence; Joe V1 has concentration text/report output but no dedicated concentration chart engine. | C - ND-01 Candidate |
| DT Rainbow presentation | Source: Reference Evidence; Joe V1 has chart-help text and historical concentration output, but no DT Rainbow engine. | C - ND-01 Candidate |
| Historical views | Source: Reference Evidence and Existing Implementation; Joe has limited history comparison and concentration-history text output, but not the friend-style historical visualization surface. | C - ND-01 Candidate |
| Explicit provenance metadata (`source`, `data_as_of`) | Source: Reference Evidence; Joe already has source metadata and date fields, but not a unified explicit `data_as_of` contract at the top level. | C - ND-01 Candidate |
| Warnings and unavailable-data handling | Source: Existing Spec and Existing Implementation; Joe already surfaces `DATA NOT AVAILABLE`, warnings, and partial/error behavior. | A - Existing Joe V1 |
| Exact friend visual layout and screenshot choreography | Source: Reference Evidence; this is useful as UI/process inspiration, but it should not be promoted into a mandatory requirement. | B - Reference Only |
| Webb-site dependency and fallback behavior | Source: Reference Evidence and Existing Implementation; Joe still has Webb-site as the core holdings source, but not the friend-style ownership matrix. | C - ND-01 Candidate |
| HKEXnews, 同花順 F10, and SDW / local DB-first ownership matrix | Source: Reference Evidence; Joe V1 does not implement this source-ownership matrix. | C - ND-01 Candidate |

## 3. Joe Platform Current Status

| Feature | V1 Status | Evidence |
|---|---|---|
| Stock input, normalization, and issue-ID query | Implemented. | Source: Existing Spec and Existing Implementation (`README.md`, `app/streamlit_ui.py`, `app/api.py`). |
| Source selection / source mode | Implemented, but limited to `auto`, `webbsite`, and `google_drive_csv`. | Source: Existing Implementation (`app/sources/registry.py`, `README.md`). |
| Fetch workflow and progress feedback | Implemented. | Source: Existing Implementation (`app/streamlit_ui.py`, `streamlit_app.py`). |
| AI Analysis Ready Summary | Implemented. | Source: Existing Implementation (`ccass_core/report.py`). |
| Fetch Summary | Implemented. | Source: Existing Implementation (`ccass_core/report.py`, `app/models.py`). |
| Metadata | Implemented. | Source: Existing Implementation (`app/models.py`, `ccass_core/report.py`). |
| Holdings Summary | Implemented. | Source: Existing Implementation (`app/models.py`, `ccass_core/report.py`). |
| Holdings | Implemented. | Source: Existing Implementation (`app/models.py`, `ccass_core/report.py`). |
| Changes | Implemented. | Source: Existing Implementation (`app/models.py`, `app/services/changes.py`, `ccass_core/report.py`). |
| Big Changes | Implemented. | Source: Existing Implementation (`app/models.py`, `app/services/big_changes.py`, `ccass_core/report.py`). |
| Concentration | Implemented. | Source: Existing Implementation (`app/models.py`, `app/services/concentration.py`, `ccass_core/report.py`). |
| Price History | Specified, but not implemented. | Source: Existing Spec and Existing Implementation (`docs/PROJECT_SPEC.md`, `ccass_core/report.py` shows the section as unavailable). |
| Announcements | Specified, but only a UI shell exists; the data path is not implemented. | Source: Existing Spec and Existing Implementation (`docs/PROJECT_SPEC.md`, `ccass_core/report.py`, `app/streamlit_ui.py`, no source-backed announcements service). |
| Raw Preview | Partially implemented. | Source: Existing Implementation (`app/streamlit_ui.py` provides only summary and holdings preview tables). |
| Copy for ChatGPT | Implemented. | Source: Existing Implementation (`ccass_core/report.py`, `app/streamlit_ui.py`). |
| Download functions | Implemented, but limited. | Source: Existing Implementation (`app/streamlit_ui.py` builds combined CSV, workbook, Markdown, raw-preview summary CSV, and raw-preview holdings CSV). |
| Price chart | Not implemented. | Source: Existing Implementation and Existing Spec (`ccass_core/` has no price chart engine; `docs/PROJECT_SPEC.md` lists price history as a target capability). |
| Concentration chart | Not implemented. | Source: Existing Implementation and Existing Spec (`ccass_core/` has no concentration chart engine; `docs/PROJECT_SPEC.md` treats concentration as report/data output rather than a chart engine). |
| DT Rainbow | Not implemented. | Source: Existing Implementation and Existing Spec (`ccass_core/` has no rainbow engine; `docs/PROJECT_SPEC.md` requires it only as a future capability). |
| Historical views | Partial. | Source: Existing Implementation (`ccass_core/report.py` includes concentration history text output; no friend-style visual historical engine exists). |
| Provenance metadata `source` | Implemented. | Source: Existing Implementation (`app/models.py`, `app/sources/registry.py`). |
| Explicit `data_as_of` contract | Partial / not standardized. | Source: Existing Implementation (`holdings_date`, `issued_shares_as_of`, `snapshot_date`, and `fetched_at` exist, but no explicit top-level `data_as_of` field is standardized in the current V1 models). |
| Warnings and unavailable-data handling | Implemented. | Source: Existing Spec and Existing Implementation (`app/models.py`, `ccass_core/report.py`, `app/errors.py`). |
| External source diversification | Not implemented as a first-class matrix. | Source: Existing Implementation and Existing Spec (`app/sources/registry.py` only registers Webb-site and Google Drive CSV; `README.md` says SDW is manual verification only). |

## 4. Gap Analysis

| Gap | Impact | Classification |
|---|---|---|
| Friend uses an explicit provenance contract around `source` and `data_as_of`, while Joe V1 only has distributed date fields and source metadata. | Downstream consumers have to reconcile multiple date fields manually, which weakens cross-source consistency and reporting clarity. | C - ND-01 Candidate |
| Friend uses HKEXnews, 同花順 F10, and SDW / local DB-first ownership routing, while Joe V1 remains Webb-site-centric with a Google Drive CSV fallback. | This is a material data-source policy gap and likely requires separate approval because it affects source legality, routing, and trust boundaries. | C - ND-01 Candidate |
| Friend exposes price history, announcement surfaces, and chart-oriented historical views that Joe V1 does not currently implement. | Users lose visual parity and historical context, and the missing surfaces cannot be reconstructed from the current V1 report alone. | C - ND-01 Candidate |
| Friend-style raw previews and broader download coverage are richer than Joe V1’s current limited preview/export set. | Inspection and export fidelity are reduced, especially for users who want section-level validation or audit-friendly artifacts. | C - ND-01 Candidate |
| Exact friend visual layout and screenshot choreography are attractive references, but they are not requirements. | These details should stay as inspiration only so Joe Platform does not inherit incidental UI choices as mandatory product rules. | B - Reference Only |
| The named PDF files and `00_Source_Documents` were not available in this workspace. | Direct PDF re-validation could not be performed in this run, so some friend-side judgments remain evidence-register based rather than freshly re-rendered. | D - Unconfirmed |

## 5. ND-01 Candidate List

Only candidates, not approvals:

- explicit `data_as_of` provenance contract
- friend-style source ownership matrix for HKEXnews / 同花順 F10 / SDW / local DB-first routing
- HKEX announcements data path and surfaced table
- price history data path and surfaced history view
- concentration chart presentation
- DT Rainbow presentation
- richer historical visualization surfaces
- broader raw previews and export catalogue
- section-specific export parity beyond the current V1 subset

## 6. Unconfirmed Items

- The named PDF files were not present in this workspace, so the latest friend PDFs were not directly rendered here.
- `00_Source_Documents` was not present in this workspace.
- The exact mechanism by which the friend’s SDW data reaches local DB remains unconfirmed.
- The exact current persistent database technology on the friend side remains unconfirmed.
- The exact implementation of remaining Webb-site fallback paths on the friend side remains unconfirmed.
- The exact DT Rainbow data-generation architecture on the friend side remains unconfirmed.
- Whether every historical design statement remains identical in current production remains unconfirmed.
- Any friend-side API schema detail beyond what is recorded in `REFERENCE_EVIDENCE.md` remains unconfirmed.

## 7. Recommendation

Documentation recommendation only:

Preserve the friend evidence as Reference Evidence, keep the ND-01 candidates separate from mandatory Joe Platform requirements, and do not promote any of the listed gaps into `PROJECT_SPEC.md` until a separate approval step is completed.

If the missing PDFs or `00_Source_Documents` are later supplied, append only additive evidence notes and keep the original comparison intact.

## Governance Verification

- No code changed.
- No tests changed.
- No requirements promoted.
- Friend evidence remains Reference Evidence.
- ND-01 implementation not started.

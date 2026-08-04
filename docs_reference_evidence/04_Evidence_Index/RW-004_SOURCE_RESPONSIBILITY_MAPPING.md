# RW-004 Source Responsibility Mapping

## 1. Evidence Basis

This mapping uses only the evidence available in the workspace:

- `docs_reference_evidence/04_Evidence_Index/REFERENCE_EVIDENCE.md`
- `docs_reference_evidence/04_Evidence_Index/ND-01_REALITY_GAP_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/ND-02_FINAL_REVIEW.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_SPEC.md`
- `app/sources/registry.py`
- `app/services/ccass.py`
- `app/api.py`
- `app/mcp_server.py`
- `ccass_core/report.py`

The requested `RW-004_ARCHITECTURE_MAPPING_DECISION.md` was not present in the workspace, so any decision detail that depends on it remains Unconfirmed.

## 2. Source Mapping Table

| Source | Friend Role | Joe Status | Classification |
|---|---|---|---|
| CCASS holdings data (`get_ccass_stock_data`, `screen_stocks`, `search_participant_holdings`) | Friend evidence says SDW / local DB is primary, with Webb-site still used as fallback for some big changes, concentration, and some historical data. | Joe currently serves holdings through Webb-site mirror and Google Drive CSV sources, with persistent normalized snapshot storage for historical records and fallback warnings in the service layer. | Alignment Required |
| Historical CCASS snapshots | Friend evidence indicates a source-specific collector/data-access model with local persistent storage, but the exact friend storage path is not fully documented here. | Joe has a normalized historical snapshot repository and collector that persist CCASS snapshots locally. | Completed |
| Market price history (`get_webbsite_price_history`) | Friend evidence says Yahoo Finance is primary, with Webb-site / local cached price fallback. | Joe exposes price history as unavailable in the current report surface and does not show a dedicated price-history source in the active source registry. | Missing Capability |
| Company announcements (`get_hkex_announcements`) | Friend evidence says HKEXnews is primary and no Webb-site is required. | Joe only has an announcements UI shell / unavailable-state messaging; no source-backed announcements path is implemented in the active service registry. | Missing Capability |
| Stock events (`get_stock_events`) | Friend evidence says Webb-site only, with no non-Webb replacement currently identified. | Joe does not expose a dedicated stock-events source in the active source registry or public API surface. | Missing Capability |
| Stock officers (`get_stock_officers`) | Friend evidence says 同花順 F10 managers are primary, with Webb-site historical fallback. | Joe does not expose a dedicated officers source in the current source registry or public API surface. | Missing Capability |
| Stock capital (`get_stock_capital`) | Friend evidence says 同花順 F10 is the source, with no Webb-site required. | Joe does not expose a dedicated capital-information source in the current source registry or public API surface. | Missing Capability |
| Change comparison (`get_ccass_diff`) | Friend evidence says Webb-site only, with no non-Webb replacement currently identified. | Joe computes changes and big changes from stored snapshots and report analysis rather than exposing a dedicated friend-equivalent diff source. | Alignment Required |

## 3. Ownership Mapping

| Data Area | Friend Ownership / Provision | Joe Ownership / Provision |
|---|---|---|
| CCASS holdings data | Friend evidence assigns SDW / local DB first, with Webb-site remaining as fallback in some cases. | Joe currently relies on Webb-site mirror and Google Drive CSV sources, with shared service and fallback behavior plus local snapshot persistence. |
| Historical data | Friend evidence indicates historical data is supported by the broader source / local DB architecture, but the exact storage mechanism is not separately documented here. | Joe owns historical CCASS snapshots through the normalized snapshot repository and collector, preserving local historical records. |
| Market price data | Friend evidence assigns Yahoo Finance primary ownership with Webb-site / local cached fallback. | Joe does not currently own a source-backed price-history capability. |
| Company information | Friend evidence assigns 同花順 F10 for stock capital and officers, with Webb-site fallback for officers history. | Joe does not currently own a dedicated company-information source path beyond the existing CCASS/report metadata. |
| Event / news information | Friend evidence assigns HKEXnews for announcements and Webb-site-only for stock events. | Joe exposes announcement-related UI / report surfaces, but not a source-backed event/news ownership path. |

## 4. Fallback Mapping

| Area | Friend Fallback Responsibility | Joe Fallback Responsibility |
|---|---|---|
| CCASS holdings data | Webb-site remains fallback where SDW / local DB is primary. | Google Drive CSV is used as configured fallback when the Webb-site mirror path fails or is unavailable. |
| Historical CCASS data | Friend evidence says some historical CCASS data may still use Webb-site fallback. | Joe keeps historical CCASS snapshots locally and can fall back to stored latest-known-good / snapshot behavior through the service layer. |
| Market price history | Webb-site / local cached price fallback after Yahoo Finance. | No dedicated price-history source fallback is implemented. |
| Announcements | No Webb-site required in the friend evidence. | No source-backed fallback path is implemented. |
| Stock events | Webb-site only; no non-Webb replacement identified. | No dedicated source-backed fallback path is implemented. |
| Stock officers | Webb-site historical fallback after 同花順 F10 managers primary. | No dedicated source-backed fallback path is implemented. |
| Stock capital | No Webb-site required in the friend evidence. | No dedicated source-backed fallback path is implemented. |
| Change comparison | Webb-site only, no non-Webb replacement identified. | Joe performs change / big-change analysis from stored CCASS snapshots rather than a dedicated external diff source. |

## 5. Gap Analysis

- The strongest confirmed gap is source breadth. Friend evidence documents a multi-source ownership matrix, while Joe currently implements only a narrower active source set.
- Joe satisfies the general CCASS historical storage need for its own platform through normalized local snapshots, but this does not recreate the friend-side ownership matrix.
- Price history, announcements, officers, capital, and stock-event ownership are missing as dedicated source capabilities in Joe.
- Change comparison is partly aligned in intent, but Joe derives it from its own stored snapshots rather than exposing a friend-style dedicated diff source.
- The current Joe fallback story is internally coherent, but it is not the same as the documented friend responsibility split.

## 6. Recommendation

- Alignment Required for CCASS holdings responsibility, because Joe’s active sources do not match the friend’s documented ownership split.
- Completed for Joe’s own historical snapshot storage, because the platform already persists historical CCASS records locally.
- Missing Capability for price history, announcements, events, officers, and capital ownership, because Joe does not currently expose dedicated source-backed paths for them.
- Alignment Required for change comparison, because Joe covers the user-visible outcome but not the same documented source responsibility.

## 7. Unconfirmed Items

- The exact content of `RW-004_ARCHITECTURE_MAPPING_DECISION.md`.
- The exact friend storage mechanism behind SDW / local DB.
- The exact friend-side implementation of any remaining Webb-site fallback paths.
- Whether the friend architecture includes additional source responsibilities beyond those listed in `REFERENCE_EVIDENCE.md`.
- Whether any friend-side source currently has a different consumer-facing ownership label than the one preserved in the evidence matrix.

## Governance Verification

Confirmed:

- No code changed
- No tests changed
- No data source added
- No source routing changed
- Friend evidence remains reference only


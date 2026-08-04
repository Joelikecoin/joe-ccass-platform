# RW-005 Price History Requirement Decision

## 1. Objective

Determine whether Price History should be required to replicate the Friend Reference Website experience, what capability boundary is justified by evidence, and what remains unknown.

This document is a requirement evaluation only. It is not implementation approval.

## 2. Evidence Basis

This decision uses the evidence available in the workspace:

- `docs_reference_evidence/04_Evidence_Index/REFERENCE_EVIDENCE.md`
- `docs_reference_evidence/04_Evidence_Index/ND-01_REALITY_GAP_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/ND-02_FINAL_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/RW-004_SOURCE_RESPONSIBILITY_MAPPING.md`
- `docs/PROJECT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `ccass_core/report.py`
- `app/sources/registry.py`
- `app/services/ccass.py`

The requested `RW-004-A_DATA_CAPABILITY_PRIORITY_DECISION.md` was not present in the workspace, so any dependency on it remains Unconfirmed.

## 3. Requirement Evaluation

### User Value

- Is Price History part of the Friend report experience? Yes. The preserved friend evidence includes `get_webbsite_price_history` with Yahoo Finance as the primary source and a Webb-site / local cached fallback.
- Does it support the CCASS analysis workflow? Yes. The preserved project specification and chart guidance tie price movement to holdings and announcement context for cross-checking.
- Is it required for visual replication? Yes, at least as a visible historical price surface. The evidence supports the requirement for a price-history section, even though the exact visual form is not fully preserved.

### Required Capability Boundary

Required by current evidence:

- Historical price display
- Price date / date context
- Source metadata for the price data
- Adjusted / unadjusted status
- OHLCV fields where available
- Volume and turnover where available
- Missing-date warning
- Ability to compare price context with CCASS changes or related report context

Not required unless later evidence supports it:

- Technical indicators
- Trading signals
- Forecasting
- Automated trading
- Investment advice

Chart requirement:

- A dedicated price chart is not clearly established as a hard requirement in the preserved friend evidence.
- The evidence supports a price-history capability, but the exact display form remains Unconfirmed.

## 4. Data Source Evaluation

| Source | Evidence | Suitability | Status |
|---|---|---|---|
| Yahoo Finance | Friend matrix evidence lists `get_webbsite_price_history` with Yahoo Finance as primary. | Suitable as the evidence-backed primary source. | Supported |
| Webb-site / local cached price fallback | Friend matrix evidence lists Webb-site / local cached price as fallback for price history. | Suitable as fallback only, based on preserved evidence. | Supported |

No other price-history source is supported by the current friend evidence in this workspace.

## 5. Architecture Impact

### Data model

- Would require a first-class price-history model or table in the normalized historical layer.
- The current Joe architecture already documents a `price_history` concept, but the runtime implementation still reports price history as unavailable.

### Storage

- Would require persistent storage of dated price rows and metadata.
- The architecture already anticipates historical storage, but Joe does not yet expose a live price-history capability in the current result path.

### API

- Would likely require a structured price-history API surface or inclusion in the existing report API payloads.
- No dedicated price-history endpoint is currently exposed in the active Joe API surface.

### Report

- Would add a visible Price History section to the report experience.
- Joe currently renders that section as unavailable, so this would replace a placeholder with a real output.

### UI

- Would add a visible price-history display in the report / detail experience.
- If a chart is later justified by evidence, it should be treated as a separate UI decision rather than assumed here.

## 6. Decision

Approved for Implementation

Reason:

- The preserved friend evidence shows Price History as part of the reference experience.
- The preserved Joe evidence shows the feature is currently missing or unavailable.
- The requirement boundary is sufficiently supported to justify making Price History part of the replication scope.

Important note:

- This is a requirement decision only, not approval to start coding.
- The exact display form and exact source integration details remain partially Unconfirmed.

## 7. Governance

Confirmed:

- No code changed
- No tests changed
- No data source added
- No implementation started
- Friend evidence remains reference only

## 8. Unconfirmed Items

- The exact contents of `RW-004-A_DATA_CAPABILITY_PRIORITY_DECISION.md`
- Whether the friend reference uses a table-only price-history surface or includes a dedicated chart
- The exact date-range interaction, if any, on the friend side
- The exact fallback behavior beyond the primary/fallback source labels preserved in the matrix
- Whether price history is shown alongside CCASS changes in a single combined panel or as a separate surface


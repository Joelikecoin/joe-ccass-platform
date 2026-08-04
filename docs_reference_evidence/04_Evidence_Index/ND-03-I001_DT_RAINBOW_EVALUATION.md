# ND-03-I001 DT Rainbow Capability Evaluation

## 1. Executive Summary

DT Rainbow-style visualization is feasible as a future user-facing visualization capability, but it is not ready for immediate implementation as a fully defined analytical feature.

What is currently available in Joe Platform is the supporting surface area: historical snapshots, participant-level holdings, concentration summaries, source metadata, and a user-triggered optional loading pattern. What is still missing is an approved DT Rainbow data contract and any validated calculation logic for the visualization itself.

Conclusion:

- The visualization framework is partially supported.
- The calculation and data-contract side is not sufficiently defined.
- DT Rainbow should remain deferred until the required data model and algorithm scope are explicitly approved.

## 2. Evidence Basis

This evaluation is grounded in:

- `ND-03_IMPLEMENTATION_PLAN.md`
- `ND-02_FINAL_REVIEW.md`
- `ND-01_FINAL_REVIEW.md`
- `REFERENCE_EVIDENCE.md`
- current repository evidence in the model, report, history, and Streamlit surfaces

Reference evidence indicates that DT Rainbow is an optional, user-triggered view and that heavy visual components should not block the initial report experience. The friend/reference-system implementation remains reference-only; its internal calculation logic is not available and must not be assumed.

The repository evidence confirms:

- `data_as_of` is present on source and changes metadata
- historical snapshots are normalized and persisted
- concentration and participant rankings are already available
- the current Streamlit UI supports optional loading and progressive disclosure
- DT Rainbow in Joe Platform is currently only an interaction frame, not a calculation engine

## 3. Data Requirement Analysis

DT Rainbow-style visualization would require the following categories of data:

### Required fields

Confirmed from evidence:

- participant identity
- participant rank
- participant share count
- participant percentage of issued shares
- participant percentage of CCASS shares
- holdings date / snapshot date
- source metadata
- `data_as_of`
- concentration totals and top-holder percentages

Unconfirmed assumptions:

- exact participant ordering rules used by the reference DT Rainbow
- whether the visualization needs additional per-participant attributes beyond the current holdings rows
- whether color mapping or participant grouping must persist across dates

### Historical requirements

Confirmed from evidence:

- historical snapshots exist
- snapshot identity is stable
- historical date-range queries are supported
- multiple dated snapshots can be compared

Unconfirmed assumptions:

- exact historical depth required for a useful DT Rainbow experience
- whether the visualization needs a continuous daily series or only selected snapshots
- whether gaps in history should be interpolated, skipped, or explicitly shown

### Participant / holder data requirements

Confirmed from evidence:

- participant-level holdings are available in the current report model
- rankings and percentages are present
- concentration totals are already derived from holdings

Unconfirmed assumptions:

- whether the visualization depends on full participant identity reconciliation across dates
- whether participant renaming or merging rules are needed
- whether special handling is needed for partial snapshots or source-fallback snapshots

### Ownership concentration requirements

Confirmed from evidence:

- top 5 and top 10 concentration are already exposed
- CCASS-issued and CCASS-total ratios are already available
- concentration history is already present in report output

Unconfirmed assumptions:

- whether DT Rainbow requires more granular concentration breakdowns than the current summary
- whether historical concentration must be computed from raw participant rows or from stored aggregates

### Update frequency requirements

Confirmed from evidence:

- the platform already supports per-snapshot reporting and historical storage
- the report contract treats `data_as_of` as the main semantic date marker

Unconfirmed assumptions:

- whether DT Rainbow must update on every fetch, on-demand, or from cached snapshots
- whether near-real-time updates are required
- whether user-triggered loading alone is sufficient for the expected refresh cadence

## 4. Joe Platform Capability Mapping

| Capability | Status | Notes |
| --- | --- | --- |
| Participant-level holdings rows | Available | Current response models expose rank, participant, shares, last change, issued-share percentage, CCASS percentage, and participant category. |
| Source metadata and `data_as_of` | Available | Metadata and report/API output already standardize source provenance and `data_as_of`. |
| Historical snapshot storage | Available | Normalized historical snapshots and stable identity exist in the repository layer. |
| Historical cross-period comparison | Partially Available | Comparisons exist through previous snapshot and history support, but DT Rainbow-specific comparison behavior is not defined. |
| Concentration summary capability | Available | Top 5 / top 10 concentration values are already available in report and model surfaces. |
| Concentration history support | Available | Historical concentration sections are already part of the current report surface. |
| Optional user-triggered loading pattern | Available | The Streamlit UI already supports progressive disclosure and manual activation for optional heavy views. |
| DT Rainbow interaction frame | Available | The current UI exposes an optional DT Rainbow control surface. |
| DT Rainbow calculation logic | Missing | No approved implementation or validated algorithm exists in Joe Platform. |
| DT Rainbow reference algorithm details | Unknown | Friend/reference evidence explicitly does not provide the internal calculation logic. |
| Exact refresh/update cadence for DT Rainbow | Unknown | Evidence does not confirm whether the visual should be snapshot-based, cache-based, or on-demand only. |

## 5. Architecture Impact

### Storage impact

Likely moderate to high if a full DT Rainbow capability is implemented.

Reasoning:

- the visualization likely needs multiple dated snapshots or a time series of participant-level holdings
- caching or materialized derived data may be needed to keep generation responsive
- storing additional derived outputs could increase persistence and maintenance cost

Current status:

- the existing historical snapshot foundation can support the data, but the exact storage shape for DT Rainbow is not yet defined

### API impact

Likely low to moderate for the current interaction framework, but potentially higher for a full capability.

Reasoning:

- a simple on-demand visualization trigger can be added without changing public data contracts much
- a full DT Rainbow implementation may require structured payloads for historical series, derived states, or loading status
- preserving the current `data_as_of` and provenance contract is important

Current status:

- no API changes are required for the evaluation phase
- any future API work should stay read-only and aligned with existing report/API semantics

### UI impact

Moderate.

Reasoning:

- the current UI already supports progressive disclosure
- DT Rainbow would need clear user-triggered loading, status, and failure messaging
- if full capability is implemented, the UI must avoid blocking the initial report rendering

Current status:

- the UI pattern is already in place for an optional view
- the main remaining UI work would be visualization presentation and detailed loading states

### Performance impact

Potentially high.

Reasoning:

- DT Rainbow is likely to be more expensive than summary rendering because it depends on historical participant-level data
- rendering large time-series or stacked visualizations can increase compute and client load
- lazy loading and caching would probably be required

Current status:

- the platform already has the right pattern for deferring heavy work
- performance characteristics of a full DT Rainbow computation remain unmeasured and unknown

## 6. Feasibility Assessment

Recommended approach:

1. Keep DT Rainbow as a deferred capability until the data contract is approved.
2. Define the required historical input series, participant identity rules, and update cadence first.
3. Reuse the existing optional loading pattern so the core report remains fast.
4. Only then evaluate whether a cached or generated-on-demand visualization is practical.

Major dependencies:

- stable historical snapshot series
- participant identity continuity across dates
- approved DT Rainbow data contract
- a decision on whether output should be generated on demand, cached, or precomputed
- a validated explanation of what the visualization is intended to show

Risks:

- algorithm ambiguity could cause scope drift
- performance cost could be higher than the user value justifies
- source fallback or partial snapshots could distort the visual if not handled explicitly
- implementing an unapproved “friend-like” algorithm would violate the reference-only boundary

Estimated complexity level:

- High for full implementation
- Low to moderate for the existing interaction shell only

## 7. Recommendation

Recommended future direction: Deferred

Reasoning:

- The current platform already supports the presentation pattern needed for an optional heavy visualization.
- The missing piece is not the UI shell; it is the approved calculation and data contract.
- Friend/reference evidence is reference only and does not provide enough algorithm detail to justify immediate implementation.
- The feature is plausible and potentially valuable, but it should wait until the required inputs, meaning, and performance envelope are defined.

## 8. Unconfirmed Items

- exact DT Rainbow calculation logic
- exact participant grouping and color continuity rules
- exact historical depth required
- exact snapshot cadence required
- whether derived data should be cached or regenerated on demand
- whether the visualization expects only holdings data or also external market context
- whether the reference implementation relies on hidden normalization or enrichment steps

## 9. Open Questions

1. What is the exact user question DT Rainbow is meant to answer in Joe Platform?
2. How many historical snapshots are needed before the visualization becomes meaningful?
3. Should the visualization be generated purely from CCASS holdings, or does it require additional data context?
4. Do participant identities need to remain visually stable across time, and if so, what is the merge/rename rule?
5. Is the acceptable UX to generate on demand only, or should cached precomputation be introduced later?

## Governance Verification

- No code changed
- No tests changed
- No DT Rainbow implementation started
- No new data source added
- Friend evidence remains Reference Only


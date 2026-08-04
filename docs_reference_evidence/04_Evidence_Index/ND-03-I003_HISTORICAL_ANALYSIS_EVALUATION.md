# ND-03-I003 Advanced Historical Analysis Evaluation

## 1. Executive Summary

Advanced historical analysis is partially feasible in Joe Platform today.

The repository already provides the core foundation for snapshot-based historical work: normalized historical storage, stable snapshot identity, date-range retrieval, exact two-snapshot change comparison, concentration history, and provenance-aware metadata. That is enough to support meaningful before/after analysis on approved historical snapshots.

What is not yet available is the broader research layer implied by more advanced historical work, such as event-timeline storage, transaction-level analysis, longer-retention guarantees, and richer market-context integration. For that reason, the feature set is feasible in principle but should remain deferred until scope and data requirements are explicitly separated.

## 2. Current Capability Assessment

| Capability | Status | Notes |
| --- | --- | --- |
| Historical snapshots | Available | Normalized snapshot storage exists with stable identity and persisted provenance. |
| Snapshot dates | Available | Snapshots are keyed by `snapshot_date`, and the repository supports exact date lookups and ranges. |
| Holdings history | Available | The repository stores repeated holdings snapshots and can return historical ranges for a stock. |
| Participant changes | Available | Exact two-snapshot change comparison is already implemented, including big-change filtering and structured diagnostics. |
| Concentration history | Available | Historical concentration tables are already produced from stored snapshots and rendered in the report surface. |
| Metadata provenance | Available | Source metadata, `data_as_of`, fetched-at timing, source identity, and raw provenance are already preserved. |

## 3. Future Analysis Requirements

The following analysis needs are plausible future directions, but they are not fully satisfied by the current repository alone.

Confirmed capability:

- before/after snapshot comparison
- exact two-snapshot ownership change analysis
- concentration trend inspection from stored snapshots
- provenance-aware analysis using source metadata and `data_as_of`

Future requirement:

- before/after event comparison across a meaningful event window
- large transaction historical study
- CCASS ownership change pattern analysis across multiple dates
- participant movement analysis over time
- historical concentration change studies beyond the current report surface

Interpretation:

- Snapshot-based research is already supported.
- Event-based or transaction-based research is not yet supported as a distinct historical analysis layer.
- Broader historical studies likely need additional structure around event timing, historical depth, and cross-period grouping.

## 4. Data Gap Analysis

Missing or not yet confirmed requirements:

- longer retention period
- additional market data
- transaction-level data
- price history integration
- event timeline storage

Notes:

- Longer retention is important if advanced research needs to span multiple cycles or older reference points.
- Transaction-level data is not present in the current CCASS snapshot model, so large-transaction historical studies cannot be built from the existing data alone.
- Price history is not currently part of the historical analysis surface in a way that would support deep cross-market study.
- Event timeline storage would be needed to anchor analysis around releases, announcements, or other dated catalysts.
- No new data source should be added as part of this evaluation; the gap analysis is limited to what is missing from the current architecture.

## 5. Architecture Impact

### SQLite / history storage

Moderate impact.

The current SQLite history layer already supports snapshot persistence, range queries, and history bounds. Advanced historical analysis would likely require:

- longer retention or explicit retention policy support
- more efficient indexes for long-range reads
- possible event tables or derived history tables
- clearer separation between raw snapshots and analytical summaries

### Data models

Moderate impact.

Current models are strong for snapshot and comparison use, but advanced historical analysis may need:

- event or timeline entities
- historical series models
- participant continuity / identity resolution fields
- richer derived summary objects for multi-period analysis

### APIs

Moderate impact.

The existing API contract supports report-style and comparison-style outputs, but broader historical analysis may need:

- date-window query parameters
- timeline or series endpoints
- structured historical summary responses
- pagination or range controls for long histories

### Reports

Moderate impact.

The current report surface already shows changes and concentration history. More advanced historical analysis would likely add:

- multi-period comparison sections
- longer trend summaries
- event-anchored historical views
- optional historical drill-downs without changing the current V1 experience

### Future AI consumers

Low to moderate impact.

The existing provenance contract is already a good base for structured consumers. If advanced historical analysis is later exposed to AI or MCP consumers, it should remain read-only and grounded in:

- source
- `data_as_of`
- snapshot identity
- explicit warnings / completeness flags

## 6. Feasibility Assessment

Advanced historical analysis is feasible in a limited, snapshot-based form, but not yet fully defined for broader research use.

Recommended approach:

- Treat the current snapshot repository as the baseline.
- Expand only after the analysis question is explicit.
- Separate snapshot-based research from event-based or transaction-based research.
- Preserve the current data contract and avoid inventing missing history.

Major dependencies:

- adequate historical retention
- clear participant identity continuity rules
- a defined event/timeline model if event-driven analysis is desired
- any required price or market context, if cross-market analysis is in scope

Risks:

- scope can expand from “historical analysis” into full research-platform work
- missing transaction-level data can lead to false expectations about what can be analyzed
- participant renaming or identity drift can distort longitudinal analysis
- over-reliance on derived summaries can hide the fact that only snapshot data is available

Estimated complexity level:

- Moderate for snapshot-based historical enhancements
- High for event-driven or transaction-level historical research

## 7. Recommendation

Deferred

Reasons:

- The platform already supports meaningful snapshot-based historical comparison, so the foundation is good.
- The broader advanced historical analysis vision is still underspecified and would need additional data requirements before implementation.
- Some of the examples in scope, especially transaction-level study and event-timeline analysis, are not supported by the current repository alone.
- The safest next step is to keep the current foundation and define the exact historical research questions before adding new structures.

## 8. Unconfirmed Items

- exact retention horizon required for advanced historical analysis
- whether participant identity continuity needs merge/rename rules
- whether event timelines should be first-class data or derived from existing records
- whether price history is required for all advanced historical analyses or only some
- whether transaction-level historical study is expected to be possible from Joe Platform data alone
- whether long-range analysis should be computed on demand or precomputed

## 9. Open Questions

1. What is the minimum historical depth required for a useful advanced analysis experience?
2. Which analyses must be snapshot-only, and which require event anchors?
3. Do we need a participant identity resolution layer across time?
4. Should price or market context be part of the historical analysis scope, or stay separate?
5. Is the expected output a report surface, an API surface, an AI/MCP surface, or all three?
6. What retention policy is acceptable for historical snapshots and derived analysis results?

## Governance Verification

- No code changed
- No tests changed
- No new data source added
- No analysis engine implemented
- No investment logic added
- Reference Evidence remains Reference Only


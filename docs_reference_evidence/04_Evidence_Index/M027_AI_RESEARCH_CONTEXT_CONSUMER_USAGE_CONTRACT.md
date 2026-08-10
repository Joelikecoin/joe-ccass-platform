# M027-01 AI Research Context Consumer Usage Contract

## 1. Objective

Define how downstream consumers should use the approved AI Research Context consumer surface without reintroducing domain processing logic into the consumer layer.

This contract is consumer guidance only. It does not change the AI Research Context model shape, the API contract, the MCP contract, schema, storage, or source strategy.

The goal is to keep consumer access clear and stable:

- one approved consumer entry point,
- a small set of allowed consumer dependencies,
- explicit prohibition against direct domain-layer access from consumers.

## 2. Approved Consumer Entry Point

The approved consumer entry point is `AIResearchContextConsumerEntry`.

Consumers should enter through the consumer entry and then read the approved consumer-facing surfaces exposed by the entry:

- `AIResearchContextConsumerBoundary`
- `AIResearchContextConsumerEntryContext`
- `AIResearchContextDelivery`
- `AIResearchContextQualitySummary`

`AIResearchContextConsumerBoundary` is the preferred consumer-facing boundary because it presents the approved consumer-facing objects together as a stable surface.

## 3. Allowed Consumer Dependencies

Downstream consumers may depend on the following objects:

| Allowed dependency | Purpose |
|---|---|
| `AIResearchContextConsumerEntry` | Approved entry point for consumer access. |
| `AIResearchContextConsumerBoundary` | Approved consumer-facing bundle of current / historical / quality context. |
| `AIResearchContextConsumerEntryContext` | Stable consumer-readable wrapper for current and historical context. |
| `AIResearchContextDelivery` | Consumer-facing current context surface. |
| `AIResearchContextHistoricalDelivery` | Consumer-facing historical context surface. |
| `AIResearchContextQualitySummary` | Consumer-facing freshness / provenance / warning summary. |

Consumers may also use the summary / markdown helpers that render these approved surfaces, as long as they do not rebuild the underlying processing chain.

## 4. Prohibited Direct Domain Access

Consumers must not bypass the approved boundary by reading or reconstructing domain processing layers directly.

Prohibited direct dependencies include:

- `comparison`
- `change_summary`
- `timeline`
- `timeline_summary`
- `historical_query`
- `historical_comparison_query`
- `historical_summary`
- any direct reconstruction of historical/current processing logic
- any direct domain processing logic that belongs in original layers

If a consumer needs one of these structural objects, it should read the approved consumer boundary or the approved consumer entry rather than composing the domain layers itself.

## 5. Dependency Protection Rules

Consumer code should follow these rules:

1. Use `AIResearchContextConsumerEntry` as the consumer entry point.
2. Read `AIResearchContextConsumerBoundary` for the approved consumer-facing bundle.
3. Use `AIResearchContextDelivery` only as a consumer-facing current context surface.
4. Use `AIResearchContextHistoricalDelivery` only as a consumer-facing historical context surface.
5. Use `AIResearchContextQualitySummary` to interpret freshness, provenance, warnings, and limitation status.
6. Do not recreate comparison, timeline, historical query, or historical summary logic in consumer code.

This keeps domain processing in the original layers and prevents consumer code from becoming a second processing pipeline.

## 6. Consumer Access Guidance

Recommended read order:

1. `AIResearchContextConsumerEntry` to confirm the approved entry point.
2. `AIResearchContextConsumerBoundary` to inspect the consumer-facing bundle.
3. `AIResearchContextDelivery` to inspect current context.
4. `AIResearchContextHistoricalDelivery` to inspect historical context.
5. `AIResearchContextQualitySummary` to inspect freshness, provenance, warnings, and limitations.

Consumers should treat these surfaces as read-only contract surfaces. They are for access and interpretation, not for rebuilding processing logic.

## 7. Boundary Preservation

The consumer boundary must remain additive and narrow:

- it may compose existing consumer-facing objects,
- it may expose approved visibility and reference metadata,
- it may summarize availability and quality,
- it must not recreate domain processing logic,
- it must not widen the contract into analysis or inference.

The boundary is a consumer access surface, not a calculation engine.

## 8. Out of Scope

This contract does not:

- add new fields,
- change the consumer entry contract,
- change the consumer boundary contract,
- change the AI Read Model v0.1,
- change API or MCP contracts,
- change schema or storage,
- add new data sources,
- add analysis logic,
- add investment logic,
- add trading signals,
- add recommendation logic.

In short: no new source, no analysis logic, and no direct domain-layer reconstruction from consumer code.


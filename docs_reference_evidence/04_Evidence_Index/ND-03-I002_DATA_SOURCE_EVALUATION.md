# ND-03-I002 Advanced Data Source Capability Evaluation

## 1. Executive Summary

Additional data source capabilities are feasible in Joe Platform, but the current repository only supports a narrow source set today.

What is already in place is a good foundation: a capability-based source registry, explicit fallback selection, provenance metadata, normalized historical storage, and structured data-quality handling. That means new source work can be added in a controlled way later without redesigning the whole platform.

What is not yet in place is a broader approved source estate. The current platform is primarily centered on Webb-site mirror holdings plus a configured Google Drive CSV fallback/import path. Reference evidence suggests other public or semi-public sources could be valuable, but they remain reference-only until a source decision is made.

Overall recommendation:

- Yahoo / public market data sources: recommended for future implementation
- HKEX official sources: recommended for future implementation
- 同花順 F10: deferred
- other public sources: reference only unless separately evidenced and approved

## 2. Current Source Capability

| Source | Status | Notes |
| --- | --- | --- |
| Webb-site mirror holdings source | Available | This is the primary holdings source in the current registry. It supports latest holdings retrieval, persistent last-known-good handling, and provenance metadata. |
| Google Drive CSV import source | Available | This is a configured fallback/import source with requested-date, historical, and manual-import capabilities. It is useful for operational coverage, but it does not increase source authority. |
| Source abstraction / registry | Available | The registry already models source priority, audit state, fallback eligibility, supported capabilities, and provenance. |
| Fallback capability | Partially Available | Fallback selection exists for holdings retrieval, but it is not a universal multi-source routing fabric for every product surface. |
| Provenance metadata | Available | Source identity, parser/schema version, audit state, `source`, and `data_as_of` are already part of the platform contract. |
| Data quality handling | Available | Structured warnings, source failure classification, and fallback visibility are already present in the existing product and UI surfaces. |

## 3. Additional Source Evaluation

| Source | Potential Use | Assessment |
| --- | --- | --- |
| HKEX official sources | Official announcements, event verification, corporate-action context, and read-only market/event corroboration. | Recommended for Future Implementation. HKEX is authoritative and useful for event context, but no approved collector is present today and the integration path still needs explicit design and validation. |
| 同花順 F10 | Company capital structure, officers/management context, capital data, and auxiliary company profile enrichment. | Deferred. The potential value is real, but ownership/licensing, stability, and long-term maintenance cost are not sufficiently confirmed in the current evidence. |
| Yahoo / public market data sources | Price history, market context, cross-checking holdings against market movement, and lightweight historical context. | Recommended for Future Implementation. Public market data is a strong fit for the current report gaps, especially price history, and it is lower risk than proprietary or opaque sources if data quality checks are in place. |
| Other public sources supported only by existing evidence | Reference discovery, future investigation, or secondary corroboration only. | Reference Only. The current evidence set is too thin to promote these sources beyond reference status without a separate approval path. |

## 4. Risk Assessment

### HKEX official sources

- Data ownership: official public-source ownership.
- Availability: generally strong, but access method may be gated by web behavior, permissions, or anti-bot protection.
- Stability: medium; public pages can change structure.
- Maintenance cost: moderate to high.
- Dependency risk: moderate; source is authoritative, but operational access can still shift.

### 同花順 F10

- Data ownership: third-party commercial/public aggregator ownership, not Joe-owned.
- Availability: unclear from current evidence.
- Stability: medium to low; source format and access policies may change.
- Maintenance cost: high if the source requires ongoing parser upkeep.
- Dependency risk: high due to uncertainty around licensing, structure, and long-term access.

### Yahoo / public market data sources

- Data ownership: external public market-data ownership.
- Availability: generally good, but subject to provider limits and format changes.
- Stability: medium; public market pages and endpoints can change.
- Maintenance cost: moderate.
- Dependency risk: moderate; lower than proprietary sources, but quality and coverage must be validated.

### Other public sources

- Data ownership: unknown until each source is individually reviewed.
- Availability: unknown.
- Stability: unknown.
- Maintenance cost: unknown.
- Dependency risk: high until a specific source is approved and measured.

## 5. Architecture Impact

### Source registry

The current registry is already the right place to add new source definitions, capabilities, audit states, and fallback eligibility. New source work would mainly extend the registry rather than replace it.

### Collectors

Any additional source would require a dedicated collector or adapter. The implementation cost depends on whether the source is:

- snapshot-style holdings
- event-style announcements
- market data / price history
- company-profile / capital / officers data

The collector burden is likely highest for proprietary or unstable third-party sources.

### Metadata contract

The current provenance contract is strong enough to carry new sources without adding duplicate fields. Existing top-level concepts such as `source` and `data_as_of` should remain the baseline.

If a source needs extra metadata, it should be modeled as source-specific provenance rather than widening the core contract unnecessarily.

### Historical storage

The current SQLite/history layer is well aligned with holdings snapshots and exact-date comparison. Sources that provide snapshot holdings can usually fit into this model with limited change.

Sources that provide time series, events, or price history may require additional storage shapes or derived tables. In particular, price history is not the same thing as a holdings snapshot and should not be forced into the current snapshot table without a separate design decision.

### API output

The current API contract already supports structured report outputs and provenance-aware responses. New sources may require:

- new endpoints
- richer product-specific response models
- source-specific warnings or completeness flags

The safest path is to keep the current contract stable unless a source genuinely adds a new product dimension.

## 6. Recommendation

### HKEX official sources

Recommended for Future Implementation

Reason:

- authoritative public source
- strong fit for announcement and event-context use cases
- useful for corroboration without changing the current data-model philosophy
- integration cost is real, but the value is high enough to justify later implementation planning

### 同花順 F10

Deferred

Reason:

- potentially valuable for company capital/officer context
- evidence is not strong enough to justify immediate adoption
- ownership, licensing, and stability risks are higher than the public-source alternatives

### Yahoo / public market data sources

Recommended for Future Implementation

Reason:

- useful for price history and market-context enrichment
- aligns with current report gaps
- likely lower risk than proprietary alternatives
- can improve historical interpretation without changing the core holdings contract

### Other public sources

Reference Only

Reason:

- existing evidence is insufficient for source promotion
- source-specific evaluation would be required before any approval
- should remain a research reference until separately justified

## 7. Unconfirmed Items

- exact current production coverage for non-holdings sources in Joe Platform
- whether any official HKEX source connector is already approved outside the current repo
- whether Yahoo or F10 access terms are acceptable for the intended use
- exact maintenance burden for each prospective source
- exact data-quality behavior for any future price or event source
- whether other public sources beyond the listed references are intended or approved

## 8. Open Questions

1. Is the next priority a holdings enrichment source, an event/announcement source, or a price-history source?
2. Should new sources be added only when they improve a current gap in the user-facing report?
3. What minimum provenance fields must every new source provide before it can be approved?
4. Is the acceptable standard for a new source “public and stable,” or “public, stable, and independently validated”?
5. Should future source additions require a separate approval for storage and API changes, or only for the source itself?

## Governance Verification

- No code changed
- No tests changed
- No new data source added
- No collector implemented
- No source routing changed
- Friend evidence remains Reference Only


# ND-01 Scope Decision

This document is a scope classification artifact only.

Reference Evidence remains Reference Evidence and does not become a mandatory requirement or approved implementation.

## 1. Decision Summary

ND-01 should focus on the parts of the friend evidence that strengthen Joe Platform's reliable CCASS data foundation, structured provenance, and AI-ready outputs.

The strongest evaluation candidates are the items that improve source metadata consistency, source ownership clarity, announcements/price-history coverage, and export fidelity.

Broader visual parity, generalized historical presentation polish, and any feature with weak evidence or unclear platform value should remain deferred or out of scope.

## 2. Candidate Review Table

| Candidate | Evidence Source | Classification | Reason |
|---|---|---|---|
| Explicit `data_as_of` provenance contract | Reference Evidence; Existing Spec; Existing Implementation | Category A - Recommended for ND-01 Evaluation | Improves the reliability of structured metadata and aligns with Joe Platform's AI-ready data foundation. |
| Friend-style source ownership matrix for HKEXnews / 同花順 F10 / SDW / local DB-first routing | Reference Evidence (RE-009) | Category A - Recommended for ND-01 Evaluation | Valuable for source governance and fallback clarity, even though it carries dependency and policy risk that must be reviewed separately. |
| HKEX announcements data path and surfaced table | Reference Evidence; Existing Spec | Category A - Recommended for ND-01 Evaluation | Fits Joe Platform's stated CCASS research scope and supports structured, auditable event data. |
| Price history data path and surfaced history view | Reference Evidence; Existing Spec | Category A - Recommended for ND-01 Evaluation | Directly supports the platform's objective of reliable historical data and structured output. |
| DT Rainbow presentation | Reference Evidence; Existing Spec | Category A - Recommended for ND-01 Evaluation | It is a meaningful historical visualization surface and aligns with the existing V1 direction, but should still go through separate approval before implementation. |
| Broader raw previews and export catalogue | Reference Evidence; Existing Spec; Existing Implementation | Category A - Recommended for ND-01 Evaluation | Strengthens inspection, auditability, and downstream AI consumption without changing the core data model. |
| Concentration chart presentation | Reference Evidence; Existing Spec | Category B - Deferred | Helpful as presentation polish, but Joe already has concentration data output and the chart adds cost without a clear foundation benefit. |
| Richer historical visualization surfaces | Reference Evidence; Existing Spec | Category B - Deferred | Interesting, but too broad to justify as a current scope item without a narrower, evidence-backed use case. |
| Section-specific export parity beyond the current V1 subset | Reference Evidence; Existing Implementation | Category B - Deferred | Useful, but current V1 exports already cover the main workflow and the remaining parity work is lower priority. |

## 3. Recommended ND-01 Evaluation Scope

Recommended for further evaluation:

- explicit `data_as_of` provenance contract
- friend-style source ownership matrix for HKEXnews / 同花順 F10 / SDW / local DB-first routing
- HKEX announcements data path and surfaced table
- price history data path and surfaced history view
- DT Rainbow presentation
- broader raw previews and export catalogue

## 4. Deferred Items

- concentration chart presentation
- richer historical visualization surfaces
- section-specific export parity beyond the current V1 subset

## 5. Not Included Items

For current ND-01 scope, the following are not included:

- exact friend visual layout and screenshot choreography
- any attempt to promote Reference Evidence into mandatory requirements
- any attempt to treat friend-side source routing as an approved Joe Platform dependency without separate approval

## 6. Unconfirmed Items

- Exact SDW-to-local-DB ingestion mechanism on the friend side
- Exact current persistent database technology on the friend side
- Exact implementation of remaining Webb-site fallback paths
- Exact DT Rainbow data-generation architecture
- Whether every historical design statement remains identical in current production
- Any friend-side API detail beyond what is recorded in `REFERENCE_EVIDENCE.md`

## 7. Open Questions

- Should ND-01 evaluation prioritize metadata and provenance alignment before any new visualization work?
- Should the source ownership matrix be evaluated as architecture guidance only, or also as a candidate for future API/schema metadata alignment?
- Should announcements and price history be treated as first-class ND-01 evaluation tracks because they already exist in the V1 specification?
- What minimum evidence is needed before any DT Rainbow implementation discussion can begin?

## Governance Verification

- No code changed.
- No tests changed.
- No specification changed.
- Friend evidence remains reference only.
- No implementation approved.

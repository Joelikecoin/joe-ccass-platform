# RW-006-A Company Information Data Source Decision

## 1. Objective

Evaluate approved data source direction for the Company Information Layer:

- Announcements
- Stock Events
- Officers

This is a data-source decision review only. It does not approve implementation.

## 2. Evidence Basis

This decision uses only the evidence available in the workspace:

- `docs_reference_evidence/04_Evidence_Index/RW-006_COMPANY_INFORMATION_LAYER_ALIGNMENT_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/RW-004_SOURCE_RESPONSIBILITY_MAPPING.md`
- `docs_reference_evidence/04_Evidence_Index/REFERENCE_EVIDENCE.md`
- `docs/REFERENCE_SPEC.md`
- `docs/PROJECT_SPEC.md`
- current Joe Platform implementation evidence in `app/`, `ccass_core/`, `streamlit_app.py`, and `app/api.py`

If source support is not directly evidenced, it is marked Unconfirmed.

## 3. Capability Review

### 3.1 Announcements

| Item | Decision |
|---|---|
| Required capability | A visible company-announcements surface with publish time, category, title, file information, official URL, and objective event tags. |
| Source candidate | HKEXnews official announcements. |
| Evidence | `REFERENCE_EVIDENCE.md` records `get_hkex_announcements` with HKEXnews as primary and no Webb-site required. `docs/REFERENCE_SPEC.md` shows `HKEX Announcements` as an exact visible section and documents the required visible fields. |
| Status | Approved for Implementation |

Decision notes:

- This is the clearest and most maintainable company-information source direction in the evidence set.
- The source is official, reference-aligned, and does not depend on Webb-site for the primary path.

### 3.2 Stock Events

| Item | Decision |
|---|---|
| Required capability | Event records for the company-information layer, with objective dated event context that can support cross-checking with CCASS changes and price history. |
| Source candidate | Webb-site only, based on the current evidence. |
| Evidence | `REFERENCE_EVIDENCE.md` records `get_stock_events` as Webb-site only and says no non-Webb replacement is currently identified. `docs/REFERENCE_SPEC.md` shows an exact `Events` section label and export evidence for `Corporate Events`, `Share Capital Changes`, and `Buybacks`. |
| Status | Deferred |

Decision notes:

- The reference evidence supports the capability, but the source direction is not yet maintainable enough for approval in Joe.
- Because the evidence says there is no non-Webb replacement currently identified, this remains a deferred source decision rather than an approved implementation path.
- Relationship to CCASS changes and Price History is a presentation / analysis concern, not a separate source approval.

### 3.3 Officers

| Item | Decision |
|---|---|
| Required capability | Officer / management information with the visible fields implied by the reference exports, such as names, positions, tenure dates, current status, and profile details. |
| Source candidate | 同花順 F10 managers primary, with Webb-site historical fallback. |
| Evidence | `REFERENCE_EVIDENCE.md` records `get_stock_officers` with 同花順 F10 managers primary and Webb-site fallback. `docs/REFERENCE_SPEC.md` shows an exact `Officers` section label and documents `Managers F10` export fields. |
| Status | Need More Evidence |

Decision notes:

- The source direction is promising and reference-backed, but the workspace evidence is still thin on access, licensing, and operational reliability details.
- Before implementation approval, Joe needs a firmer answer on how the F10 source will be accessed and maintained in this environment.

## 4. Source Classification

| Source | Classification | Reason |
|---|---|---|
| HKEXnews announcements | Approved for Implementation | Official, reference-backed, and explicitly documented as primary without Webb-site dependency. |
| Webb-site stock events | Deferred | Supported by evidence, but the current evidence does not identify a maintainable non-Webb replacement and therefore does not justify immediate implementation approval. |
| 同花順 F10 managers | Need More Evidence | Primary source direction is evidence-backed, but operational details and maintainability are not yet sufficiently confirmed in the workspace. |
| Webb-site officers fallback | Unconfirmed | Mentioned in evidence as a fallback, but its exact implementation path is not supported well enough for approval. |

## 5. Architecture Impact

The company-information layer would need:

- a new collector or source adapter for announcements
- a new collector or source adapter for stock events if the feature is implemented beyond the current unavailable state
- a new source path for officers, likely with fallback behavior
- report integration for the new sections and their unavailable states
- API surface updates if these datasets are exposed outside the Streamlit/report layer

What is not approved here:

- new collectors without source approval
- speculative fallback routing
- schema changes beyond what the approved source actually requires

## 6. Final Recommendation

Approved next implementation item:

- Announcements via HKEXnews.

Deferred items:

- Stock Events, pending a maintainable source decision beyond Webb-site-only evidence.
- Officers, pending stronger evidence for the F10 access and operating model.

Unconfirmed items:

- Whether the stock-events path can be replaced by a maintainable non-Webb source.
- Whether the officers source can be operationalized in Joe without hidden licensing or access constraints.
- Whether additional company-information fields beyond the reference evidence should be included.

## 7. Governance Verification

Confirmed:

- No code changed
- No tests changed
- No data source added
- No collector created
- No requirements promoted
- Friend evidence remains reference only

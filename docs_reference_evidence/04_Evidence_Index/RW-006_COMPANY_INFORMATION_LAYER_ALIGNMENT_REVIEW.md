# RW-006 Company Information Layer Alignment Review

## 1. Evidence Basis

This review uses only the evidence available in the workspace:

- `docs_reference_evidence/04_Evidence_Index/REFERENCE_EVIDENCE.md`
- `docs_reference_evidence/04_Evidence_Index/RW-004_SOURCE_RESPONSIBILITY_MAPPING.md`
- `docs/REFERENCE_SPEC.md`
- `docs/PROJECT_SPEC.md`
- current Joe Platform implementation evidence in `app/`, `ccass_core/`, `streamlit_app.py`, and `app/api.py`

The unavailable `RW-004-A_DATA_CAPABILITY_PRIORITY_DECISION.md` is treated as Unconfirmed evidence.

## 2. Capability Comparison Table

| Capability | Friend Evidence | Joe Status | Classification |
|---|---|---|---|
| Announcements | The Reference Spec shows `HKEX Announcements` as a visible section and section anchor. It calls for publish time, category, title, file information, official URL, and objective event tags. The reference evidence also treats the announcements surface as part of the approved page structure. | Joe currently exposes an announcements UI shell and empty-state messaging, but no source-backed announcements collector or API path is implemented in the active application surface. | Replication Required |
| Stock Events | The Reference Spec shows an exact visible `Events` section-anchor label. It also documents export schemas with `Corporate Events`, `Share Capital Changes`, and `Buybacks`, including concrete event fields such as announced date, type, amount, ex-date, notes, and event URLs. | Joe does not expose a dedicated stock-events source, API route, or populated UI surface for stock events. | Replication Required |
| Officers | The Reference Spec shows an exact visible `Officers` section-anchor label and documents `Managers F10` fields in the approved export evidence. | Joe does not expose a dedicated officers source, API route, or populated UI surface for officers data. | Replication Required |
| Capital Information | The Reference Spec documents `Share Capital Changes` in the approved export evidence and includes `share_capital` fields in the workbook schema. This supports company-capital context, but the evidence is stronger on export/schema support than on a separate visible page section. | Joe does not expose a dedicated capital-information source, API route, or populated UI surface. | Future Enhancement |

## 3. Gap Analysis

- Announcements are required for reference alignment because the Reference Website presents them as a first-class visible section with structured metadata. Joe still lacks a source-backed announcements path, so the current UI shell is not enough for parity.
- Stock events and officers are also part of the documented reference information layer. Both appear in the reference page or export evidence, but Joe currently has no dedicated implementation for either capability.
- Capital information is supported by reference export evidence and clearly belongs to the broader company-information layer, but the workspace evidence is weaker on a separate visible page surface. That makes it a lower-confidence requirement than announcements, events, and officers.
- Joe’s current implementation remains centered on CCASS holdings, historical snapshots, and report metadata. The company-information layer is not yet represented as a first-class, source-backed capability set.

## 4. Recommendation

- Treat Announcements, Stock Events, and Officers as Replication Required items for the friend-aligned company-information layer.
- Treat Capital Information as a Future Enhancement that is strongly supported by reference export evidence, but not yet as clearly evidenced as a visible page requirement.
- Do not promote any of these capabilities into implementation work without separate source, data-contract, and UI approval.
- If the next phase targets reference parity beyond CCASS holdings, the company-information layer should be planned as a dedicated workstream rather than folded into CCASS-only maintenance.

## 5. Unconfirmed Items

- Whether `RW-004-A_DATA_CAPABILITY_PRIORITY_DECISION.md` would have changed the priority ordering for company-information features.
- The exact current visible layout and interaction flow of the friend `Events`, `Officers`, and company-capital surfaces beyond the approved evidence captures.
- Whether capital information is meant to appear as a user-facing section on the Reference Website or primarily as export / workbook data.
- Whether the friend implementation uses the same field labels and normalization rules for all company-information exports across versions.

## Governance Verification

Confirmed:

- No code changed
- No tests changed
- No data source added
- No requirement promoted
- Friend evidence remains reference only

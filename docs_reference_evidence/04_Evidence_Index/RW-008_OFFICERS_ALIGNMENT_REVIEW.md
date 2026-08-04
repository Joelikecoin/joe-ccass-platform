# RW-008 Officers Alignment Review

## 1. Evidence Basis

This review uses only the evidence already present in the workspace:

- `docs_reference_evidence/04_Evidence_Index/REFERENCE_EVIDENCE.md`
- `docs_reference_evidence/04_Evidence_Index/RW-006_COMPANY_INFORMATION_LAYER_ALIGNMENT_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/RW-006-A_COMPANY_INFORMATION_DATA_SOURCE_DECISION.md`
- `docs/REFERENCE_SPEC.md`
- current Joe Platform implementation evidence in `app/`, `ccass_core/`, `streamlit_app.py`, and `app/api.py`

Key evidence points:

- The reference spec contains an exact visible `Officers` section-anchor label.
- The reference export evidence contains a `Managers F10` section and confirms fields such as name, positions, tenure dates, current status, sex, age, education, salary, and biography.
- The reference evidence matrix records `get_stock_officers` as `同花順 F10 managers primary` with Webb-site historical fallback.
- Joe Platform currently exposes only an unavailable/officer-placeholder surface, not a source-backed officers capability.

## 2. Feature Comparison Table

| Item | Friend Evidence | Joe Status | Classification |
|---|---|---|---|
| Officers | The reference spec shows an exact visible `Officers` section-anchor label. The export evidence includes a `Managers F10` section with confirmed fields for officer / management records. | Joe shows only an officers placeholder / unavailable surface. There is no dedicated officers source, API route, or populated report data. | Replication Required |

## 3. Gap Analysis

Officers appears to be a distinct, visible company-information capability rather than a duplicate of announcements or stock events.

- It is not the same as Announcements: announcements are official dated notices; officers are management / role records.
- It is not the same as Stock Events: events are corporate-action or timeline records.
- It is not the same as Capital Information: capital is structural company data, while officers describe who is managing the company.
- In the reference evidence, officers belong to the broader company-information layer and are represented by the `Managers F10` export surface.

The current Joe implementation gap is twofold:

- there is no source-backed officers data path
- the visible UI/report surface is only a placeholder state

## 4. Recommendation

Replication Required at the feature level, but source approval is not yet complete.

Recommended interpretation:

- the friend-visible Officers surface should be treated as required for replication
- the current source candidate (`同花順 F10 managers`) should remain in `Need More Evidence` status until access, reliability, and maintainability are more fully confirmed

This means the feature is required by evidence, but not yet ready for implementation approval.

## 5. Unconfirmed Items

- The exact current visible layout of the friend Officers surface.
- Whether Officers appears as a standalone section, a subsection inside Full Report, or both.
- The exact interaction behavior for expand/collapse, if any, on the friend side.
- Whether the displayed officer fields on the page are identical to the export/workbook fields or a reduced subset.
- Whether the Webb-site historical fallback is actively visible to users or only used behind the scenes.

## 6. Relationship With Other Modules

Officers is best treated as supporting company-information data.

Relationship summary:

- Company Information: direct member of this layer.
- Announcements: related only by report grouping and company context; not a substitute.
- Stock Events: complementary historical context; not a substitute.
- Capital Information: also company-information data, but a separate concept from officers.

So the relationship is:

- independent module within the company-information layer
- supporting context for the overall company profile
- not derivable from Announcements or Stock Events

## 7. Data Source Evaluation

| Source | Assessment | Status |
|---|---|---|
| `同花順 F10 managers` | Evidence-backed as the primary direction for officers. The workspace evidence confirms the source family and the intended officer fields, but not the operational access, licensing, or maintainability details needed for implementation approval. | Need More Evidence |
| Webb-site historical fallback | Mentioned in evidence as a fallback path, but the exact implementation route is not sufficiently supported in the workspace. | Unconfirmed |

Conclusion:

- the source direction is plausible and evidence-backed
- the implementation path is not yet fully approved

## 8. Governance Verification

Confirmed:

- No code changed
- No tests changed
- No data source added
- No collector created
- No requirements promoted
- Friend evidence remains reference only

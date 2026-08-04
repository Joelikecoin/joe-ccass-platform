# RW-002 Historical Experience Alignment Review

## 1. Evidence Basis

This review uses only the preserved reference evidence and the current Joe Platform implementation evidence available in the workspace:

- `docs_reference_evidence/04_Evidence_Index/REFERENCE_EVIDENCE.md`
- `docs_reference_evidence/04_Evidence_Index/ND-02_FINAL_REVIEW.md`
- `ccass_core/report.py`
- `streamlit_app.py`
- `app/streamlit_ui.py`
- `tests/test_streamlit_ui.py`

The requested `FRIEND_WEBSITE_REPLICATION_MATRIX.md` and friend PDF/screenshot files were not directly available in the workspace, so any friend-side interaction detail that depends on them remains explicitly unconfirmed.

## 2. Feature Comparison Table

| Feature | Friend Evidence | Joe Status | Classification |
|---|---|---|---|
| Historical section placement | Reference evidence and the preserved review notes indicate historical content is shown as part of the full report detail experience, with secondary historical views separated from the first reading pass. | Joe places Historical Information after the core summary / metadata / detail flow, and it is not forced into the initial reading pass. | Completed |
| Information hierarchy | Friend evidence emphasizes progressive disclosure so the report can be read top-down before deeper historical content is opened. | Joe now shows summary and metadata first, then detailed sections, then historical information and optional controls. | Completed |
| Expand / collapse behavior | Reference evidence indicates full report detail is revealed through user interaction rather than all at once. | Joe uses expandable sections for detail surfaces, including historical information and the optional download / copy block. | Completed |
| User interaction flow | The friend reference is clearly interaction-driven, but the exact click path and default-open state of every historical panel are not fully preserved in the accessible workspace files. | Joe’s flow is interaction-driven as well, but the exact reference choreography cannot be verified from the files available here. | Unconfirmed |
| Concentration History | Friend evidence preserves a historical concentration surface as part of the reference report experience. | Joe renders concentration history in the report surface and keeps it available as part of the historical detail set. | Completed |
| Price History | Friend evidence preserves a visible price-history surface in the reference experience. | Joe still marks price history as unavailable in the current result. | Missing Capability |
| Snapshot / history information | Friend evidence suggests a clear historical presentation layer tied to dated snapshots and report context. | Joe has snapshot-aware reporting and history notes, but the exact friend-style historical presentation is not fully mirrored. | Alignment Required |
| Initial report loading | Friend evidence shows the core report should appear before heavy or optional views. | Joe loads the main report first and keeps optional surfaces separate. | Completed |
| Heavy visualization loading | Friend evidence indicates heavier views should not block first render. | Joe keeps the DT Rainbow surface optional and user-triggered rather than blocking the main report. | Completed |
| Optional loading behavior | Friend evidence supports a user-driven reveal pattern for optional content. | Joe follows the same pattern for optional visualization and detail sections. | Completed |

## 3. Gap Analysis

- The strongest confirmed gap is price history: the reference experience includes it as a visible historical surface, while Joe still reports it as unavailable.
- Joe’s overall historical presentation is now structurally close to the reference behavior: summary first, details later, and optional surfaces kept out of the initial load.
- The remaining difference is mostly in evidence certainty rather than obvious missing structure. The exact friend-side historical click choreography is not fully recoverable from the files available in this workspace.
- No evidence here suggests a need to promote new requirements. The current Joe implementation already covers the main historical-reading flow and optional loading behavior.

## 4. Recommendation

- No Action for the aligned historical presentation, expand / collapse behavior, and optional loading pattern.
- Future Evaluation for price history parity, because the current Joe result still marks that section unavailable.
- Future Evaluation for any finer-grained friend-specific historical choreography that depends on the missing matrix or PDF/screenshot files.

## 5. Unconfirmed Items

- The exact contents of `FRIEND_WEBSITE_REPLICATION_MATRIX.md`, because that file was not accessible in the workspace.
- The exact friend PDF / screenshot layout for historical panels.
- The exact default-open state of each reference historical section.
- Whether the friend site uses any additional historical controls beyond what is preserved in `REFERENCE_EVIDENCE.md`.
- Whether the reference price-history surface is purely informational or includes additional charting behavior not preserved in the accessible evidence.

## Governance

Confirmed:

- No code changed
- No tests changed
- Reference remains reference
- No requirements promoted


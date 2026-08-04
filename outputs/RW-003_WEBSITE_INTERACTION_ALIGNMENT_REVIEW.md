# RW-003 Website Interaction Alignment Review

## 1. Evidence Basis

This review uses only the evidence available in the workspace and the current Joe Platform implementation:

- `docs_reference_evidence/04_Evidence_Index/REFERENCE_EVIDENCE.md`
- `docs_reference_evidence/04_Evidence_Index/ND-02_FINAL_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/ND-01_REALITY_GAP_REVIEW.md`
- `ccass_core/report.py`
- `app/streamlit_ui.py`
- `streamlit_app.py`
- `tests/test_streamlit_ui.py`

The requested `FRIEND_WEBSITE_REPLICATION_MATRIX.md`, friend screenshots, and friend PDF evidence were not directly accessible in the workspace. Where the friend-side interaction details depend on those missing files, the classification is explicitly Unconfirmed.

## 2. Interaction Comparison Table

| Feature | Friend Evidence | Joe Status | Classification |
|---|---|---|---|
| Homepage / entry point | Reference evidence preserves the stock lookup entry flow, but the exact friend homepage composition is not directly available here. | Joe exposes a guided Streamlit entry page with sidebar controls and a visible fetch form. | Unconfirmed |
| Stock code input | Reference evidence preserves a stock-oriented lookup flow. | Joe supports stock code input and issue-ID-to-code lookup guidance. | Completed |
| User action flow | Reference evidence shows a fetch-oriented user journey from entry to report. | Joe follows the same fetch-oriented flow with validation, guidance, and report rendering. | Completed |
| Fetch trigger | Reference evidence indicates the report is produced from an explicit user action. | Joe requires an explicit Fetch action before building the report. | Completed |
| User guidance | Reference evidence preserves guided lookup behavior, but the exact friend-side helper copy is not fully accessible. | Joe displays input guidance and fetch guidance before the user starts a request. | Completed |
| Fetch started state | Friend evidence implies a loading state during report generation. | Joe shows staged progress messages while fetching and building the report. | Completed |
| Loading indication | Reference evidence supports visible loading feedback during the fetch/report process. | Joe shows progress states and status text. | Completed |
| Heavy component loading | Reference evidence indicates heavy views should not block the initial report. | Joe keeps DT Rainbow as an optional user-triggered surface rather than a blocking default. | Completed |
| Error / fallback messaging | Reference evidence preserves fallback and unavailable-state behavior. | Joe surfaces fetch failures, unavailable data, and warning states. | Completed |
| Result page structure | Reference evidence shows a report-first result page with visible report navigation. | Joe renders a structured report page with summary, navigation, report detail, visualization, and raw preview areas. | Completed |
| Section navigation | Reference evidence preserves jump links / section navigation. | Joe provides report navigation links that map to the rendered report sections. | Completed |
| Expand / collapse interaction | Reference evidence favors progressive disclosure for detailed content. | Joe uses expandable sections for report detail, history, downloads, and optional visualization controls. | Completed |
| Detail viewing flow | Reference evidence shows detailed content revealed through interaction instead of being fully expanded at first load. | Joe follows the same interaction model. | Completed |
| Copy actions | Reference evidence includes copy-oriented report usage. | Joe provides Copy for ChatGPT and Copy report actions. | Completed |
| Download actions | Reference evidence includes download-oriented report usage. | Joe provides CSV, Excel workbook, Markdown, and raw-preview downloads. | Completed |
| Export workflow | Reference evidence suggests a user-driven export path after the report is visible. | Joe groups export controls into a dedicated Download / Copy surface. | Alignment Required |
| Buttons placement | The exact friend button placement is not directly recoverable from the missing screenshots / PDF files. | Joe places copy/download controls in a dedicated expandable block instead of leaving them inline. | Alignment Required |
| Optional loading | Reference evidence implies optional surfaces should not delay the main report. | Joe keeps DT Rainbow and other heavy surfaces opt-in. | Completed |
| User-triggered components | Reference evidence preserves an interaction-first pattern. | Joe requires explicit user action to reveal DT Rainbow. | Completed |
| Interactive behaviour | Friend-side detailed interaction choreography is only partially preserved in the accessible evidence. | Joe supports expanding sections and toggling optional views, but exact friend choreography cannot be verified. | Unconfirmed |

## 3. Gap Analysis

- The strongest confirmed alignment is the core fetch-to-report flow: input, explicit fetch trigger, staged loading, report navigation, and expandable detail surfaces are all in place.
- The main remaining uncertainty is not a missing feature but a missing direct verification source. The friend screenshots and replication matrix are not available here, so the exact homepage composition and button placement cannot be verified precisely.
- Joe’s current implementation is clearly closer to the reference interaction style than the earlier V1 baseline, especially for progressive disclosure and optional heavy components.
- Export and copy behavior are present and functional; the only caveat is that the exact reference layout for those controls cannot be matched one-for-one without the missing friend assets.

## 4. Recommendation

- No Action for the core user-entry, loading, navigation, and optional-visualization behavior.
- Alignment Required only for exact visual placement / choreography details that depend on missing friend screenshots or the replication matrix.
- Future Evaluation if new friend evidence becomes available and a stricter interaction parity check is needed.

## 5. Unconfirmed Items

- The exact contents of `FRIEND_WEBSITE_REPLICATION_MATRIX.md`.
- The exact homepage composition in the friend website.
- The exact button placement and spacing from the friend screenshots.
- The exact click choreography for every expand/collapse panel in the friend full report.
- Whether the friend export workflow has any additional inline affordances beyond what is preserved in the accessible evidence.

## Governance Verification

Confirmed:

- No code changed
- No tests changed
- No requirements promoted
- Reference remains evidence only


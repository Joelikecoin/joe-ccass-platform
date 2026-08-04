# RW-007 Stock Events Alignment Review

## 1. Evidence Basis

This review uses only the workspace evidence already captured in the repository:

- `docs_reference_evidence/04_Evidence_Index/REFERENCE_EVIDENCE.md`
- `docs_reference_evidence/04_Evidence_Index/RW-006_COMPANY_INFORMATION_LAYER_ALIGNMENT_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/RW-006-A_COMPANY_INFORMATION_DATA_SOURCE_DECISION.md`
- `docs/REFERENCE_SPEC.md`
- current Joe Platform implementation evidence in `app/`, `ccass_core/`, `streamlit_app.py`, and `app/api.py`

Key evidence points:

- The reference spec contains an exact visible `Events` section-anchor label.
- The reference export evidence includes `Corporate Events`, `Share Capital Changes`, and `Buybacks`.
- The reference evidence matrix records `get_stock_events` as Webb-site only, with no non-Webb replacement currently identified.
- Joe Platform currently does not expose a dedicated, source-backed stock-events capability.

## 2. Feature Comparison Table

| Item | Friend Evidence | Joe Status | Classification |
|---|---|---|---|
| Stock Events | The reference spec shows an exact visible `Events` section-anchor label. The export evidence also includes `Corporate Events`, `Share Capital Changes`, and `Buybacks` with concrete event-oriented fields. The evidence matrix says `get_stock_events` is Webb-site only and no non-Webb replacement is currently identified. | Joe does not have a dedicated stock-events source, API route, or populated report surface. The current platform only shows a stock-events unavailable placeholder. | Missing Capability |

## 3. Gap Analysis

Stock Events is a distinct capability from Announcements.

- Announcements are now source-backed through HKEXnews and cover official announcement titles, dates, source attribution, and links.
- Stock Events, by contrast, is an event-history / corporate-action style layer. The reference evidence ties it to dated event records such as corporate events, share capital changes, and buybacks.
- Price History is complementary context, not a substitute. It can help explain market movement, but it does not provide the event records shown in the reference evidence.
- CCASS changes are also distinct. They describe holdings movement, while stock events provide a dated event timeline that can be used alongside holdings and price history.

The main gap is not just presentation. It is the absence of a supported source path and an implemented data surface in Joe.

## 4. Recommendation

Deferred.

The reference evidence supports Stock Events as a visible friend capability, but the source direction remains Webb-site only in the current evidence set, and no maintainable non-Webb replacement has been approved. That means implementation should not proceed yet.

Recommended next step:

- keep Stock Events in deferred state until a supported source decision is approved
- treat Announcements, Price History, and CCASS changes as separate surfaces rather than collapsing Stock Events into them

## 5. Unconfirmed Items

- The exact interactive layout of the friend Stock Events surface beyond the visible `Events` anchor.
- Whether the friend surface is intended as a standalone section, a subsection inside Full Report, or both.
- The exact empty-state and error-state presentation for the friend Stock Events view.
- Whether the exported event fields map one-to-one to the on-page presentation or are richer than the visible surface.
- Whether a non-Webb source for Stock Events can be approved later without changing the intended user experience.

## 6. Governance Verification

Confirmed:

- No code changed
- No tests changed
- No data source added
- No collector created
- No requirements promoted
- Friend evidence remains reference only

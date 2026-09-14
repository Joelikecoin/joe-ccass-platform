# Fresh Stock Timeout Fix Production Acceptance Lock

- Deployed SHA: `9d3f74612bd15dd66870218e75dab626e3a9c00b`
- Render deploy ID: `dep-dajt8cm7bikc73de2k40`
- Production health: PASS

## Fresh-stock acceptance

### 09999

- Pre-run snapshot count: 0
- First request: 26.487s
- HTTP status: 200
- Terminal state: COMPLETE
- Source: Longbridge
- Data date: 2026-09-11
- Holdings rows: 238
- Snapshot persisted: YES
- Post-run snapshot count: 1
- Changes: WAITING_SECOND_SNAPSHOT
- Big Changes: WAITING_SECOND_SNAPSHOT
- Concentration: COMPLETE
- Cached: NO
- Fallback: NO

### 03690

- Pre-run snapshot count: 0
- First request: 23.075s
- HTTP status: 200
- Terminal state: COMPLETE
- Source: Longbridge
- Data date: 2026-09-11
- Holdings rows: 420
- Snapshot persisted: YES
- Post-run snapshot count: 1
- Changes: WAITING_SECOND_SNAPSHOT
- Big Changes: WAITING_SECOND_SNAPSHOT
- Concentration: COMPLETE
- Cached: NO
- Fallback: NO

## SLA and observability

- Target <=60 seconds: PASS
- Hard terminal <=90 seconds: PASS
- Production runtime failure: NO
- Client connectivity failure observed in a prior check: YES; this was a client-path issue, not a production runtime failure.
- Both fresh-stock requests reached truthful COMPLETE terminal states with real Longbridge data and persistence.
- The first snapshot correctly reports Changes and Big Changes as `WAITING_SECOND_SNAPSHOT`.
- A non-blocking telemetry label defect was observed: trace entries inside both fresh-stock request windows incorrectly carried `stock=06182`. Per-stage attribution is partial, while the non-overlapping request windows and end-to-end results remain independently verified. This is recorded and not changed in this acceptance lock.

TIMEOUT_FIX_PRODUCTION_ACCEPTANCE=PASS
FRESH_STOCK_FIRST_REQUEST_SLA=PASS
P0_RUNTIME_SLA=LOCKED_PASS
OBSERVABILITY_LABEL_DEFECT=NON_BLOCKING

No runtime behavior, feature selection, or product scope was changed by this acceptance lock.

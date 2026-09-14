# P0 Runtime SLA Final Lock

P0 runtime acceptance is locked to the proven fresh-stock production evidence below.

## Deployment

- Timeout-fix SHA: `9d3f74612bd15dd66870218e75dab626e3a9c00b`
- Render deploy ID: `dep-dajt8cm7bikc73de2k40`
- Existing acceptance lock: `docs_reference_evidence/latest_reference_updates/2026-09-14_FRESH_STOCK_TIMEOUT_FIX_PRODUCTION_ACCEPTANCE_LOCK.md`
- Existing acceptance-lock commit: `c4db4f7a424ba1551a8e88be58e6667423ba97a4`

## Fresh-stock proof

### 09999

- Pre-run snapshots: 0
- First request: 26.487s
- HTTP: 200
- Terminal: COMPLETE
- Source: Longbridge
- Data date: 2026-09-11
- Holdings rows: 238
- Snapshot persisted: YES; post-run snapshots: 1
- Changes: WAITING_SECOND_SNAPSHOT
- Big Changes: WAITING_SECOND_SNAPSHOT
- Concentration: COMPLETE
- Cached: NO
- Fallback: NO

### 03690

- Pre-run snapshots: 0
- First request: 23.075s
- HTTP: 200
- Terminal: COMPLETE
- Source: Longbridge
- Data date: 2026-09-11
- Holdings rows: 420
- Snapshot persisted: YES; post-run snapshots: 1
- Changes: WAITING_SECOND_SNAPSHOT
- Big Changes: WAITING_SECOND_SNAPSHOT
- Concentration: COMPLETE
- Cached: NO
- Fallback: NO

## Governance lock

- Target <=60 seconds: PASS
- Hard terminal <=90 seconds: PASS
- Production runtime failure: NO
- Observability label defect: NON_BLOCKING. Some trace records incorrectly carry `stock=06182`; this affects telemetry attribution only and does not invalidate elapsed time, HTTP 200, real Longbridge data, Holdings rows, persistence, terminal state, or SLA acceptance.

P0_RUNTIME_SLA=LOCKED_PASS
FRESH_STOCK_FIRST_REQUEST_SLA=LOCKED_PASS
TIMEOUT_FIX_PRODUCTION_ACCEPTANCE=LOCKED_PASS
REOPEN_REQUIRES_NEW_PRODUCTION_REGRESSION_EVIDENCE=YES

## Reopen rule

P0 runtime SLA may be reopened only for new production evidence proving one of: a genuine fresh stock fails to terminate within 90 seconds; real Holdings fails where the production source is available; snapshot persistence fails; successful core sections disappear because of supplemental-source failure; or production regresses from this accepted behavior.

Transient client HTTP 000, browser/client blocking, telemetry label mismatch, local-only failures, mock or fixture failures, UI wording, feature-selection discussion, optional supplemental unavailability, and warm-stock timing differences do not reopen this lock.

No runtime behavior, deployment, feature selection, or product scope was changed by this governance lock.

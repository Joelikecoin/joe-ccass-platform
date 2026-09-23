# CROSS_SOURCE_INTELLIGENCE_V1_PRODUCTION_ACCEPTANCE

## Precheck

| Field | Result |
|---|---|
| LOCAL_HEAD | `3324d8625d682c304e875d94867a1cc59e362da5` |
| CURRENT_DEPLOYED_SHA | `UNKNOWN`; historical evidence records `6a7049a85639650ee136c20d9f9293a034a0fd05` |
| DEPLOY_TARGET | Render service `joe-ccass-api`, service id `srv-dads94740ujc73cpdktg`, Singapore; start command `python -m uvicorn app.portal_8504:app --host 0.0.0.0 --port $PORT` |
| PRODUCTION_DB_SELECTION | Existing policy says Turso persistence; live runtime selection is not externally readable |
| WORKTREE | DIRTY; current Cross-Source changes and pre-existing Longbridge changes are uncommitted |

## Deployment result

Deployment was not attempted. Render CLI is not installed, `RENDER_API_KEY` is missing, and the repository remote is SSH-only. The current branch is `codex/render-branch-sync`, while the Render deployment branch is not independently verified. Deploying would require Owner credentials/action and a deliberate commit containing the scoped changes; no uncommitted or unrelated files were pushed.

## Live validation

- `https://joe-ccass-api.onrender.com/health` returned HTTP 200 with `{"status":"ok","app":"joe-ccass-visual-portal-8504"}`.
- `https://joe-ccass-api.onrender.com/openapi.json` returned HTTP 200.
- Live OpenAPI contains no `/api/v1/cross-source/*` routes.
- Production DB connection, table schema, persistence read/write, restart persistence and deployed SHA could not be verified without deployment/runtime access.

## Local acceptance evidence

The local implementation and existing integration tests remain green:

```text
pytest -q tests/test_cross_source_intelligence.py tests/test_cross_source_persistence.py tests/test_stock_events.py tests/test_api_report.py
19 passed
```

Local OpenAPI contains:

- `/api/v1/cross-source/entities/{entity_id}/securities`
- `/api/v1/cross-source/securities/{security_id}/timeline`
- `/api/v1/cross-source/securities/{security_id}/sequence`
- `/api/v1/cross-source/interval`
- `/api/v1/cross-source/fingerprint`

Local tests cover real existing source model conversion, explicit participant/security relationships, normalized event timeline and deduplication, ordered sequences, calendar/trading interval output, fingerprint matched/unmatched/unknown output, evidence lineage, and append-only idempotent persistence. This is local acceptance evidence, not production acceptance.

## Acceptance decision

`DEPLOY_PASS=NO`
`LIVE_API_PASS=PARTIAL`
`PRODUCTION_DB_PASS=UNKNOWN`
`REAL_SAMPLE_PASS=LOCAL_ONLY`
`EVIDENCE_DRILLDOWN_PASS=LOCAL_ONLY`
`PRODUCTION_ACCEPTANCE_PASS=NO`

Issued-share denominator, HKEX holiday calendar, historical aliases and source-specific backfill remain `UNKNOWN`/`PARTIAL` limitations and are not deployment blockers. The actual blocker is deployment authorization/access and production runtime verification.

## Required Owner action

Provide or authorize the Render deployment path/credential, confirm the intended deployment branch or commit, and authorize production read-only DB/API acceptance. Then deploy the scoped current changes, verify the deployed SHA, run live route/sample/drill-down checks, and record restart persistence evidence.

## 2026-09-23 — Scoped commit and deployment gate update

- Scoped Cross-Source commit: `422ef6710529e9dce521219f0da1ffc30af35c98` (`feat: integrate cross-source intelligence routes and persistence`).
- The commit was pushed successfully to `origin/codex/cross-source-v1-production-acceptance`.
- The tracked historical deployment branch rejected a non-fast-forward push because it contains 53 commits absent locally; no force push or unrelated merge was performed.
- Render CLI, `RENDER_API_KEY`, service credentials, and production database credentials remain unavailable in this runtime.
- Live health remains HTTP 200, but live OpenAPI still has no Cross-Source routes; deployed SHA remains unverified.
- Final gate remains `PRODUCTION_ACCEPTANCE_PASS=NO` pending deployment of commit `422ef6710529e9dce521219f0da1ffc30af35c98` through the authorized Render path.

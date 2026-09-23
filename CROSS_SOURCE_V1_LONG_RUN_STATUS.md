# CROSS_SOURCE_V1_LONG_RUN_STATUS

Run date: 2026-09-23 (Asia/Hong_Kong)

| Track | Status | Evidence | Blocker / safe next action |
|---|---|---|---|
| A1 authorized API-key path | BLOCKED | Render service metadata and GitHub workflow identify `secrets.API_KEY`; value is unavailable here | Owner runs authenticated checks from an authorized secret-bearing environment; never paste the key into chat |
| A2 authorized Turso path | BLOCKED | Code uses `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`; Render logs show successful Turso persistence events | Owner runs read-only schema/read-back query from authorized runtime |
| A3 live API route surface | PASS | Live health/OpenAPI HTTP 200; all five Cross-Source routes listed; unauthenticated interval returns expected 401 | Authenticated samples remain pending |
| A4 production DB schema/read-back | BLOCKED | No DB credentials exposed; no destructive operation attempted | Read-only query against deployed runtime database |
| B1-B11 readiness tests | PASS | Cross-Source/portal/API/persistence regression: 43 passed; full suite: 580 passed, 5 unrelated existing failures | Keep unrelated failures separate from this scope |
| B12 restart/persistence readiness | PARTIAL | Append-only idempotent persistence test passed; Render deployment reached live; Turso persistence logs exist | Verify canonical read-back after authenticated request/restart |
| B13 migration/readiness review | PARTIAL | `cross_source_records` uses additive `CREATE TABLE IF NOT EXISTS` on existing repository path; no numbered migration rewrite | Confirm table/schema in production DB read-only |
| B14 acceptance checklist | PARTIAL | Deployment, route, health, OpenAPI, auth-failure and local lineage evidence recorded | Complete authenticated samples and DB verification |
| C1 source-to-canonical adapters | PASS | `adapt_ccass_response`, `adapt_stock_events_response` preserve source/date/lineage fields | Expand only when approved source payloads require it |
| C2 security identity mapping | PARTIAL | Canonical `security:{code}` and issue identity are retained from CCASS metadata | Historical aliases/listing history remain outside V1 |
| C3 CCASS participant mapping | PASS | Participant IDs remain source-native and map to participant holding relationships | Do not interpret participant as beneficial owner |
| C4 event-source mapping | PASS | Normalized stock events retain source, event date, evidence state and lineage | Missing source rows remain unknown |
| C5 historical lineage | PASS | Canonical records carry source_id/source_date/valid_from/valid_to/evidence state; core outputs carry lineage | Production read-back still pending |
| C6 backfill orchestration | NOT_REQUIRED | No source-wide backfill was requested or executed | Future work must be separately authorized |
| D documentation | PASS | This file, PROJECT_PROGRESS.md and production acceptance evidence updated | Keep production evidence synchronized after authenticated run |
| E next-stage readiness | PASS | Checklist created in `CROSS_SOURCE_V1_NEXT_STAGE_READINESS.md`; no empirical execution | Execute only after API/DB gates pass |

## Known unrelated full-suite failures

The full repository run produced 580 passed and five failures in pre-existing Streamlit/deployment compatibility tests. They are not caused by Cross-Source code and were not changed in this run.

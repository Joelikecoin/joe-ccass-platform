# Feature Engineering Dependency Map

## Shared flow

8504 input and controls → `app/portal_8504.py` → `app/friend_clone_app.py` / `app/streamlit_ui.py` → services and source adapters → normalization/domain models → `NormalizedSnapshotRepository` / SQLite history → FastAPI routes in `app/api.py` → MCP tools in `app/mcp_server.py` and download/report builders.

## Core trusted chain

- Stock code/source/fetch → parse → validate → normalize → persistent snapshot DB.
- Holdings reads the exact persisted Longbridge snapshot.
- Changes compares the current snapshot with the previous persisted snapshot.
- Big Changes consumes the same comparison chain and threshold logic.
- Concentration reads an exact persisted snapshot and derives participant concentration.
- History endpoints and MCP history tools expose the persisted dates/payloads.
- Scheduled snapshot work calls the daily snapshot runner and persistence path; keep-alive only affects availability/wake behavior.

## Feature paths

| Area | Frontend | Backend/source | Storage | API/MCP/export | Shared dependency |
|---|---|---|---|---|---|
| Input, metadata, loading, terminal states | `app/portal_8504.py` | portal bundle and request context | none | portal response | all sections |
| Holdings and history | 8504 report sections | `StockDataService`, Longbridge source, validation/normalization | snapshot DB | stock/holdings, history, MCP history, reports/downloads | DIRECT P0 |
| Changes | 8504 Changes section | `ChangesService` / changes report | two persisted snapshots | changes/report/MCP/download | DIRECT P0 |
| Big Changes | 8504 Big Changes section | `BigChangesService` / report builder | two persisted snapshots | big-changes/report/MCP/download | DIRECT P0 |
| Concentration and Rainbow | 8504 Concentration/Rainbow | `ConcentrationService`, rainbow builders | persisted snapshots | concentration/evidence/rainbow/MCP/download | SHARED P0 |
| Announcements/events/officers/capital | 8504 supplemental sections | dedicated services and source adapters | response/cache where implemented | API routes and section downloads | supplemental |
| Price and Price History | 8504 market sections | price services/source | response/cache | API and exports | supplemental |
| Reports and downloads | 8504 action links | report/artifact builders | reads response/persisted data | REST/MCP/download routes | shared output |
| REST API/MCP | API clients and tools | `app/api.py`, `app/mcp_server.py` | reads shared services/repository | JSON/tool contracts | shared integration |
| Scheduler/keep-alive | workflow/ops | `app/daily_snapshot.py`, scheduler handlers | writes snapshot DB | admin/job APIs | P0 persistence |

## Separability audit

Core snapshot, validation, normalization, persistence, service, API, and 8504 paths are shared. A supplemental section can usually be hidden independently, but disabling or removing its source may still affect shared request timing and warning aggregation. Changes, Big Changes, Concentration, History, and scheduled snapshots are tightly coupled to the trusted persisted chain and are not independently removable without a P0 review.

## P0 protection map

| Component | Protection | Reason |
|---|---|---|
| Stock code, source, fetch, parse, validate, normalize | DIRECT | Required to create trusted snapshots |
| Persistent DB and history | DIRECT | Required for reload/restart and comparison |
| Holdings | DIRECT | Core persisted output |
| Changes, Big Changes, Concentration | DIRECT/SHARED | Derived from trusted snapshots |
| API, MCP, exports, 8504 UI | SHARED | Multiple surfaces consume the same contracts |
| Supplemental sources/sections | NONE or SHARED | Can be isolated only after dependency checks |

No deletion, toggle, or runtime disable is performed by this map.

## Test and dead-code evidence

Direct route tests are strong for officers, stock events, capital, announcements, prices, holdings, Changes, Big Changes, Concentration, downloads, and source status. No direct route test was found for corporate timeline, share-capital-history, historical intelligence, or four Longbridge detail routes. `portal_8504.py` is the only numbered production portal; 8501–8503 are absent. `friend_clone_app.py` and Streamlit remain referenced legacy/shared paths. No files were deleted.

## Observability fix boundary

`app/friend_clone_app.py` previously emitted a constant 06182 stock label. The isolated fix passes `resolved_code` to each `_p0_bundle_trace` call. This changes telemetry attribution only and leaves the product data chain untouched.

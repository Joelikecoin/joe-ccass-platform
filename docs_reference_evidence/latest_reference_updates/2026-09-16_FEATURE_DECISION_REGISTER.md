# Feature Decision Register

This register is descriptive preparation for Joe. Every decision remains `UNDECIDED`; no visibility, runtime, or removal choice was made. Reference directories absent locally are recorded as unresolved rather than inferred.

| ID | Feature / user-visible surface | Category | JOE_DECISION | Reference | Current | Status | Source/storage | API | MCP | P0 dependency | Parity | Toggle readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F001 | Stock code input | Input | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F002 | Source selector/mode | Input | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F003 | timeout | Runtime | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | NOT_APPLICABLE |
| F004 | progress/loading | Runtime | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | 8504 portal or download route | No direct MCP evidence | NONE | UNKNOWN | NOT_APPLICABLE |
| F005 | terminal states | Runtime | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | SHARED | UNKNOWN | NOT_APPLICABLE |
| F006 | stock name | Metadata | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F007 | data date | Metadata | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F008 | source metadata | Metadata | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | SHARED | UNKNOWN | PARTIAL |
| F009 | source-used metadata | Metadata | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | SHARED | UNKNOWN | PARTIAL |
| F010 | mirror status | Metadata | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F011 | ID lookup | Source | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F012 | local history depth | History | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F013 | Holdings | Core analysis | UNDECIDED | YES | YES | WORKING | Longbridge + persistent SQLite/Turso history; Persistent snapshot DB | app/api.py route(s) | app/mcp_server.py where exposed | DIRECT | MATCH | PARTIAL |
| F014 | Changes | Core analysis | UNDECIDED | YES | YES | WORKING | Longbridge + persistent SQLite/Turso history; Persistent snapshot DB | app/api.py route(s) | app/mcp_server.py where exposed | DIRECT | MATCH | PARTIAL |
| F015 | Big Changes | Core analysis | UNDECIDED | YES | YES | WORKING | Longbridge + persistent SQLite/Turso history; Persistent snapshot DB | app/api.py route(s) | app/mcp_server.py where exposed | DIRECT | MATCH | PARTIAL |
| F016 | Concentration | Core analysis | UNDECIDED | YES | YES | WORKING | Longbridge + persistent SQLite/Turso history; Persistent snapshot DB | app/api.py route(s) | app/mcp_server.py where exposed | DIRECT | MATCH | PARTIAL |
| F017 | Top5 / Top10 | Core analysis | UNDECIDED | PARTIAL | YES | WORKING | Longbridge + persistent SQLite/Turso history; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | SHARED | PARTIAL | PARTIAL |
| F018 | percentage basis | Core analysis | UNDECIDED | UNKNOWN | YES | WORKING | Longbridge + persistent SQLite/Turso history; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | SHARED | UNKNOWN | PARTIAL |
| F019 | participant information | Core analysis | UNDECIDED | PARTIAL | YES | WORKING | Longbridge + persistent SQLite/Turso history; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | SHARED | PARTIAL | PARTIAL |
| F020 | history/snapshot history | History | UNDECIDED | UNKNOWN | YES | WORKING | Longbridge + persistent SQLite/Turso history; Persistent snapshot DB | app/api.py route(s) | app/mcp_server.py where exposed | DIRECT | MATCH | PARTIAL |
| F021 | Price | Market data | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F022 | Price History | Market data | UNDECIDED | UNKNOWN | YES | UNKNOWN_RUNTIME | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F023 | Announcements | Historical intelligence | UNDECIDED | YES | YES | WORKING | HKEX/Webb/Longbridge as implemented; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | PARTIAL | YES |
| F024 | announcement period/count | Historical intelligence | UNDECIDED | UNKNOWN | YES | WORKING | HKEX/Webb/Longbridge as implemented; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | PARTIAL | YES |
| F025 | Events | Historical intelligence | UNDECIDED | UNKNOWN | YES | PARTIAL | HKEX/Webb/Longbridge as implemented; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F026 | Officers | Historical intelligence | UNDECIDED | UNKNOWN | YES | UNAVAILABLE | HKEX/Webb/Longbridge as implemented; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F027 | Capital | Historical intelligence | UNDECIDED | UNKNOWN | YES | UNAVAILABLE | HKEX/Webb/Longbridge as implemented; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F028 | buybacks | Historical intelligence | UNDECIDED | UNKNOWN | YES | UNKNOWN_RUNTIME | HKEX/Webb/Longbridge as implemented; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F029 | Rainbow / participant concentration visual | Analysis visual | UNDECIDED | PARTIAL | YES | WORKING | Longbridge + persistent SQLite/Turso history; No dedicated storage / response metadata | app/api.py route(s) | app/mcp_server.py where exposed | SHARED | PARTIAL | PARTIAL |
| F030 | data quality warnings | Metadata | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | SHARED | UNKNOWN | NOT_APPLICABLE |
| F031 | raw previews | Diagnostics | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |
| F032 | jump navigation | Navigation | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | 8504 portal or download route | No direct MCP evidence | NONE | UNKNOWN | YES |
| F033 | language selector | UX | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | 8504 portal or download route | No direct MCP evidence | NONE | UNKNOWN | YES |
| F034 | reports | Output | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | 8504 portal or download route | app/mcp_server.py where exposed | SHARED | UNKNOWN | PARTIAL |
| F035 | downloads | Output | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | 8504 portal or download route | app/mcp_server.py where exposed | SHARED | UNKNOWN | PARTIAL |
| F036 | CSV | Output | UNDECIDED | YES | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | 8504 portal or download route | app/mcp_server.py where exposed | NONE | MATCH | YES |
| F037 | Excel | Output | UNDECIDED | YES | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | 8504 portal or download route | app/mcp_server.py where exposed | NONE | MATCH | YES |
| F038 | Snapshot DB Backup | Output | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | 8504 portal or download route | No direct MCP evidence | NONE | MATCH | YES |
| F039 | section CSV | Output | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | 8504 portal or download route | No direct MCP evidence | NONE | UNKNOWN | YES |
| F040 | Markdown | Output | UNDECIDED | YES | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | 8504 portal or download route | app/mcp_server.py where exposed | NONE | MATCH | YES |
| F041 | Raw Tables JSON | Output | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | 8504 portal or download route | app/mcp_server.py where exposed | NONE | UNKNOWN | YES |
| F042 | REST API | Integration | UNDECIDED | YES | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | app/mcp_server.py where exposed | SHARED | MATCH | PARTIAL |
| F043 | MCP | Integration | UNDECIDED | YES | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | app/mcp_server.py where exposed | SHARED | MATCH | PARTIAL |
| F044 | shared core | Infrastructure | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | DIRECT | UNKNOWN | NOT_APPLICABLE |
| F045 | schema version | Infrastructure | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | NOT_APPLICABLE |
| F046 | UTF-8 CSV behavior | Output | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | NOT_APPLICABLE |
| F047 | section metadata | Metadata | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | SHARED | UNKNOWN | PARTIAL |
| F048 | incompatible schema behavior | Infrastructure | UNDECIDED | UNKNOWN | YES | UNKNOWN_RUNTIME | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | NOT_APPLICABLE |
| F049 | scheduled snapshot behavior | Automation | UNDECIDED | UNKNOWN | YES | UNKNOWN_RUNTIME | Longbridge + persistent SQLite/Turso history; Persistent snapshot DB | app/api.py route(s) | No direct MCP evidence | DIRECT | UNKNOWN | NOT_APPLICABLE |
| F050 | keep-alive behavior | Automation | UNDECIDED | UNKNOWN | YES | UNKNOWN_RUNTIME | Longbridge + persistent SQLite/Turso history; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | NOT_APPLICABLE |
| F051 | history proof/internal verification surfaces | Diagnostics | UNDECIDED | UNKNOWN | YES | WORKING | Local application/shared core; No dedicated storage / response metadata | app/api.py route(s) | No direct MCP evidence | NONE | UNKNOWN | YES |

## Neutral decision consequences

For every row above, the following consequences apply; they are not recommendations.

- **KEEP:** no code change; existing UI, fetch, calculations, API/MCP and exports remain active. Verify the current contract and its dependent shared chain.
- **HIDE_ONLY:** change only the relevant 8504 entry/section or navigation. Backend fetch and calculations remain active; API, MCP, and export surfaces remain available unless separately changed.
- **DISABLE_RUNTIME:** stop only the feature’s fetch/calculation/scheduled work, preserve implementation where possible, define truthful UI/API/MCP unavailable semantics, and check shared-core and persistence effects before execution.
- **REMOVE:** remove the feature’s frontend, service/source/parser, routes, MCP/export hooks, and tests only after dependency review; migration, rollback, and contract compatibility work may be required.

### Per-feature execution fields

Each feature requires the same later review fields: code change, runtime change, user-visible effect, dependency effect, and tests for KEEP; frontend files and retained backend/API/MCP/export behavior for HIDE_ONLY; fetch/calculation/scheduler/storage/UI/API/MCP effects for DISABLE_RUNTIME; files, imports, contracts, DB/export/shared-core effects, migration, rollback, and tests for REMOVE. No field is selected in this preparation.

## Counts

TOTAL_FEATURES=51
REFERENCE_MATCH=10
REFERENCE_PARTIAL=3
REFERENCE_GAP=0
REFERENCE_UNKNOWN=39
WORKING=44
PARTIAL=1
UNAVAILABLE=2
UNKNOWN_RUNTIME=5
P0_DIRECT=7
P0_SHARED=15
P0_NONE=30
TOGGLE_READY_YES=25
TOGGLE_READY_PARTIAL=17
TOGGLE_READY_NO=0
TOGGLE_READY_NA=10
JOE_DECIDED=0
JOE_UNDECIDED=51

## Evidence boundary

Latest acceptance locks are present under `docs_reference_evidence/latest_reference_updates`. The requested friend-engineering, architecture, website, and source-document directories are absent locally; no claims about their contents are made.
## Test coverage map

Coverage is based on repository tests inspected during this preparation. `UNIT` means focused service/model tests; `INTEGRATION` means API/service tests; `E2E` means portal/runtime acceptance evidence.

| Feature groups | Test coverage | Representative tests/evidence |
|---|---|---|
| Holdings, Changes, Big Changes, Concentration | MULTIPLE | `tests/test_holdings.py`, `tests/test_changes.py`, `tests/test_big_changes.py`, `tests/test_concentration.py`, `tests/test_portal_8504.py`, locked production acceptance |
| Officers, Events, Capital, Announcements, Prices | INTEGRATION | `tests/test_officers.py`, `tests/test_stock_events.py`, `tests/test_capital_information.py`, announcement/price tests |
| Downloads and artifacts | MULTIPLE | `tests/test_download_api.py`, `tests/test_portal_8504.py`, MCP artifact tests |
| History, persistence, scheduler lifecycle | MULTIPLE | history/storage/portal snapshot tests and locked production evidence |
| Corporate timeline, share-capital-history, historical intelligence route parity | NONE or PARTIAL | no direct corporate-timeline or share-capital-history route test found; route parity remains a test gap |
| Longbridge detail routes | NONE | no direct tests found for the four detail routes identified in the audit |
| Language, jump navigation, wording, raw previews | UNIT / INTEGRATION | portal/render and report tests where present; exact production parity remains partial |

REFERENCE_PARITY_TEST=NO for route surfaces without a direct reference test. PRODUCTION_ACCEPTANCE_EVIDENCE=YES only where a locked production record explicitly proves it; otherwise NO.

## Dead and duplicate implementation audit

- `app/portal_8504.py`: ACTIVE production entrypoint.
- `app/friend_clone_app.py`: LEGACY_BUT_REFERENCED shared HTML/report and download path.
- `streamlit_app.py` plus `app/streamlit_ui.py`: LEGACY_BUT_REFERENCED alternate UI path.
- `app/api.py`: ACTIVE canonical REST app; some routes are independently re-exposed by the production portal and require parity review.
- 8501/8502/8503 portal files: PROVEN_DEAD/ABSENT in local repository and branch history; no deletion was performed.
- Duplicate download/artifact implementations across `app/api.py`, `app/portal_8504.py`, and `app/friend_clone_app.py`: ACTIVE or LEGACY_BUT_REFERENCED, with drift risk; no deletion was performed.
- Historical source adapters and aliases: UNKNOWN unless directly referenced by the registry/service tests; no removal decision was made.

## Observability defect

Root cause proven: `_p0_bundle_trace` in `app/friend_clone_app.py` hard-coded `stock="06182"` for every bundle trace. A telemetry-only fix was applied in a separate commit; each trace call now receives the resolved stock code. A direct test emitted labels for 09999 and 03690 and passed. No product response, persistence, API contract, or feature visibility changed.

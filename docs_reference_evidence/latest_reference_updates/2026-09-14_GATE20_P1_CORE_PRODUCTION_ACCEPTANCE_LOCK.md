# Gate 20 / P1 Core Production Acceptance Lock

Date: 2026-09-14

## Production deployment

- Service: `joe-ccass-api`
- Render deploy: `dep-dajsac95efls73a5uju0`
- Status: `LIVE`
- Production application SHA: `86ff8f5ef700710a4f947bdff0564d14cf5b0d68`

## Gate 20 verifier

- Workflow: `Gate20 postdeploy verification`
- Run: `34830999323`
- Result: `success`
- Temporary verifier cleanup: completed
- Cleanup commit: `3f4d2372e8bada06c7fc8406f5a1a4ab680a07fe`

The production verifier checked `/download/holdings/csv?code=...` for `00005`,
`00006`, and `06182`. Each response contained non-empty real holdings rows,
UTF-8-SIG, `schema_version=1`, `section_status=ready`, truthful source, and
`data_as_of`. The verifier also confirmed `schema_version=2` returns HTTP 400
with `SCHEMA_VERSION_UNSUPPORTED`.

Existing regression evidence confirms the same export contract through REST,
MCP, and the 8504 download surface; `tests/test_download_api.py` passed 10
tests and compileall passed.

## Closure

- Gate 20: PASS
- P0 regression: PASS
- P1 core parity: PASS
- Next allowed priority: Gate 22 / P2 only

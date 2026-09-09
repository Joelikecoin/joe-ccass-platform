# Joe CCASS Platform — Home Codex Handover

Date: 2026-09-09
Purpose: Bring the latest production P0 state to the home-computer Codex without relying on chat history.

## 1. Authority / source policy

Use `docs_reference_evidence/latest_reference_updates` first.

For the current architecture, prioritize the newer Longbridge/Turso/Render references, especially:

- `04092026mcp.longbridge.com 嘅原始碼用途.md`
- `06092026 Turso監視股票內部方式.md`
- `06092026Render免費plan控制的事項.md`
- `06092026Render + Longbridge + Webb-site mirror + AI 每朝分析」的完整資料架構.md`

Do NOT use these three older documents as architecture authority; Joe has explicitly retired them because they pre-date the Longbridge production design:

- `1 - AI_港股財技數據平台_由零開始完整指南.md`
- `2 - AI港股財技數據平台_數據源完整指南_整合版.md`
- `2026-08-24_朋友CCASS原系統_工程難題正式答覆.md.md`

Permanent current-production policy:

`Longbridge -> validate -> normalize -> persist Turso -> Service/API -> 8504`

Fallback on temporary Longbridge failure:

`trusted Turso snapshot -> STALE/PARTIAL`

If neither is available:

`UNAVAILABLE/ERROR`

Webb/0xmd is historical/specialized only. It must not return to synchronous current Holdings routing.

## 2. Latest deployed production baseline

Current tested deployment before this handover:

`DEPLOYED_SHA=6a7049a85639650ee136c20d9f9293a034a0fd05`

Render service:

- service: `joe-ccass-api`
- service id: `srv-dads94740ujc73cpdktg`
- region: Singapore
- plan: Free
- start command: `python -m uvicorn app.portal_8504:app --host 0.0.0.0 --port $PORT`
- health: `/health`

## 3. Production components already proven

Do not reopen these without regression evidence:

- Longbridge authentication: PASS
- MCP connect: PASS
- `broker_holding_detail`: PASS
- Longbridge response receive/decode: PASS
- parse: PASS
- validate: PASS
- normalize: PASS
- Turso persistence: PASS, but slow
- `prepared.response` can be present with Holdings
- `allow_external=False` has been observed
- live product build can complete
- bundle construction can complete

Latest representative real 06182 timing evidence from Render logs:

- broker_holding_detail path: ~1.46s
- static info: ~1.30s
- parse/validate: ~milliseconds
- Turso persist: ~18.27s
- Longbridge total: ~21.04s
- after the gateway eventually returns, normal report/bundle work is mostly very fast (milliseconds to ~1s)

## 4. Exact currently proven blocking defect

The latest source/runtime comparison proves an important branch bug in `app/services/ccass.py` at SHA `6a7049a...`:

The code only passes:

`include_optional_surfaces=False`

when the selected source is a cached/persisted Longbridge snapshot.

Fresh live Longbridge falls through the other branch and calls `_attach_related_surfaces(...)` without that argument, so the default remains:

`include_optional_surfaces=True`

The fresh current Holdings request therefore waits for `_attach_related_surfaces()` under a 20-second timeout even after the real Longbridge/Turso core is already complete.

Production timing confirms this:

- `LB_REQUEST_END`: 2026-09-09T10:44:30.539Z
- `PREPARE_POST_GATEWAY_START`: 2026-09-09T10:44:50.541Z

Gap: approximately 20.0 seconds.

That matches the secondary-surfaces `asyncio.wait_for(... timeout=20.0)` budget.

This is why the full request reaches roughly 43–45 seconds and then fails at/near the portal/Render deadline.

## 5. Current request failure

Warm service verification already proved cold start is not the main blocker:

- healthcheck: 200
- warm 06182 request: `HTTP 504`
- elapsed: `45s`
- state: `PORTAL_REQUEST_TIMEOUT`

The portal route currently has a 45-second application deadline.

Observed Render/proxy cutoff has also been around ~43.5–45 seconds, so deadline ordering remains defective.

However, do not start by changing timeout values. First remove the proven unnecessary 20-second fresh-Longbridge secondary wait.

## 6. Earliest root cause and next minimal fix

Earliest proven root cause now:

**Fresh live Longbridge current Holdings incorrectly re-enters `_attach_related_surfaces()` with `include_optional_surfaces=True`.**

Minimal fix target:

For current Longbridge Holdings, whether fresh or persisted fallback, optional surfaces must not block the synchronous core response.

Expected current path:

`Longbridge -> validate -> normalize -> persist Turso -> core Holdings/required derived core -> return 8504`

Optional/specialized work must not block this path:

- announcements
- Stock Events
- Capital Information
- Officers
- Price History enrichment
- Webb historical/specialized work
- AI/research hydration
- downloads/reports

Do not remove those capabilities; only keep them off the synchronous current Holdings critical path.

## 7. Acceptance immediately after the minimal fix

Run one warm real production test for `06182` after deploy.

Required:

- source = Longbridge
- Holdings rows > 0
- Turso persisted = yes
- no secondary 20s wait after Longbridge core
- `prepared.response` present
- `allow_external=False`
- bundle completes
- route returns
- HTTP 200 or explicit application terminal response
- no proxy 502 / portal 504
- target <=60s; hard <=90s

Expected if the proven 20s delay is removed: roughly low-to-mid 20 seconds based on current real timings, subject to Turso variance.

Only after this passes, run regression on prior real-success surfaces:

- 00003 Holdings
- RCT1 / RCT5 / RCT20 / RCT60
- Broker History

Then continue P0 downstream:

- current Concentration production gate
- second distinct real snapshot
- Changes
- Big Changes
- Concentration History
- reload/restart persistence regression

## 8. Turso performance note

Turso is not currently a failure; persistence succeeds.

But ~18–20 seconds is a material performance concern.

The newer Turso reference explicitly warns to determine whether writes are row-by-row remote round trips and to batch inserts if so.

Do not optimize this before the current proven fresh-Longbridge secondary wait is removed and production is retested.

## 9. Governance

Always:

`Reference -> Current -> Gap -> Earliest Root Cause -> Minimal Fix -> Runtime Verify`

Fail Loud, Never Fake.

Do not relabel previously real production PASS components as unfinished; architecture changes require regression verification only.

Do not return to a micro-patch relay loop. Once an exact root cause is proven, fix it and rerun the same production gate.

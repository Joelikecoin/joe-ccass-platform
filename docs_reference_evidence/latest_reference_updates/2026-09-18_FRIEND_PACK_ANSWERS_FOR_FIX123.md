# FRIEND PACK ANSWERS FOR FIX-1/2/3 (0.5) — evidence digest

> **Date:** 2026-09-18 (company machine)
> **Source:** `CCASS_Codex_Handover_20260814.zip` (authoritative pack, `latest_reference_updates/`)
> **Extracted at (company machine, workspace root, outside repo):** `../friend_pack/webbsite-ccass-tool/`
> **Purpose:** store the pack-verified answers that scope the 0.5 fixes, so the next session starts from evidence, not memory.
> **Governance:** Reference → Current → Gap. Concepts verified here are design references only — build natively, never a code crutch (§6). fundamentals depth / unified event layer / evidence cache do NOT exist in the pack and must be built from zero.

## FIX-2 — dynamic announcement-PDF text extraction ✅ pack has a full working answer

`utils/hkex_announcement_pdf.py` (pack):

- Fetch + extract **HKEX announcement PDF text**, used by both its FastAPI route and MCP tool.
- **Host allow-list**: `www1.hkexnews.hk`, `www.hkexnews.hk`, `hkexnews.hk` only (SSRF-safe; returns structured error payload on violation).
- Parser: **PyMuPDF (fitz)** `>=1.24` — our repo ships `pypdf`; either works, pypdf is already wired.
- Structured errors via `utils/errors.structured_error` (fail-loud, same discipline as ours).
- Local disk cache under `data/hkex_announcement_pdf_cache/`; char caps `DEFAULT_MAX_CHARS=50_000`, `MAX_MAX_CHARS=500_000`; default timeout 20 s.

→ **Our FIX-2 plan:** reuse the concept (host allow-list + structured errors + cache + char caps) on our existing `pypdf` stack; feed `document_entities` extraction from allotment-results/circulars discovered dynamically.

## FIX-1 — dynamic discovery of annual/interim report documents ⚠️ pack has half the answer

The pack has **no fundamentals service** (confirmed again 2026-09-18; see V3 §5.3). But it proves the discovery half:

- `api.py:793` — title classifier: `("results_announcement", r"業績|年報|中期報告|annual result|interim result|final result")` — dynamically recognizing results/annual/interim documents from announcement titles.
- `utils/hkexnews.py::fetch_announcements` — the same HKEXnews titlesearch servlet we already use (`resolve_hkex_stock` → `stockId` → search), `row_range=100`, date window `365 * period_years`.
- Raw reference assets also shipped: `hkex_titlesearch.js/.html`, `hkex_search.js`, `hkex_config_c.js`.

→ **Our FIX-1 plan (build, don't copy):** announcements search (already dynamic in our repo) → title-category filter for annual/interim reports → PDF fetch (FIX-2 layer) → **new** PDF parsers for Revenue / NAV / Debt / Receivables / OCF / Auditor / Going-concern. The parser half has no pack reference — that is our differentiator (V3 §5.3).

## FIX-3 — free-container capacity ⚠️ pack's answer is "cap it"; ours must be "chunk + async + accumulate"

- `api.py:2659` — `period_years: int = Query(1, ge=1, le=2)` — announcements **hard-capped at 2 years** (`utils/hkexnews.py`: `from_day = today - timedelta(days=365 * period_years)`).
- Yahoo price lookback: default 1095 days, max 3650 (`api.py:2638`).

→ The friend hit the same wall and capped around it; our 2026-09-18 gate measurements agree (2y = safe: 236 rows/41.9s; 5y single payload = OOM crash). Our 5-year product target needs our own mechanism, already field-proven today:
1. **Windowed chunking** — DI 6-month windows: 4/4 succeeded (94–105 s each, zero warnings) on the free container.
2. **Async job pattern** — the DI job infra (`POST /admin/disclosure-interests/job`) is the template for announcements/timeline 5-year pulls.
3. **Structured Evidence Cache** — persist once, never re-derive (V3 §2 storage layer C); accumulation replaces monolithic fetches.
4. Zero-budget scheduling option (from the pack's own repo pattern, V3 §8.0): GitHub Actions scheduled workflows — no 60 s edge, 2 GB RAM.

## Gate context this digest feeds (V3 §7 0.4/0.5)

- 0.4 run on 02318: 14 PASS / 3 FAIL (FUNDAMENTALS, INTERMEDIARIES, WHITEWASH_CONCERT — all from the two hardcoded whitelists `HKEX_FUNDAMENTAL_DOCUMENTS` + `DOCUMENT_ENTITY_SPECS`) / middle gap DEFERRED by design.
- 0.5 order: FIX-1 (dynamic fundamentals discovery → delete `HKEX_FUNDAMENTAL_DOCUMENTS`), FIX-2 (dynamic entity discovery feeding `DOCUMENT_ENTITY_SPECS`), FIX-3 (chunk/async heavy pulls), then re-run the gate on a fresh unseen code → target 18/18.

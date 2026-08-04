# RW-004 Documented Architecture Alignment Review

## 1. Evidence Basis

This review uses only the documented evidence available in the workspace:

- `docs_reference_evidence/04_Evidence_Index/REFERENCE_EVIDENCE.md`
- `docs_reference_evidence/04_Evidence_Index/ND-01_REALITY_GAP_REVIEW.md`
- `docs_reference_evidence/04_Evidence_Index/ND-02_FINAL_REVIEW.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_SPEC.md`
- `app/api.py`
- `app/mcp_server.py`
- `app/services/ccass.py`
- `app/sources/registry.py`
- `ccass_core/collector.py`
- `ccass_core/report.py`

The requested `FRIEND_WEBSITE_REPLICATION_MATRIX.md` was not directly accessible in the workspace. Where the friend-side documented architecture depends on that missing file, the result is explicitly marked Unconfirmed.

## 2. Architecture Comparison Table

| Area | Friend Evidence | Joe Status | Classification |
|---|---|---|---|
| Data Source Architecture | Friend reference evidence documents a multi-source ownership matrix with SDW/local DB-first routing where available, Yahoo Finance and HKEXnews promotions where supported, and Webb-site progressively reduced to fallback or remaining single-source paths. It also records `source` and `data_as_of` as important provenance metadata. | Joe documents a layered source architecture and fallback concept, but the current implementation source registry still centers on Webb-site and Google Drive CSV. The code and services preserve provenance metadata, but not the full friend-style source ownership matrix. | Alignment Required |
| MCP / API Structure | Friend evidence describes structured API/MCP consumers with top-level provenance fields and a `/api/stock`-style schema note. The exact tool list and contract details are not fully recoverable without the missing replication matrix and original friend materials. | Joe exposes FastAPI report/holdings/changes/big-changes/concentration routes and one MCP tool (`get_ccass_stock_data`). The API returns structured models and report text, but the MCP surface is narrower than the documented friend architecture. | Alignment Required |
| Tool Responsibility | Friend architecture documents a separation across collector, parser, normalizer, storage, analysis/report, and AI consumer layers. | Joe has partial separation across source adapters, services, collector, storage, compute, and report layers, but the current codebase does not expose the same breadth of documented source responsibilities or a dedicated AI consumer layer. | Alignment Required |
| Backend Workflow | Friend documentation describes a fetch → parse → normalize → store → process → output flow with structured provenance and persistent historical storage. | Joe follows the same general pipeline shape in the current implementation: source fetch through services, normalization, historical storage, analysis, and report/output rendering. However, the friend-style workflow is broader in scope and source coverage than Joe’s current concrete source set. | Completed |

## 3. Gap Analysis

- The clearest architectural gap is data-source breadth. Friend documentation shows a multi-source ownership matrix and a source diversification strategy; Joe currently implements only a smaller active source set.
- Joe’s workflow shape is directionally aligned with the friend architecture: source adapters feed services, services feed analysis/report layers, and both API and Streamlit consume the shared outputs.
- MCP coverage is materially narrower in Joe. The friend documentation implies a richer documented consumer surface, while Joe currently exposes a single MCP tool.
- Tool separation is present in Joe, but not to the same documented granularity as the friend architecture. In particular, the dedicated AI consumer layer described in the friend docs is not implemented as a distinct Joe surface.
- The backend pipeline is conceptually aligned, but the friend documents describe a more complete source-neutral architecture with stronger collector/storage formalization than the current Joe implementation evidence shows.

## 4. Recommendation

- Alignment Required for the source architecture, because Joe still lacks the documented breadth of source ownership and fallback relationships.
- Alignment Required for MCP/API structure, because Joe’s current MCP surface is smaller than the documented friend consumer model.
- Alignment Required for tool responsibility separation, because Joe only partially matches the documented collector/parser/normalizer/storage/analysis/AI split.
- Completed for the high-level backend workflow shape, because Joe already follows the same broad fetch/process/output pattern.

## 5. Unconfirmed Items

- The exact content of `FRIEND_WEBSITE_REPLICATION_MATRIX.md`.
- The exact friend-side tool list beyond what is recorded in `REFERENCE_EVIDENCE.md`.
- The exact friend API payload shape for every endpoint and every consumer.
- The exact friend-side internal storage technology and how each source ultimately lands in persistent storage.
- Any friend-side architecture detail not explicitly preserved in the accessible documentation.

## Governance Verification

Confirmed:

- No code changed
- No tests changed
- No requirements promoted
- Friend documents remain evidence/reference


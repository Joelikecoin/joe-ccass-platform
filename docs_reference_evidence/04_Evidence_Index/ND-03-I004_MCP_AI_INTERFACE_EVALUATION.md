# ND-03-I004 MCP / AI Consumer Interface Evaluation

## 1. Executive Summary

Joe Platform is already substantially AI-ready at the API and report layer, but it does not yet expose a dedicated MCP / AI-consumer interface.

The current repository already provides:

- structured FastAPI endpoints
- JSON response models with provenance fields
- `data_as_of` aliases
- structured warnings and data-quality messages
- historical snapshot access for holdings-style analysis
- Markdown report generation for direct downstream use

That makes an MCP or AI consumer layer feasible in principle. However, a dedicated interface would still need clear tool boundaries, consumer-safe contracts, and explicit security design before it should be implemented.

Recommendation:

- future MCP / AI consumer interface: Recommended for Future Implementation
- direct reproduction of friend MCP tools: not appropriate without separate approval

## 2. Current AI-ready Capability Assessment

| Capability | Status | Notes |
| --- | --- | --- |
| FastAPI endpoints | Available | The platform already exposes structured API endpoints for holdings, changes, big changes, concentration, and report variants. |
| Structured reports | Available | Markdown and JSON report outputs already exist and are used by the current Streamlit and API surfaces. |
| Metadata contract | Available | Response models already carry source metadata, fetched-at timing, source URL/name, and canonical dates. |
| Source provenance | Available | Source identity, parser/schema details, and provenance fields are preserved through the model layer and history layer. |
| `data_as_of` | Available | The platform exposes `data_as_of` as a computed alias on relevant models. |
| Warnings / data-quality notes | Available | Structured warnings are already part of the product and API contract. |
| Historical data access | Partially Available | Snapshot storage and exact-date/history queries exist, but the platform does not yet expose a generic historical AI query layer. |
| Dedicated MCP / AI tool boundary | Missing | No MCP tool layer exists today. |
| AI reasoning / agent orchestration logic | Missing | The repository intentionally avoids embedding AI reasoning or judgement logic. |
| Consumer-specific access policy | Partially Available | API key verification exists for HTTP endpoints, but MCP-specific permissions and scoping are not defined. |

## 3. MCP Capability Evaluation

A future MCP layer is technically feasible because the current API and data models already provide the kind of structured payloads MCP tools would typically wrap.

Possible tool boundaries:

- `get_ccass_stock_data`: could map to the holdings endpoint and return the latest structured holdings snapshot plus provenance.
- `get_ccass_diff`: could map to the existing changes/big-changes style comparison endpoints.
- `search_participant_holdings`: could be built only if a clear participant-search contract is defined on top of the current holdings data.
- `get_stock_events`: would require a separate event model or an approved event source; it is not currently supported by the repository surface.

Required data contracts:

- normalized stock identity
- source identifier and source name
- `data_as_of`
- fetched-at / snapshot timing
- warning list or quality flags
- history boundary or comparison dates where relevant
- clear “read-only” semantics

Authentication / security considerations:

- the current HTTP API already uses API-key verification when configured
- MCP consumers would need an equivalent or stricter auth model
- tool access should be read-only by default
- tool boundaries should prevent hidden investment advice, trading action, or unreviewed source routing
- if MCP is externalized, rate limits, audit logs, and prompt-injection-safe output rules should be part of the design

Maintenance complexity:

- moderate for a thin wrapper over the current API
- high if MCP tool semantics diverge from the existing API contract or introduce new data-shaping rules

## 4. AI Consumer Use Case Evaluation

Potential future consumers:

- ChatGPT
- Claude
- internal AI agents
- research assistants

For these consumers, the main requirement is not “more intelligence in the backend,” but a cleaner, safer data contract.

Required output format:

- structured JSON for machine use
- Markdown for human-readable summaries
- explicit provenance fields
- explicit warnings and limitations
- stable field names across requests

Data completeness requirements:

- consumers need to know when data is unavailable, partial, cached, or stale
- snapshot-based analysis should remain honest about its time boundary
- consumer outputs should preserve source and `data_as_of` consistently

Reliability requirements:

- read-only responses
- deterministic schema
- explicit error messaging
- stable report sections for human verification
- no hidden dependence on mutable prompt behavior

Current fit:

- ChatGPT and research assistants can already consume the API/report outputs directly
- internal AI agents would benefit from a narrower tool surface
- Claude or similar consumers would benefit from the same structured payloads, but the platform does not yet provide a dedicated AI-consumer packaging layer

## 5. Architecture Impact

### FastAPI

Low to moderate impact.

The existing FastAPI service is already the right integration point for a future MCP wrapper. A thin MCP layer could sit on top of the existing route/service layer without changing core product logic.

### Existing API contracts

Low impact if MCP is implemented as a wrapper.

The safest path is to reuse existing response models and avoid inventing duplicate payloads. If new tool-specific schemas are introduced, they should be thin projections of the existing contract rather than a parallel model system.

### Data models

Low to moderate impact.

Current models already carry the most important AI-facing fields. A future MCP layer should reuse:

- source metadata
- `data_as_of`
- warnings
- history/comparison dates

Only genuinely MCP-specific metadata should be added, and only if it cannot be expressed safely through the existing models.

### Metadata schema

Low impact.

The current provenance contract is already a good baseline for AI consumers. The main requirement is to preserve the existing semantics rather than widen the schema unnecessarily.

### Security

Moderate impact.

This is the most important gap. The existing API-key mechanism is sufficient for the HTTP API, but an MCP interface would still need:

- explicit access control
- tool-level permissions
- auditability
- rate limiting
- safe output policy

Without that, an AI consumer layer could accidentally become a broad data-exposure surface.

## 6. Feasibility Assessment

Feasible, but only as a future controlled addition.

Recommended approach:

1. Reuse the current API and data models as the source of truth.
2. Define a small set of read-only MCP tools.
3. Keep tool outputs tightly aligned with existing response schemas.
4. Require provenance and warning fields on every tool result.
5. Add security and audit controls before any external AI integration.

Major dependencies:

- a stable, approved tool boundary
- API/auth policy for non-human consumers
- read-only schema design
- safe mapping from existing endpoints to MCP semantics
- validation that no tool leaks investment judgement or trading capability

Risks:

- tool proliferation without a clear boundary
- duplicated schemas that drift away from the current API contract
- consumers over-trusting a tool result without checking warnings or `data_as_of`
- security gaps if AI access is added without a proper permission model

Estimated complexity level:

- Moderate for a thin wrapper
- High for a fully productized MCP platform with governance, logging, and consumer management

## 7. Recommendation

Recommended for Future Implementation

Reasoning:

- the platform already has the core machine-readable data contract
- the strongest missing piece is not data, but interface definition and security
- a read-only MCP layer could add value for ChatGPT, Claude, and internal agents without changing the underlying product logic
- the implementation should remain a thin, governed wrapper over existing capabilities rather than a separate AI reasoning system

## 8. Unconfirmed Items

- exact tool boundary expected for MCP usage
- whether external AI consumers need separate authentication from the HTTP API
- whether event-style tools such as `get_stock_events` are actually needed or only reference examples
- whether participant search should be a true new capability or just a filtered view of holdings
- whether AI consumers need streaming outputs, tool-chaining support, or only static responses
- whether audit/log retention requirements exist for AI consumer access

## 9. Open Questions

1. Should the first MCP scope be holdings-only, comparison-only, or report-only?
2. Do AI consumers need direct access to JSON models, Markdown reports, or both?
3. What authentication model should govern AI tool access?
4. Should MCP responses be identical to existing API responses, or a smaller AI-friendly projection?
5. Are there any AI-consumer use cases that require search or event tools beyond the current report contract?
6. What is the acceptable audit/logging standard for AI tool usage?

## Governance Verification

- No code changed
- No tests changed
- No MCP implemented
- No AI analysis implemented
- No new data source added
- Friend evidence remains Reference Only


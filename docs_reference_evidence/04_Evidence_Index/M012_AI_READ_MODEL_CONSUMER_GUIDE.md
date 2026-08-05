# M012-02 AI Read Model Consumer Guide

## 1. Objective

Define how API consumers, MCP consumers, and future downstream agents should read and interpret `AI Read Model v0.1` without changing the model shape, API response contract, MCP contract, or storage layer.

This guide is consumer-facing only. It does not add fields, does not widen the contract, and does not introduce new analysis logic.

## 2. Consumer Usage Guidance

Use the read model in this order:

1. `identity` to confirm the stock identity being described.
2. `timing` to understand when the data was fetched and which `data_as_of` date it reflects.
3. `provenance` to understand where the model was sourced from and whether it came from a primary or fallback path.
4. `quality` to decide whether the result is fresh, cached, stale, partial, or unavailable.
5. `history` to understand whether a previous snapshot exists and whether comparison context is present.
6. `context` to understand which related surfaces are available as supporting information.
7. `payload` to access the underlying data objects.
8. `contract_meta` to identify the version and the named surface for routing / consumer bookkeeping.

Consumers should treat the model as a read-only product surface. It is a structured description of what the platform knows, not a decision engine.

## 3. Contract Block Interpretation

| Block | What it is for | Consumer interpretation |
|---|---|---|
| `identity` | Stock identity and market context | Use this first to verify the instrument. Do not infer any analytical meaning from it. |
| `timing` | `data_as_of`, `fetched_at`, `generated_at` | Use this to assess recency and freshness. `generated_at` is the read-model assembly time, not the source date. |
| `provenance` | Source name, source type, primary/fallback state | Use this to understand where the result came from. Primary/fallback is a source-path label, not a quality judgment by itself. |
| `quality` | Freshness status, warnings, and error state | Use this as the trust and availability layer. It is the first place to check before reusing payload content. |
| `history` | Snapshot identity and comparison context | Use this when you need snapshot continuity or previous-snapshot awareness. Absence of comparison context means no historical comparison should be assumed. |
| `context` | Related surfaces and supporting references | Use this as a map of adjacent surfaces. It is supporting information, not the primary data payload. |
| `payload` | The underlying data objects | Use this when you need the actual structured data. It is the consumer data plane. |
| `contract_meta` | Version and named surface | Use this for routing, compatibility checks, and tool bookkeeping only. |

## 4. Payload, Context, and Quality Semantics

The three most important separation rules are:

- `payload` is the data consumer plane.
- `context` is supporting information that points to related surfaces.
- `quality` is trust / freshness / availability information.

Do not use `context` as a substitute for payload data.
Do not use `payload` without checking `quality`.
Do not treat a populated payload as automatically fresh or complete.

## 5. Warning, Freshness, and Fallback Interpretation

Warnings are part of the contract and should be read as structured operational signals.

- `fresh` usually means the current source response is the primary live result.
- `cached` usually means a fallback or cached snapshot path was used.
- `stale` means the data is older than the preferred freshness threshold but is still intentionally surfaced as a known stale result.
- `partial` means the result is available but incomplete or reduced in confidence.
- `unavailable` means the source or required component could not be served for this request.

Fallback state is not the same as failure state.

- A fallback result can still be valid and useful.
- A warning does not automatically invalidate the entire model.
- An `unavailable` error state means the consumer should not assume payload data exists.

Future consumers should prefer the structured status fields over ad hoc string parsing when both are available.

## 6. API / MCP / Downstream Agent Guidance

API consumers and MCP consumers should expect the same contract shape.

Future downstream agents should:

- check `quality` before using `payload`
- use `history` only as comparison context, not as a second source of truth
- treat `context` as supporting references, not independent analysis
- respect `contract_meta.version` before assuming compatibility

If a consumer only needs routing or bookkeeping, `contract_meta` is sufficient.
If a consumer needs data, `payload` is the relevant block.
If a consumer needs trust / freshness judgment, `quality` is the relevant block.

## 7. Out of Scope

This guidance does not:

- add new fields
- redefine the AI read model schema
- change API or MCP contracts
- add new sources
- add AI investment logic
- add trading signal or recommendation logic

## 8. Practical Consumer Rule

When in doubt:

1. trust `quality` first,
2. then inspect `provenance`,
3. then inspect `timing`,
4. then consume `payload`,
5. and only then use `context` or `history` for supporting interpretation.

That keeps API, MCP, and downstream agents aligned on the same read-only contract semantics.

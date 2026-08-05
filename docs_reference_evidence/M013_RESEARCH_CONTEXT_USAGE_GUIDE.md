# M013-03 Research Context Usage Guide

## 1. Purpose

`ResearchContextPackage` is a consumer-facing packaging layer for existing platform data.

Its purpose is to:

- organize existing platform data into a structured research context package,
- provide consumer-friendly context for downstream consumers, and
- support future AI consumption without changing the underlying read model contract.

This guide is intentionally not an investment conclusion, not a decision engine, and not an AI analysis layer.

The package helps consumers understand what the platform knows, but it does not tell the consumer what to buy, sell, score, or recommend.

## 2. Package Overview

`ResearchContextPackage` groups the existing platform surfaces into a stable, readable package:

- `identity`
- `ownership_context`
- `market_context`
- `company_context`
- `historical_context`
- `quality_context`
- `contract_meta`

The package is additive in usage only. It organizes existing data for consumption, but it does not redefine the AI Read Model v0.1, the API contract, the MCP contract, schema, storage, or source strategy.

## 3. Context Block Explanation

### `identity`

`identity` describes the research subject.

It is used to confirm the stock being discussed.

It does not contain valuation, ranking, judgment, or recommendation.

### `ownership_context`

`ownership_context` groups ownership-related information such as holdings, changes, and concentration.

It is useful for understanding the current ownership picture and the surrounding ownership context.

It does not mean the platform is making an accumulation / distribution judgment.

### `market_context`

`market_context` groups market-related context such as price history availability and related market surface information.

It helps consumers understand whether price history is present and how it relates to the research package.

It does not imply trend prediction, price signal generation, or market recommendation.

### `company_context`

`company_context` groups company-related surfaces such as announcements, officers, stock events, and capital information.

It helps consumers see the surrounding company context in one place.

It does not assign a company quality rating or interpret the company as good or bad.

### `historical_context`

`historical_context` contains existing historical context and snapshot information.

It helps consumers understand current / previous snapshot relationships and any available historical context already present in the platform.

It does not re-define M007 historical analysis scope, semantics, or boundaries.

### `quality_context`

`quality_context` carries provenance, freshness, warnings, and availability-related interpretation.

It helps consumers decide how much trust or caution to apply when reading the package.

It does not convert a warning into an investment conclusion.

### `contract_meta`

`contract_meta` carries package version and surface information.

It helps consumers identify the package version and route it correctly.

It is for compatibility and bookkeeping only.

## 4. Consumer Workflow

The recommended workflow is:

1. User selects a stock.
2. The platform builds a `ResearchContextPackage`.
3. The consumer reads the structured context package.
4. A future analysis layer outside the current scope may use the package if needed.

The consumer should treat the package as a structured context package, not as a decision engine.

## 5. Data Quality Interpretation

Consumers should interpret the following carefully:

- `source`
- `freshness`
- `warnings`
- `unavailable` state

These values describe data state, provenance, and availability.

They must not be misread as investment conclusions.

When the package is incomplete, stale, or unavailable, consumers should treat that as a context signal, not as a recommendation or signal to trade.

## 6. Usage Limitations

Consumers can use the package to:

- organize data,
- expose context, and
- preserve metadata.

Consumers must not use the package to:

- make investment decisions,
- generate trading signals,
- predict price movement,
- produce a recommendation, or
- replace analysis with inference.

## 7. Out of Scope

This guide does not:

- add new fields,
- change the AI Read Model v0.1,
- change the API contract,
- change the MCP contract,
- change schema or storage,
- add new data sources,
- add AI analysis logic,
- add stock scoring,
- add buy / sell recommendation logic, or
- add trading signal generation.

In short: no investment logic, no trading signal, and no recommendation.

## 8. Practical Consumer Rule

When in doubt:

1. inspect `quality_context`,
2. inspect `identity`,
3. inspect `ownership_context`, `market_context`, `company_context`, and `historical_context`,
4. then use `contract_meta` for version / routing checks.

That keeps consumers aligned on the same read-only package semantics.

The package is for context organization only and should never be treated as a substitute for analysis.

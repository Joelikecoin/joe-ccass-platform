# Reference Evidence Index

This document is documentation/evidence preservation only.

It records newly obtained friend/reference-system evidence for later review. It does not promote any evidence into mandatory requirements, approved implementation, or current Joe Platform architecture.

## Preservation Rules

- Keep all existing Reference Evidence records additive and intact.
- Do not modify the five original source documents.
- Do not modify `docs/PROJECT_SPEC.md`.
- Do not modify `docs/REFERENCE_SPEC.md`.
- Do not modify application code, tests, or data-source routing.
- Do not infer unconfirmed implementation details.

## RE-009 — Friend MCP Data Source Ownership Matrix

Source Type:
Direct information supplied by the reference-system owner through Joe.

Classification:
Current/Historical Reference Implementation Evidence

Matrix:

| Tool | Primary | Fallback / Remaining Webb-site Dependency |
|---|---|---|
| get_ccass_stock_data | SDW / local DB first | Big changes, concentration and some historical data may still use Webb-site fallback |
| get_webbsite_price_history | Yahoo Finance | Webb-site / local cached price fallback |
| get_hkex_announcements | HKEXnews | No Webb-site required |
| get_stock_events | Webb-site only | No non-Webb replacement currently identified |
| get_stock_officers | 同花順 F10 managers primary | Webb-site officers historical fallback |
| get_stock_capital | 同花順 F10 | No Webb-site required |
| screen_stocks | SDW / local DB first | Same fallback strategy as get_ccass_stock_data |
| search_participant_holdings | SDW / local DB first | Same fallback strategy as get_ccass_stock_data |
| get_ccass_diff | Webb-site only | No non-Webb replacement currently identified |

Reported implementation changes:

- Alternative sources were promoted to primary where available:
  - Yahoo Finance
  - HKEXnews
  - 同花順 F10
  - SDW / local DB
- Webb-site was downgraded to fallback where alternatives exist.
- Some capabilities remain Webb-site-only.
- MCP tool responses reportedly include top-level:
  - `data_as_of`
  - `source`
- `/api/stock` OpenAPI response schema reportedly includes:
  - `ok`
  - `data_as_of`
  - `source`
- No HKEX SDW scraper was reportedly implemented in that reference-system change.

Important:
Do not infer how SDW data enters the friend's local database unless separately evidenced.

## Evidence Interpretation

This evidence supports a reference architecture pattern of:

Multiple approved/public sources
→ source-specific collectors/data access
→ local/persistent data
→ structured API/MCP
→ UI/AI consumers

with Webb-site progressively reduced from a critical dependency to a fallback or remaining single source for specific datasets.

This is Reference Architecture Evidence only.

It does not automatically require Joe Platform to reproduce every friend tool, source choice, or fallback rule.

## Provenance Metadata Evidence

Record `source` and `data_as_of` as valuable reference-system provenance metadata.

Before any future implementation, compare them against Joe Platform's existing:

- metadata schema
- source metadata
- snapshot date/as-of fields
- warnings/data-quality contract

Do not create duplicate fields in this task.

## External References

Record these URLs as Reference/Supporting Evidence only.

- 同花順: <https://q.10jqka.com.cn/hk/>
- Webb-site: <https://webbsite.0xmd.com/dbpub/>
- HKEX crawler reference: <https://github.com/SteamerLee/WebCrawler-HKEX>
- HKEX announcements service reference: <https://apify.com/nexgendata/hkex-news-announcements>

These URLs are externally provided references only. They were not fetched in this task and do not become approved Joe Platform dependencies automatically.

## Screenshot Evidence Preservation

Suggested archive filenames:

- `custom_gpt_openapi_api_evidence`
- `custom_gpt_api_usage_evidence`
- `webbsite_cloudflare_evidence`

Status:

The original screenshot image files were not accessible from the repository/runtime at the time of this task. No placeholder images were created. The screenshots are treated as externally held by Joe and require later archival into `docs_reference_evidence/02_Friend_Architecture/` when the files become available.

## Friend Architecture Investigation Status

Status:
CLOSED — Sufficient Reference Evidence Collected

Reason:

Enough evidence now exists to proceed with Joe Platform architecture and data-foundation work without requesting further internal implementation details from the reference-system owner.

No further:

- friend questioning
- F12 investigation
- private architecture discovery

is required for current planning.

Future evidence may be added only if voluntarily supplied or materially necessary.

## Remaining Unconfirmed Items

Keep these explicitly Unconfirmed where evidence is insufficient:

- Exact mechanism by which the friend's SDW data reaches local DB
- Exact current persistent database technology
- Exact implementation of remaining Webb-site fallback paths
- Exact DT Rainbow data-generation architecture
- Whether every historical design statement remains identical in current production

Do not infer answers.

## Governance Verification

- Five original source documents unchanged.
- `docs/PROJECT_SPEC.md` unchanged.
- `docs/REFERENCE_SPEC.md` unchanged.
- No source requirements promoted to Mandatory.
- No implementation code changed.

## Notes

This file is intentionally additive. It preserves the newly supplied evidence for later ND-02 review and does not overwrite or reinterpret the original source material.

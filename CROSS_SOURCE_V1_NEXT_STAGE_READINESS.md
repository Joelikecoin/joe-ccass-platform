# CROSS_SOURCE_V1_NEXT_STAGE_READINESS

This is a readiness package only. It does not execute empirical research or add features.

## Real-stock validation checklist

1. Use an authorized production API key from the existing `secrets.API_KEY` reference.
2. Select one real CCASS participant ID with holdings on at least two securities.
3. Select one real normalized HKEX event with source document lineage.
4. Query the same security across timeline and sequence windows.
5. Query interval in calendar mode; use trading mode only if the holiday calendar is verified.
6. Compare two fingerprints with explicit lineage and include an unknown field.
7. Drill from every returned record to source_id, source_date, source-native identifier and evidence reference.
8. Record HTTP status, schema validation, evidence state and row counts without exposing secrets.

## Required inputs

- `X-API-Key` or approved bearer credential (provided only by the authorized runtime)
- Real `entity_id`, `security_id`, event date range and event type sequence
- Existing source-native participant/security/event identifiers
- Read-only Turso connection through `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`

## Expected Cross-Source outputs

- Entity search: explicit relationships only; same names do not merge; participant is not beneficial owner.
- Timeline: normalized events sorted by point-in-time date with duplicate IDs reported.
- Sequence: matched event IDs, missing predicates and SUPPORT/CONTRADICTION/UNKNOWN state.
- Interval: calendar result; trading result only when calendar is reliable, otherwise UNKNOWN/PARTIAL.
- Fingerprint: matched, unmatched, unknown fields and RESEARCH_PRIOR label; never a prediction.
- Evidence: source and lineage fields preserved on every derived result.
- Missing data: UNKNOWN/PARTIAL, never zero or fabricated values.

## Acceptance rules

- All route responses are HTTP success and schema-valid under authentication.
- Production DB contains `cross_source_records` with idempotent canonical records readable after restart.
- Source lineage and point-in-time fields are present on read-back.
- No row-level source stitching, interpolation or beneficial-owner inference occurs.
- Ownership-derived fields remain UNKNOWN when issued-share denominator is unavailable.

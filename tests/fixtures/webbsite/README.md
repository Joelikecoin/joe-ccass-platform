# Webb-site parser fixtures

These files are synthetic, reduced HTML fixtures for deterministic offline tests.
They preserve only the known table labels and identity fields needed by the parser.
They contain no live production figures, credentials, cookies, tokens, or private data.

- `holdings_normal.html`: valid latest Holdings shape with deliberately unsorted rows.
- `holdings_missing_table.html`: identity and summary are present, but Holdings is absent.
- `holdings_malformed.html`: Holdings contains a malformed numeric value.
- `holdings_identity_mismatch.html`: the returned stock identity differs from the request.

# Cross-Source V1 production acceptance — 2026-09-23

Result: FAIL (data/lineage acceptance), not a credential or Render access blocker.

The bounded verifier ran in the existing Render Docker service using its existing
API_KEY, TURSO_DATABASE_URL and TURSO_AUTH_TOKEN. No credential values were returned,
stored in this repository, or emitted by the verifier. No service, paid resource,
environment-variable change, branch-setting change, synthetic data, or destructive
database operation was used. The temporary Docker startup hook is removed.
The standalone script remains available for a future authorized runtime audit.

## Runtime evidence

- Audit revision: fed38f85570d316b9ea37544235e126fcde932f3.
- Render deployment: dep-dapmsum7bikc73833c30 (live).
- All three required runtime credentials are present; direct Turso SELECT succeeds.
- Six authenticated public API requests return HTTP 200: entity search, timeline,
  sequence, interval, fingerprint and concentration evidence. Unauthenticated
  interval requests return 401. HTTP success does not establish data acceptance.
- Public and loopback entity/timeline/sequence/evidence responses agree.
- Real Longbridge snapshot: 06182, 2026-09-17, 103 participant holdings. Evidence
  participant IDs, shares and total agree with direct production DB read-back.
- Snapshot source/provenance relationship and checksum format pass. This confirms
  persisted provenance metadata, not a new download/hash of the upstream artifact.
- Interval and fingerprint results match expectations from the real snapshot.

## Failed acceptance gates

- The first audit found no cross_source_records table before API reads. The
  existing API repository constructor creates it with CREATE TABLE IF NOT EXISTS.
  The second audit confirms its schema exists but it contains ZERO canonical rows,
  before and after all requests. No backfill or sample insertion was performed.
- No canonical entity, security, relationship or event can be read back. Empty
  repeated reads agree but do not prove nonempty persistence correctness.
- Entity, timeline and sequence return no real matches. Sequence was exercised
  with an UNCLASSIFIED predicate because no canonical event exists; it is not a
  real-event sequence acceptance pass.
- Cross-Source evidence lineage cannot be drilled down. Concentration evidence
  passes independently and must not be substituted for Cross-Source lineage.

## Implementation bottlenecks found by source inspection

1. adapt_ccass_response exists but has no ingestion call site. Production source
   snapshots have not been projected/backfilled into the canonical table.
2. Both source adapters emit empty lineage (and securities empty source_mappings).
3. CrossSourceRepository.records uses dict(row), but _LibsqlRow does not provide
   a mapping protocol. A local reproduction against _LibsqlConnection confirms
   nonempty row conversion fails. Empty production results currently mask this.

These require implementation and a source-grounded, idempotent backfill before
another production acceptance run. Owner secret copying is not required.

## Validation and limits

Six focused local tests passed, including error-continuation and log redaction.
The final runtime audit completed 42 checks: 31 passed and 11 failed. The final
audit_finished marker is separate from those 42 checks. Full sanitized evidence
is in production-acceptance-2026-09-23.json.
An initial public timeline 502 during deployment handover resolved on the second
audit. Render log retrieval also had one transient failure and succeeded on retry.
The audit only changes startup behavior; application API/storage code is unchanged
from f7086d11bd7f011cded5cfa00b711d80b7012b78. Removing the startup hook restores
the original Docker command without changing that application behavior.

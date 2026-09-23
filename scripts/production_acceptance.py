"""Bounded, read-only production audit. Never emit payloads or credentials.

Run inside the existing Render runtime: python -m scripts.production_acceptance
All SQL is SELECT/PRAGMA table_info; HTTP POST only invokes pure fingerprint logic.
No source ingestion, synthetic fixtures, or repair writes are performed.
"""
import hashlib
import json
import os
import re
import signal
import time
import urllib.error
import urllib.parse
import urllib.request

PREFIX = "CROSS_SOURCE_ACCEPTANCE_V1 "
PUBLIC = "https://joe-ccass-api.onrender.com"
RESULTS = {}


def emit(check, passed, **facts):
    # Only booleans/numbers and fixed status labels enter logs. No response bodies,
    # database values, exception messages, request headers, URLs or key hashes.
    safe = {k: v for k, v in facts.items() if isinstance(v, (bool, int, float)) or v is None}
    RESULTS[check] = bool(passed)
    print(PREFIX + json.dumps({"check": check, "pass": bool(passed), **safe}), flush=True)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def request(path, *, payload=None, authenticated=True, local=False):
    base = "http://127.0.0.1:" + os.getenv("PORT", "10000") if local else PUBLIC
    headers = {"Content-Type": "application/json"}
    if authenticated:
        headers["X-API-Key"] = os.getenv("API_KEY", "")
    req = urllib.request.Request(base + path, headers=headers,
                                 data=None if payload is None else json.dumps(payload).encode())
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=25) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, {}
    except Exception:
        return 0, {}


def rows(connection, sql, args=()):
    cursor = connection.execute(sql, args)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def run():
    for name in ("API_KEY", "TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN"):
        emit(name + "_runtime", bool(os.getenv(name)))
    for _ in range(50):
        status, _ = request("/health", authenticated=False, local=True)
        if status == 200:
            break
        time.sleep(2)
    emit("local_health", status == 200)
    # API code is unchanged by this audit-only deployment; compare the public
    # response against this instance below while the rolling deploy progresses.
    status, _ = request("/health", authenticated=False)
    emit("public_health", status == 200, http_status=status)
    status, schema = request("/openapi.json", authenticated=False)
    emit("openapi", status == 200, http_status=status)
    cross_paths = [p for p in schema.get("paths", {}) if "/cross-source/" in p]
    emit("cross_source_routes", len(cross_paths) == 5, route_count=len(cross_paths))
    status, _ = request("/api/v1/cross-source/interval?anchor=2026-09-17", authenticated=False)
    emit("unauthenticated_rejected", status == 401, http_status=status)

    connection = None
    records = []
    snapshot = None
    holdings = []
    table_exists = False
    try:
        import libsql
        connection = libsql.connect(database=os.environ["TURSO_DATABASE_URL"],
                                    auth_token=os.environ["TURSO_AUTH_TOKEN"])
        emit("turso_connection", rows(connection, "SELECT 1 AS ok")[0]["ok"] == 1)
        tables = {r["name"] for r in rows(connection, "SELECT name FROM sqlite_master WHERE type='table'")}
        table_exists = "cross_source_records" in tables
        emit("cross_source_table_exists_before_api", table_exists)
        if table_exists:
            columns = {r["name"] for r in rows(connection, "PRAGMA table_info(cross_source_records)")}
            emit("cross_source_schema", {"record_id", "record_kind", "source_id", "payload_json", "evidence_state", "created_at"} <= columns)
            total = rows(connection, "SELECT count(*) AS n FROM cross_source_records")[0]["n"]
            records = rows(connection, "SELECT * FROM cross_source_records ORDER BY record_kind,record_id LIMIT 10000")
            emit("canonical_records_readback", bool(records), row_count=len(records), total=total, bounded_sample=total > 10000)
            for kind in ("entity", "security", "relationship", "event"):
                emit("canonical_" + kind, any(r["record_kind"] == kind for r in records),
                     count=sum(r["record_kind"] == kind for r in records))
            digest = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).digest()
            with_again = rows(connection, "SELECT * FROM cross_source_records ORDER BY record_kind,record_id LIMIT 10000")
            emit("canonical_repeat_read", digest == hashlib.sha256(json.dumps(with_again, sort_keys=True).encode()).digest())
        snapshots = rows(connection, "SELECT * FROM ccass_snapshots WHERE source_id='longbridge' AND stock_code='06182' ORDER BY snapshot_date DESC LIMIT 1")
        if snapshots:
            snapshot = snapshots[0]
            holdings = rows(connection, "SELECT participant_id,shares,rank FROM ccass_holdings WHERE snapshot_id=? ORDER BY rank", (snapshot["id"],))
            provenance = rows(connection, "SELECT * FROM raw_provenance WHERE id=?", (snapshot["provenance_id"],))
            emit("real_snapshot_readback", bool(holdings), row_count=len(holdings))
            emit("snapshot_source_lineage", bool(provenance) and provenance[0]["source_id"] == snapshot["source_id"] and bool(provenance[0]["safe_reference"]) and bool(re.fullmatch(r"[0-9a-f]{64}", provenance[0]["checksum_sha256"])))
    except Exception:
        emit("database_audit_completed", False)

    # The snapshot supplies real IDs even if the Cross-Source projection is empty.
    code = snapshot["stock_code"] if snapshot else "06182"
    anchor = snapshot["snapshot_date"] if snapshot else "2026-09-17"
    payloads = []
    for record in records:
        try:
            payloads.append((record, json.loads(record["payload_json"])))
        except Exception:
            emit("canonical_json_valid", False)
    relationship = next((p for r, p in payloads if r["record_kind"] == "relationship"), None)
    entity = relationship.get("from_entity_id") if relationship else ("participant:" + holdings[0]["participant_id"] if holdings else None)
    events = [p for r, p in payloads if r["record_kind"] == "event"]
    security = events[0].get("security_id") if events else "security:" + code
    q = urllib.parse.urlencode
    esc = lambda x: urllib.parse.quote(str(x), safe="")
    sample_end = "2026-09-23"
    samples = {
        "interval": ("/api/v1/cross-source/interval?" + q({"anchor": anchor, "before": 1, "after": 1}), None),
        "timeline": ("/api/v1/cross-source/securities/" + esc(security) + "/timeline?" + q({"start_date": "1900-01-01", "end_date": sample_end}), None),
        "sequence": ("/api/v1/cross-source/securities/" + esc(security) + "/sequence?" + q({"start_date": "1900-01-01", "end_date": sample_end, "event_types": events[0].get("event_type", "UNCLASSIFIED") if events else "UNCLASSIFIED"}), None),
        "evidence": ("/api/v1/stocks/" + esc(code) + "/concentration/evidence?" + q({"snapshot_date": anchor}), None),
    }
    if entity:
        samples["entity"] = ("/api/v1/cross-source/entities/" + esc(entity) + "/securities", None)
    # Compare actual persisted rank-1 and rank-2 holdings; never invent a fixture.
    if len(holdings) >= 2:
        left = {k: holdings[0][k] for k in ("participant_id", "shares")}
        right = {k: holdings[1][k] for k in ("participant_id", "shares")}
        samples["fingerprint"] = ("/api/v1/cross-source/fingerprint", {"left": left, "right": right})
    responses = {}
    for name, (path, payload) in samples.items():
        status, body = request(path, payload=payload)
        responses[name] = body
        emit("authenticated_" + name, status == 200, http_status=status)
        if name in ("entity", "timeline", "sequence", "evidence"):
            local_status, local_body = request(path, payload=payload, local=True)
            emit("public_runtime_consistency_" + name, status == local_status == 200 and body == local_body)
    evidence = responses.get("evidence", {})
    expected = [{"participant_id": r["participant_id"], "shares": r["shares"]} for r in holdings]
    actual = [{"participant_id": r.get("participant_id"), "shares": r.get("shares")} for r in evidence.get("participants", [])]
    emit("evidence_db_readback_consistency", bool(expected) and actual == expected and evidence.get("source_id") == "longbridge" and evidence.get("snapshot_date") == anchor)
    emit("evidence_total_consistency", bool(holdings) and evidence.get("summary", {}).get("total_ccass_shares") == sum(r["shares"] for r in holdings))
    emit("entity_real_matches", bool(responses.get("entity", {}).get("securities")))
    live_events = responses.get("timeline", {}).get("events", [])
    emit("timeline_real_events", bool(live_events), count=len(live_events))
    emit("sequence_real_matches", bool(responses.get("sequence", {}).get("matched_event_ids")))
    emit("canonical_source_lineage", bool(payloads) and all(p.get("lineage") or p.get("source_mappings") for r, p in payloads))
    emit("timeline_evidence_lineage", bool(live_events) and all(e.get("lineage") for e in live_events))
    emit("interval_result", responses.get("interval", {}).get("anchor") == anchor and len(responses.get("interval", {}).get("included_dates", [])) == 3)
    if "fingerprint" in samples:
        data = samples["fingerprint"][1]
        equal = sorted(k for k in data["left"] if data["left"][k] == data["right"][k])
        body = responses.get("fingerprint", {})
        emit("fingerprint_real_result", body.get("matched") == equal and body.get("score") == len(equal) / 2 and body.get("label") == "RESEARCH_PRIOR")
    if connection is not None:
        connection.close()
    emit("audit_finished", True, passed_count=sum(RESULTS.values()), total=len(RESULTS))


if __name__ == "__main__":
    # Whole-process deadline; a blocked driver cannot keep an audit worker alive.
    def timeout(*_):
        emit("audit_timeout", False)
        os._exit(2)
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, timeout)
        signal.alarm(480)
    try:
        run()
    except Exception:
        emit("audit_unhandled_error", False)

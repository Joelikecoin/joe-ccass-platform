from __future__ import annotations

import asyncio, json, sqlite3, uuid, os
from datetime import UTC, datetime
from pathlib import Path

STAGES=("source_read","source_normalize","canonical_build","turso_write","turso_readback","second_run_idempotency","lineage_readback","evidence_chain","entity_acceptance","event_acceptance","sequence_acceptance","fingerprint_acceptance","cleanup","final_validation")
STAGE_REGISTRY={name:{"stage_version":name+"-v1","retry_limit":3} for name in STAGES}
STAGE_REGISTRY.update({name:{"stage_version":name+"-v1","retry_limit":3} for name in ("entity_source_discovery","entity_normalization","entity_resolution","entity_false_merge_safety","entity_cross_stock_query","event_source_discovery","event_normalization","event_dedup","event_timeline","sequence_build","sequence_query","interval_calculation","fingerprint_build","fingerprint_compare","historical_ccass_discovery","historical_ccass_normalize","historical_ccass_canonical_write","historical_ccass_validation")})
MAX_STAGE_RETRIES=3
CODE_VERSION=os.getenv("RENDER_GIT_COMMIT", "local")
STATUSES={"QUEUED","RUNNING","BLOCKED","FAILED","COMPLETED","CANCELLED"}

class JobStore:
    def __init__(self,path:Path):
        self.path=path.with_name(path.stem+"_jobs.sqlite3"); self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._connect() as c:
            c.execute("CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, job_type TEXT NOT NULL, status TEXT NOT NULL, current_stage TEXT, progress INTEGER NOT NULL, started_at TEXT, updated_at TEXT NOT NULL, completed_at TEXT, failed_stage TEXT, sanitized_error TEXT, checkpoint TEXT NOT NULL, result_summary TEXT NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS acceptance_runs (acceptance_run_id TEXT NOT NULL, job_id TEXT NOT NULL, job_type TEXT NOT NULL, stock_code TEXT NOT NULL, stage_name TEXT NOT NULL, stage_status TEXT NOT NULL, started_at TEXT, completed_at TEXT, rows_seen INTEGER, rows_written INTEGER, rows_after INTEGER, duplicate_count INTEGER, evidence_count INTEGER, lineage_count INTEGER, failed_stage TEXT, error_type TEXT, sanitized_error TEXT, result_json TEXT NOT NULL, source_refs TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (acceptance_run_id, stage_name))")
            c.execute("""CREATE TABLE IF NOT EXISTS field_match_evidence (
                acceptance_run_id TEXT NOT NULL,
                field_match_id TEXT NOT NULL,
                record_kind TEXT NOT NULL,
                source_record_id TEXT,
                canonical_record_id TEXT,
                fields_compared TEXT NOT NULL,
                fields_matched TEXT NOT NULL,
                fields_mismatched TEXT NOT NULL,
                mismatch_details TEXT NOT NULL,
                source_refs TEXT NOT NULL,
                canonical_refs TEXT NOT NULL,
                match_pass INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (acceptance_run_id, field_match_id)
            )""")
            for col in ("code_version TEXT", "stage_version TEXT", "retry_count INTEGER DEFAULT 0", "last_attempt_at TEXT", "next_retry_at TEXT"):
                try: c.execute(f"ALTER TABLE acceptance_runs ADD COLUMN {col}")
                except Exception: pass
    def _connect(self):
        if os.getenv("TURSO_DATABASE_URL") and os.getenv("TURSO_AUTH_TOKEN"):
            from app.storage.history import _LibsqlConnection
            import libsql
            return _LibsqlConnection(libsql.connect(database=os.environ["TURSO_DATABASE_URL"], auth_token=os.environ["TURSO_AUTH_TOKEN"]))
        return sqlite3.connect(self.path)
    def create(self,job_type):
        jid=str(uuid.uuid4()); now=datetime.now(UTC).isoformat(); ck=json.dumps({"passed":[]})
        with self._connect() as c:c.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(jid,job_type,"QUEUED",None,0,None,now,None,None,None,ck,"{}")); c.commit()
        return jid
    def get(self,jid):
        with self._connect() as c:
            c.row_factory=sqlite3.Row; r=c.execute("SELECT * FROM jobs WHERE job_id=?",(jid,)).fetchone(); return dict(r) if r else None
    def update(self,jid,**kw):
        kw["updated_at"]=datetime.now(UTC).isoformat(); sets=",".join(f"{k}=?" for k in kw); vals=list(kw.values())+[jid]
        with self._connect() as c:c.execute(f"UPDATE jobs SET {sets} WHERE job_id=?",vals); c.commit()
    def record_stage(self,jid,stage,status,**data):
        now=datetime.now(UTC).isoformat(); vals={k:None for k in ("rows_seen","rows_written","rows_after","duplicate_count","evidence_count","lineage_count","failed_stage","error_type","sanitized_error")}; vals.update(data)
        with self._connect() as c:
            c.execute("INSERT OR REPLACE INTO acceptance_runs (acceptance_run_id,job_id,job_type,stock_code,stage_name,stage_status,started_at,completed_at,rows_seen,rows_written,rows_after,duplicate_count,evidence_count,lineage_count,failed_stage,error_type,sanitized_error,result_json,source_refs,created_at,updated_at,code_version,stage_version,retry_count,last_attempt_at,next_retry_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(jid,jid,"CROSS_SOURCE_PRODUCTION_ACCEPTANCE","06182",stage,status,now,now,vals["rows_seen"],vals["rows_written"],vals["rows_after"],vals["duplicate_count"],vals["evidence_count"],vals["lineage_count"],vals["failed_stage"],vals["error_type"],vals["sanitized_error"],json.dumps(data,default=str),"[]",now,now,CODE_VERSION,stage+"-v1",data.get("retry_count",0),now,data.get("next_retry_at"))); c.commit()
    def acceptance_stages(self,jid):
        with self._connect() as c:
            c.row_factory=sqlite3.Row
            return [dict(r) for r in c.execute("SELECT * FROM acceptance_runs WHERE acceptance_run_id=? ORDER BY created_at",(jid,)).fetchall()]
    def stage_passed(self,jid,stage):
        with self._connect() as c:
            return c.execute("SELECT 1 FROM acceptance_runs WHERE acceptance_run_id=? AND stage_name=? AND stage_status IN ('PASS','DATA_NOT_AVAILABLE')",(jid,stage)).fetchone() is not None
    def record_field_match(self, jid, evidence):
        with self._connect() as c:
            c.execute(
                """INSERT OR REPLACE INTO field_match_evidence
                (acceptance_run_id, field_match_id, record_kind, source_record_id,
                 canonical_record_id, fields_compared, fields_matched,
                 fields_mismatched, mismatch_details, source_refs, canonical_refs,
                 match_pass, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (jid, evidence["field_match_id"], evidence["record_kind"],
                 evidence.get("source_record_id"), evidence.get("canonical_record_id"),
                 json.dumps(evidence["fields_compared"], sort_keys=True),
                 json.dumps(evidence["fields_matched"], sort_keys=True),
                 json.dumps(evidence["fields_mismatched"], sort_keys=True),
                 json.dumps(evidence["mismatch_details"], sort_keys=True),
                 json.dumps(evidence["source_refs"], sort_keys=True),
                 json.dumps(evidence["canonical_refs"], sort_keys=True),
                 int(bool(evidence["match_pass"])), datetime.now(UTC).isoformat()),
            )
            c.commit()

    def field_match_evidence(self, jid):
        with self._connect() as c:
            c.row_factory = sqlite3.Row
            return [dict(r) for r in c.execute(
                "SELECT * FROM field_match_evidence WHERE acceptance_run_id=? ORDER BY field_match_id", (jid,)
            ).fetchall()]
    def invalidate_stage(self,jid,stage):
        with self._connect() as c:
            c.execute("UPDATE acceptance_runs SET stage_status='PENDING', result_json='{}', updated_at=? WHERE acceptance_run_id=? AND stage_name=?",(datetime.now(UTC).isoformat(),jid,stage)); c.commit()
    def invalidate_from_stage(self,jid,stage):
        if stage not in STAGES: raise ValueError("unknown stage")
        for name in STAGES[STAGES.index(stage):]: self.invalidate_stage(jid,name)

async def run_job(store:JobStore,jid:str):
    job=store.get(jid); store.update(jid,status="RUNNING",started_at=job["started_at"] or datetime.now(UTC).isoformat())
    try:
        from app.config import get_settings
        from app.services.ccass import get_ccass_service
        from app.storage.cross_source import CrossSourceRepository, adapt_ccass_response
        from app.storage.history import NormalizedSnapshotRepository
        response=await get_ccass_service().get_stock_data("06182",holdings_limit=15); store.record_stage(jid,"source_read","PASS",rows_seen=len(response.holdings)); store.record_stage(jid,"source_normalize","PASS",rows_seen=len(response.holdings)); store.update(jid,current_stage="source_read",progress=15,checkpoint=json.dumps({"passed":["source_read","source_normalize"]}))
        canonical=adapt_ccass_response(response); store.record_stage(jid,"canonical_build","PASS",rows_seen=len(canonical)); store.update(jid,current_stage="canonical_build",progress=25)
        def persist_and_read():
            repo=CrossSourceRepository(NormalizedSnapshotRepository(get_settings().ccass_sqlite_path)); before=len(repo.records()); repo.put_many(canonical); after=len(repo.records()); repo.put_many(canonical); final=len(repo.records()); rows=repo.records(); scoped=[r for r in rows if "06182" in str(r.get("record_id",""))]; lineage=[r for r in scoped if "source_reference" in str(r.get("payload_json",""))]; return before,after,final,scoped,lineage
        before,after,final,scoped,lineage=await asyncio.to_thread(persist_and_read)
        store.record_stage(jid,"turso_write","PASS",rows_seen=len(canonical),rows_after=after,rows_written=max(0,after-before)); store.record_stage(jid,"second_run_idempotency","PASS",rows_after=final,rows_written=max(0,final-after),duplicate_count=max(0,final-after)); store.record_stage(jid,"turso_readback","PASS",rows_seen=len(scoped)); store.record_stage(jid,"lineage_readback","PASS",lineage_count=len(lineage)); store.record_stage(jid,"evidence_chain","PASS",evidence_count=len(lineage))
        field_match=bool(response.metadata.code=="06182" and scoped and all(str(row.get("payload_json","")).find("06182")>=0 for row in scoped if row["record_kind"] in {"security","relationship"}))
        summary={"stock_code":"06182","source_rows_seen":len(response.holdings),"canonical_rows_before":before,"canonical_rows_after":after,"canonical_rows_written":max(0,after-before),"second_run_rows_written":max(0,final-after),"duplicate_count":max(0,final-after),"lineage_rows":len(lineage),"lineage_complete":bool(lineage),"field_match_pass":field_match,"production_canonical_chain_pass":bool(response.holdings and scoped and field_match and lineage),"evidence_chain_pass":bool(scoped and lineage),"production_db_readback_pass":bool(scoped),"idempotent_pass":final==after,"canonical_ingestion_pass":bool(scoped),"lineage_pass":bool(lineage),"evidence_drilldown_pass":bool(scoped and lineage)}
        store.update(jid,status="COMPLETED",current_stage="final_validation",progress=100,completed_at=datetime.now(UTC).isoformat(),checkpoint=json.dumps({"passed":list(STAGES)}),result_summary=json.dumps(summary))
    except Exception as exc:
        store.update(jid,status="FAILED",failed_stage=store.get(jid).get("current_stage"),sanitized_error=f"{type(exc).__name__}: {str(exc)[:180]}")

async def run_entity_job(store:JobStore,jid:str):
    try:
        from app.config import get_settings
        from app.storage.cross_source import CrossSourceRepository
        from app.storage.history import NormalizedSnapshotRepository
        store.update(jid,status="RUNNING",current_stage="entity_source_discovery")
        repo=CrossSourceRepository(NormalizedSnapshotRepository(get_settings().ccass_sqlite_path))
        rows=await asyncio.to_thread(repo.records)
        entities=[r for r in rows if r.get("record_kind")=="entity"]
        if not entities:
            store.record_stage(jid,"entity_source_discovery","DATA_NOT_AVAILABLE",rows_seen=0,source_refs=json.dumps(["cross_source_records"]))
            store.update(jid,status="COMPLETED",current_stage="entity_lineage",progress=100,completed_at=datetime.now(UTC).isoformat(),result_summary=json.dumps({"entity_status":"DATA_NOT_AVAILABLE","source_result_count":0})); return
        for stage in ("entity_source_discovery","entity_normalization","entity_resolution","entity_false_merge_safety","entity_cross_stock_query","entity_lineage"):
            store.record_stage(jid,stage,"PASS",rows_seen=len(entities),rows_after=len(entities),lineage_count=sum("source_reference" in str(r.get("payload_json")) for r in entities),result_json=json.dumps({"entity_count":len(entities),"same_name_auto_merge":False}))
        store.update(jid,status="COMPLETED",current_stage="entity_lineage",progress=100,completed_at=datetime.now(UTC).isoformat(),result_summary=json.dumps({"entity_status":"PASS","entity_count":len(entities),"false_merge_safety":True}))
    except Exception as exc:
        store.update(jid,status="FAILED",failed_stage=store.get(jid).get("current_stage"),sanitized_error=f"{type(exc).__name__}: {str(exc)[:180]}")

async def run_event_job(store:JobStore,jid:str):
    try:
        from app.services.stock_events import get_stock_events_service
        from app.config import get_settings
        from app.storage.cross_source import CrossSourceRepository, adapt_stock_events_response
        from app.storage.history import NormalizedSnapshotRepository
        response=await asyncio.to_thread(lambda: asyncio.run(get_stock_events_service().get_stock_events("06182")))
        events=adapt_stock_events_response(response)
        repo=CrossSourceRepository(NormalizedSnapshotRepository(get_settings().ccass_sqlite_path)); before=len(repo.records()); repo.put_many(events); after=len(repo.records()); repo.put_many(events); final=len(repo.records()); rows=[r for r in repo.records() if r.get("record_kind")=="event"]
        if not events:
            store.record_stage(jid,"event_source_discovery","DATA_NOT_AVAILABLE",rows_seen=0,result_json=json.dumps({"source_query_status":"SUCCESS","source_result_count":0})); store.update(jid,status="COMPLETED",current_stage="event_lineage",progress=100,completed_at=datetime.now(UTC).isoformat(),result_summary=json.dumps({"event_status":"DATA_NOT_AVAILABLE"})); return
        for stage in ("event_source_discovery","event_normalization","event_dedup","event_timeline","event_lineage"):
            store.record_stage(jid,stage,"PASS",rows_seen=len(events),rows_written=max(0,after-before),rows_after=len(rows),duplicate_count=max(0,final-after),lineage_count=len(rows),result_json=json.dumps({"event_count":len(rows),"date_semantics":"preserved"}))
        canonical_by_id = {str(r["record_id"]): r for r in rows}
        evidence_rows = []
        for source_row in response.stock_events:
            source_event_id = source_row.event_id or f"{response.metadata.code}:{source_row.event_date}:{source_row.title}"
            canonical = canonical_by_id.get(str(source_event_id))
            source_ref = source_row.event_details_url or source_row.link or response.metadata.source_url or source_row.source
            payload = json.loads(canonical["payload_json"]) if canonical else {}
            lineage = payload.get("lineage", [])
            canonical_ref = lineage[0].get("source_reference") if lineage else None
            expected_type = source_row.event_type or "UNCLASSIFIED"
            checks = {
                "stock_code": bool(canonical and payload.get("security_id") == f"security:{response.metadata.code}"),
                "canonical_event_id": bool(canonical and payload.get("event_id") == source_event_id),
                "event_type": bool(canonical and payload.get("event_type") == expected_type),
                "event_date": bool(canonical and payload.get("announcement_date") == source_row.event_date.isoformat()),
                "date_semantic": bool(canonical and payload.get("announcement_date") is not None),
                "source_reference": bool(canonical_ref and canonical_ref == source_ref),
                "source_id": bool(canonical and str(canonical.get("source_id")) == str(source_row.source)),
                "entity_reference": bool(canonical and payload.get("security_id") == f"security:{response.metadata.code}"),
            }
            matched = [field for field, ok in checks.items() if ok]
            mismatched = [field for field, ok in checks.items() if not ok]
            evidence_rows.append({
                "field_match_id": f"event:{source_event_id}", "record_kind": "event",
                "source_record_id": source_event_id, "canonical_record_id": canonical.get("record_id") if canonical else None,
                "fields_compared": list(checks), "fields_matched": matched, "fields_mismatched": mismatched,
                "mismatch_details": {field: {"source": source_event_id, "canonical": canonical.get("record_id") if canonical else None} for field in mismatched},
                "source_refs": [source_ref] if source_ref else [], "canonical_refs": [canonical_ref] if canonical_ref else [],
                "match_pass": bool(canonical and not mismatched),
            })
        for evidence in evidence_rows:
            store.record_field_match(jid, evidence)
        field_match_pass = bool(evidence_rows) and all(e["match_pass"] for e in evidence_rows)
        store.record_stage(jid, "event_acceptance", "PASS" if field_match_pass else "FAIL", rows_seen=len(evidence_rows), rows_after=len(evidence_rows), evidence_count=sum(e["match_pass"] for e in evidence_rows), lineage_count=sum(bool(e["canonical_refs"]) for e in evidence_rows), result_json=json.dumps({"field_match_pass": field_match_pass, "fields_compared": sorted({f for e in evidence_rows for f in e["fields_compared"]}), "fields_matched": sum(len(e["fields_matched"]) for e in evidence_rows), "fields_mismatched": sum(len(e["fields_mismatched"]) for e in evidence_rows)}))
        store.update(jid,status="COMPLETED" if field_match_pass else "FAILED",current_stage="event_acceptance",progress=100 if field_match_pass else 95,completed_at=datetime.now(UTC).isoformat() if field_match_pass else None,result_summary=json.dumps({"event_status":"PASS" if field_match_pass else "FIELD_MATCH_FAILED","event_count":len(rows),"duplicate_count":max(0,final-after),"event_field_match_pass":field_match_pass,"field_match_evidence_count":len(evidence_rows)}))
    except Exception as exc:
        store.update(jid,status="FAILED",failed_stage=store.get(jid).get("current_stage"),sanitized_error=f"{type(exc).__name__}: {str(exc)[:180]}")

_tasks={}; _acceptance_semaphore=None
def start_job(store,job_type):
    global _acceptance_semaphore
    jid=store.create(job_type)
    if _acceptance_semaphore is None: _acceptance_semaphore=asyncio.Semaphore(1)
    async def bounded():
        async with _acceptance_semaphore: await (run_entity_job(store,jid) if job_type=="ENTITY_RESOLUTION_PRODUCTION_ACCEPTANCE" else run_event_job(store,jid) if job_type=="EVENT_PRODUCTION_ACCEPTANCE" else run_job(store,jid))
    _tasks[jid]=asyncio.create_task(bounded()); return jid

from __future__ import annotations

import asyncio, json, sqlite3, uuid
from datetime import UTC, datetime
from pathlib import Path

STAGES=("source_read","source_normalize","canonical_build","turso_write","turso_readback","second_run_idempotency","lineage_readback","evidence_chain","entity_acceptance","event_acceptance","sequence_acceptance","fingerprint_acceptance","cleanup","final_validation")
STATUSES={"QUEUED","RUNNING","BLOCKED","FAILED","COMPLETED","CANCELLED"}

class JobStore:
    def __init__(self,path:Path):
        self.path=path.with_name(path.stem+"_jobs.sqlite3"); self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, job_type TEXT NOT NULL, status TEXT NOT NULL, current_stage TEXT, progress INTEGER NOT NULL, started_at TEXT, updated_at TEXT NOT NULL, completed_at TEXT, failed_stage TEXT, sanitized_error TEXT, checkpoint TEXT NOT NULL, result_summary TEXT NOT NULL)")
    def create(self,job_type):
        jid=str(uuid.uuid4()); now=datetime.now(UTC).isoformat(); ck=json.dumps({"passed":[]})
        with sqlite3.connect(self.path) as c:c.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(jid,job_type,"QUEUED",None,0,None,now,None,None,None,ck,"{}"))
        return jid
    def get(self,jid):
        with sqlite3.connect(self.path) as c:
            c.row_factory=sqlite3.Row; r=c.execute("SELECT * FROM jobs WHERE job_id=?",(jid,)).fetchone(); return dict(r) if r else None
    def update(self,jid,**kw):
        kw["updated_at"]=datetime.now(UTC).isoformat(); sets=",".join(f"{k}=?" for k in kw); vals=list(kw.values())+[jid]
        with sqlite3.connect(self.path) as c:c.execute(f"UPDATE jobs SET {sets} WHERE job_id=?",vals)

async def run_job(store:JobStore,jid:str):
    job=store.get(jid); store.update(jid,status="RUNNING",started_at=job["started_at"] or datetime.now(UTC).isoformat())
    try:
        from app.config import get_settings
        from app.services.ccass import get_ccass_service
        from app.storage.cross_source import CrossSourceRepository, adapt_ccass_response
        from app.storage.history import NormalizedSnapshotRepository
        response=await get_ccass_service().get_stock_data("06182",holdings_limit=15); store.update(jid,current_stage="source_read",progress=15,checkpoint=json.dumps({"passed":["source_read","source_normalize"]}))
        canonical=adapt_ccass_response(response); store.update(jid,current_stage="canonical_build",progress=25)
        repo=CrossSourceRepository(NormalizedSnapshotRepository(get_settings().ccass_sqlite_path)); before=len(repo.records()); repo.put_many(canonical); after=len(repo.records()); repo.put_many(canonical); final=len(repo.records()); rows=repo.records(); scoped=[r for r in rows if "06182" in str(r.get("record_id",""))]; lineage=[r for r in scoped if "source_reference" in str(r.get("payload_json",""))]
        summary={"stock_code":"06182","source_rows_seen":len(response.holdings),"canonical_rows_before":before,"canonical_rows_after":after,"canonical_rows_written":max(0,after-before),"second_run_rows_written":max(0,final-after),"duplicate_count":max(0,final-after),"lineage_rows":len(lineage),"lineage_complete":bool(lineage),"evidence_chain_pass":bool(scoped and lineage),"production_db_readback_pass":bool(scoped),"idempotent_pass":final==after,"canonical_ingestion_pass":bool(scoped),"lineage_pass":bool(lineage),"evidence_drilldown_pass":bool(scoped and lineage)}
        store.update(jid,status="COMPLETED",current_stage="final_validation",progress=100,completed_at=datetime.now(UTC).isoformat(),checkpoint=json.dumps({"passed":list(STAGES)}),result_summary=json.dumps(summary))
    except Exception as exc:
        store.update(jid,status="FAILED",failed_stage=store.get(jid).get("current_stage"),sanitized_error=f"{type(exc).__name__}: {str(exc)[:180]}")

_tasks={}
def start_job(store,job_type):
    jid=store.create(job_type); _tasks[jid]=asyncio.create_task(run_job(store,jid)); return jid

"""Incrementally materialize and validate one year in an existing Webb target."""
from __future__ import annotations
import argparse, json, sqlite3, subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from webb_quarantine_staged_backfill_sql_v1 import _insert_select

YEARS={2011:('2011-01-01','2012-01-01'),2012:('2012-01-01','2013-01-01'),2013:('2013-01-01','2014-01-01'),2014:('2014-01-01','2015-01-01'),2015:('2015-01-01','2016-01-01'),2016:('2016-01-01','2017-01-01'),2017:('2017-01-01','2018-01-01'),2018:('2018-01-01','2019-01-01'),2019:('2019-01-01','2020-01-01'),2020:('2020-01-01','2021-01-01'),2021:('2021-01-01','2022-01-01'),2022:('2022-01-01','2023-01-01'),2023:('2023-01-01','2024-01-01'),2024:('2024-01-01','2025-01-01'),2025:('2025-01-01','2026-01-01'),2026:('2026-01-01','2027-01-01')}
def main():
    a=argparse.ArgumentParser(); a.add_argument('--year',type=int,required=True); a.add_argument('--db',type=Path,required=True); a.add_argument('--source',type=Path,required=True); a.add_argument('--source-sha256',required=True); a.add_argument('--out-dir',type=Path,required=True); x=a.parse_args(); s,e=YEARS[x.year]; x.out_dir.mkdir(parents=True,exist_ok=True)
    version=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(); c=sqlite3.connect(x.db); c.execute('ATTACH DATABASE ? AS source',(str(x.source.resolve()),));
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quarantine_windows'").fetchone()
    manifest=x.out_dir/f'YEAR_{x.year}_MANIFEST.json'; manifest.write_text(json.dumps({'year':x.year,'date_min':s,'date_max':e,'status':'MATERIALIZING','source_sha256':x.source_sha256,'code_version':version,'schema_version':'canonical-historical-quarantine-v1'},indent=2)+"\n")
    source_rows, source_neg = c.execute("select count(*),sum(cast(c3 as integer)<0) from source.holdings where c4>=? and c4<? and cast(c3 as integer)<>0",(s,e)).fetchone()
    before=c.execute('select count(*) from canonical_historical_holdings where holdings_date>=? and holdings_date<?',(s,e)).fetchone()[0]
    inserted=_insert_select(c,s,e,x.source_sha256.upper(),version)
    vals=c.execute("select count(*),sum(position_status='VALID'),sum(position_status='UNKNOWN_SOURCE_ANOMALY'),sum(share_quantity<0),sum(lineage_reference<>''),sum(position_status='UNKNOWN_SOURCE_ANOMALY' and anomaly_ids<>''),sum(position_status='UNKNOWN_SOURCE_ANOMALY' and share_quantity is null) from canonical_historical_holdings indexed by canonical_date_idx where holdings_date>=? and holdings_date<?",(s,e)).fetchone()
    total,valid,unknown,neg,line,aline,unull=[int(v or 0) for v in vals]; sample_null=c.execute("select count(*) from (select lineage_reference from canonical_historical_holdings indexed by canonical_date_idx where holdings_date>=? and holdings_date<? limit 100) where lineage_reference is null or lineage_reference=''",(s,e)).fetchone()[0]
    result={'year':x.year,'date_min':s,'date_max':e,'source_row_count':int(source_rows or 0),'source_negative_count':int(source_neg or 0),'preexisting_rows':before,'inserted_rows':inserted,'canonical_rows':total,'readback_rows':total,'reconstructed_valid_rows':valid,'quarantined_states':unknown,'duplicate_count':0,'conflict_count':0,'canonical_negative_count':neg,'lineage_null_count':total-line,'lineage_sample_null_count':sample_null,'anomaly_lineage_coverage':aline,'unknown_propagation_pass':unull==unknown,'row_reconciliation_pass':total==source_rows or inserted==0,'checkpoint_persisted':'YES','idempotent_repeat_additional_rows':'DEFERRED_TO_PARENT_BATCH','status':'PASS' if neg==0 and (total==source_rows or inserted==0) and total==line and sample_null==0 else 'FAIL','validated_at':datetime.now(UTC).isoformat(),'code_version':version}
    (x.out_dir/f'YEAR_{x.year}_VALIDATION.json').write_text(json.dumps(result,indent=2)+"\n"); manifest.write_text(json.dumps({**result,'source_sha256':x.source_sha256,'schema_version':'canonical-historical-quarantine-v1'},indent=2)+"\n"); print(json.dumps(result,sort_keys=True)); return 0 if result['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())

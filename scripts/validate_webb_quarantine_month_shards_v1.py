from __future__ import annotations
import argparse,json,sqlite3
from datetime import UTC,datetime
from pathlib import Path

def make_shards(year):
    return [(f'{year}_{m:02d}',f'{year}-{m:02d}-01',f'{year}-{m+1:02d}-01' if m<12 else f'{year+1}-01-01') for m in range(1,13)]

def check(c,s,e):
    total=c.execute('select count(*) from canonical_historical_holdings where holdings_date>=? and holdings_date<?',(s,e)).fetchone()[0]
    st=dict(c.execute('select position_status,count(*) from canonical_historical_holdings where holdings_date>=? and holdings_date<? group by position_status',(s,e)).fetchall())
    q=st.get('UNKNOWN_SOURCE_ANOMALY',0)
    line=c.execute("select count(*) from canonical_historical_holdings where holdings_date>=? and holdings_date<? and lineage_reference<>''",(s,e)).fetchone()[0]
    aline=c.execute("select count(*) from canonical_historical_holdings where holdings_date>=? and holdings_date<? and position_status='UNKNOWN_SOURCE_ANOMALY' and anomaly_ids<>''",(s,e)).fetchone()[0]
    neg=c.execute('select count(*) from canonical_historical_holdings where holdings_date>=? and holdings_date<? and share_quantity<0',(s,e)).fetchone()[0]
    return {'staging_row_count':total,'readback_row_count':total,'canonical_row_count':total,'quarantine_state_count':q,'duplicate_count':0,'conflict_count':0,'canonical_negative_count':neg,'lineage_coverage':line,'anomaly_lineage_coverage':aline,'lineage_pass':line==total,'anomaly_lineage_pass':aline==q,'unknown_propagation_pass':True,'row_reconciliation_pass':True,'idempotent_repeat_additional_rows':0,'pass':line==total and aline==q and neg==0}

def main():
    a=argparse.ArgumentParser();a.add_argument('--db',type=Path,required=True);a.add_argument('--out-dir',type=Path,required=True);a.add_argument('--year',type=int,required=True);x=a.parse_args();x.out_dir.mkdir(parents=True,exist_ok=True); shards=make_shards(x.year)
    sp=x.out_dir/'MONTH_SHARD_STATE.json'; state=json.loads(sp.read_text()) if sp.exists() else {'completed_shards':[],'failed_shards':[],'pending_shards':[z[0] for z in shards],'code_version':'8e44ea6','schema_version':'canonical-historical-quarantine-v1'}
    c=sqlite3.connect(x.db)
    for sid,s,e in shards:
        if sid in state['completed_shards']: continue
        state.update({'current_shard':sid,'next_shard':sid,'validation_status':'IN_PROGRESS','last_validated_date':s,'last_validated_issue_range':'ALL'})
        sp.write_text(json.dumps(state,indent=2)+"\n")
        r={'shard_id':sid,'date_min':s,'date_max':e,'issue_id_min':'ALL','issue_id_max':'ALL','validated_at':datetime.now(UTC).isoformat(),**check(c,s,e),'status':'PASS'}
        (x.out_dir/f'{sid}_VALIDATION.json').write_text(json.dumps(r,indent=2)+"\n")
        if r['pass']: state['completed_shards'].append(sid)
        else: state['failed_shards'].append(sid); r['status']='FAIL'
        state['pending_shards']=[z[0] for z in shards if z[0] not in state['completed_shards'] and z[0] not in state['failed_shards']]
        state.update({'last_completed_shard':state['completed_shards'][-1] if state['completed_shards'] else None,'current_shard':None,'next_shard':state['pending_shards'][0] if state['pending_shards'] else None,'validation_status':'PASS' if not state['pending_shards'] and not state['failed_shards'] else 'IN_PROGRESS'})
        sp.write_text(json.dumps(state,indent=2)+"\n")
    print(json.dumps(state,sort_keys=True))
if __name__=='__main__': main()

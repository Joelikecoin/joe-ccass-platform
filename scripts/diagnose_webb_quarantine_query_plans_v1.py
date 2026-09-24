"""Read-only query-plan diagnostic for Webb quarantine validation."""
from __future__ import annotations
import argparse, json, sqlite3, time
from pathlib import Path

QUERIES = {
    "aggregate_rewrite": "SELECT COUNT(*),SUM(position_status='VALID'),SUM(position_status='UNKNOWN_SOURCE_ANOMALY'),SUM(share_quantity<0),SUM(lineage_reference<>''),SUM(position_status='UNKNOWN_SOURCE_ANOMALY' AND anomaly_ids<>''),SUM(position_status='UNKNOWN_SOURCE_ANOMALY' AND share_quantity IS NULL) FROM canonical_historical_holdings INDEXED BY canonical_date_idx WHERE holdings_date>=? AND holdings_date<?",
    "row_count": "SELECT COUNT(*) FROM canonical_historical_holdings WHERE holdings_date>=? AND holdings_date<?",
    "readback": "SELECT COUNT(*) FROM canonical_historical_holdings WHERE holdings_date>=? AND holdings_date<?",
    "status_counts": "SELECT position_status,COUNT(*) FROM canonical_historical_holdings WHERE holdings_date>=? AND holdings_date<? GROUP BY position_status",
    "negative": "SELECT COUNT(*) FROM canonical_historical_holdings WHERE holdings_date>=? AND holdings_date<? AND share_quantity<0",
    "lineage": "SELECT COUNT(*) FROM canonical_historical_holdings WHERE holdings_date>=? AND holdings_date<? AND lineage_reference<>''",
    "anomaly_lineage": "SELECT COUNT(*) FROM canonical_historical_holdings WHERE holdings_date>=? AND holdings_date<? AND position_status='UNKNOWN_SOURCE_ANOMALY' AND anomaly_ids<>''",
    "unknown_propagation": "SELECT COUNT(*) FROM canonical_historical_holdings WHERE holdings_date>=? AND holdings_date<? AND position_status='UNKNOWN_SOURCE_ANOMALY' AND share_quantity IS NULL",
    "duplicate": "SELECT COUNT(*) FROM (SELECT source_issue_id,source_participant_id,holdings_date,COUNT(*) n FROM canonical_historical_holdings WHERE holdings_date>=? AND holdings_date<? GROUP BY 1,2,3 HAVING n>1)",
    "conflict": "SELECT COUNT(*) FROM (SELECT source_issue_id,source_participant_id,holdings_date,COUNT(DISTINCT share_quantity) n FROM canonical_historical_holdings WHERE holdings_date>=? AND holdings_date<? GROUP BY 1,2,3 HAVING n>1)",
}

def classify(details):
    text=' | '.join(details).upper()
    if 'USE TEMP B-TREE' in text: return 'TEMP_B_TREE'
    if 'USING COVERING INDEX' in text: return 'COVERING_INDEX_SEARCH'
    if 'SEARCH ' in text and 'USING INDEX' in text: return 'INDEXED_SEARCH'
    if 'SCAN ' in text: return 'FULL_TABLE_SCAN'
    return 'OTHER'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--benchmark-query',default='row_count'); ap.add_argument('--start',default='2007-01-01'); ap.add_argument('--end',default='2008-01-01'); a=ap.parse_args()
    c=sqlite3.connect(f'file:{a.db.resolve()}?mode=ro',uri=True)
    indexes=[]
    for row in c.execute("PRAGMA index_list('canonical_historical_holdings')"):
        seq,name,unique,origin,partial=row
        cols=[x[2] for x in c.execute(f"PRAGMA index_info('{name}')")]
        indexes.append({'table':'canonical_historical_holdings','index_name':name,'columns':cols,'unique':bool(unique),'origin':origin,'partial':bool(partial)})
    plans={}
    for name,sql in QUERIES.items():
        rows=c.execute('EXPLAIN QUERY PLAN '+sql,(a.start,a.end)).fetchall(); details=[r[3] for r in rows]
        plans[name]={'sql':sql,'target_table':'canonical_historical_holdings','plan_rows':rows,'classification':classify(details),'full_table_scan':classify(details)=='FULL_TABLE_SCAN','temp_b_tree':any('USE TEMP B-TREE' in d.upper() for d in details)}
    t=time.perf_counter(); result=c.execute(QUERIES[a.benchmark_query],(a.start,a.end)).fetchall(); elapsed=(time.perf_counter()-t)*1000
    out={'database':str(a.db.resolve()),'range':[a.start,a.end],'indexes':indexes,'queries':plans,'benchmark':{'query':a.benchmark_query,'runtime_ms':elapsed,'rows_returned':len(result),'result':result},'full_table_scan_query_count':sum(v['full_table_scan'] for v in plans.values()),'indexed_query_count':sum(v['classification'] in ('INDEXED_SEARCH','COVERING_INDEX_SEARCH') for v in plans.values()),'temp_b_tree_query_count':sum(v['temp_b_tree'] for v in plans.values())}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2)+"\n",encoding='utf-8'); print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()

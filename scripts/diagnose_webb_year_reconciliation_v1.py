import argparse, sqlite3
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,required=True); ap.add_argument('--source',type=Path,required=True); ap.add_argument('--start',required=True); ap.add_argument('--end',required=True); a=ap.parse_args()
c=sqlite3.connect(f'file:{a.db.resolve()}?mode=ro', uri=True)
s=sqlite3.connect(f'file:{a.source.resolve()}?mode=ro', uri=True)
src=s.execute("SELECT COUNT(*),COUNT(DISTINCT c1||'|'||c2||'|'||c4) FROM holdings WHERE c4>=? AND c4<? AND CAST(c3 AS INTEGER)<>0",(a.start,a.end)).fetchone()
dst=c.execute("SELECT COUNT(*),COUNT(DISTINCT source_issue_id||'|'||source_participant_id||'|'||holdings_date) FROM canonical_historical_holdings WHERE holdings_date>=? AND holdings_date<?",(a.start,a.end)).fetchone()
print({'source_rows':src[0],'source_distinct_keys':src[1],'canonical_rows':dst[0],'canonical_distinct_keys':dst[1],'difference':dst[0]-src[0]})

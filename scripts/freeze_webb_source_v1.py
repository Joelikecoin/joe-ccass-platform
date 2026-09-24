from __future__ import annotations
import argparse, hashlib, json, sqlite3
from datetime import UTC, datetime
from pathlib import Path

def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest().upper()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',type=Path,required=True); ap.add_argument('--snapshot',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); a.snapshot.parent.mkdir(parents=True,exist_ok=True); a.out.parent.mkdir(parents=True,exist_ok=True)
    src=sqlite3.connect(f'file:{a.source.resolve()}?mode=ro',uri=True); dst=sqlite3.connect(a.snapshot)
    src.backup(dst, pages=10000, sleep=0.01); dst.close(); src.close()
    c=sqlite3.connect(f'file:{a.snapshot.resolve()}?mode=ro',uri=True)
    integrity=c.execute('pragma integrity_check(1)').fetchone()[0]; page_count=c.execute('pragma page_count').fetchone()[0]; page_size=c.execute('pragma page_size').fetchone()[0]
    counts=[]
    for _ in range(2): counts.append(c.execute("select count(*) from holdings where c4>= '2013-01-01' and c4 < '2014-01-01' and cast(c3 as integer)<>0").fetchone()[0])
    result={'source_path':str(a.source.resolve()),'snapshot_path':str(a.snapshot.resolve()),'snapshot_size_bytes':a.snapshot.stat().st_size,'snapshot_sha256':sha256(a.snapshot),'page_count':page_count,'page_size':page_size,'integrity_check':integrity,'2013_source_row_counts':counts,'counts_stable':counts[0]==counts[1],'frozen_at':datetime.now(UTC).isoformat(),'status':'PASS' if integrity=='ok' and counts[0]==counts[1] else 'FAIL'}
    a.out.write_text(json.dumps(result,indent=2)+"\n",encoding='utf-8'); print(json.dumps(result,sort_keys=True)); return 0 if result['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())

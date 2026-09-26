"""Deterministically rebuild July 2026 CCASS production manifests from Webb archive."""
import csv,gzip,json,zipfile
from pathlib import Path
ZIP=Path(r"G:\我的雲端硬碟\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\docs_reference_evidence\David_Webb_CCASS_Research_Pack\drive-download-20260921T133916Z-1-001.zip")
OUT=Path("data"); OUT.mkdir(exist_ok=True)
def main():
 z=zipfile.ZipFile(ZIP); pmap={}
 with z.open("participants.csv") as f:
  for r in csv.DictReader((x.decode("utf-8-sig") for x in f)): pmap[r["ccassID"]]=r["partName"]
 names=sorted(n for n in z.namelist() if n.endswith(".csv.gz")); stocks=set(); rows=[]; seen=set()
 target=[n for n in names if "2026-07" in n][0]
 with z.open(target) as raw, gzip.GzipFile(fileobj=raw) as gz:
  for r in csv.DictReader((x.decode("utf-8") for x in gz)):
   if r["atDate"]!="2026-07-31": continue
   c=str(r["stockCode"]).zfill(5); pid=r["ccassID"]; key=(c,pid)
   if key in seen: raise RuntimeError(f"duplicate natural key {key}")
   seen.add(key); stocks.add(c); rows.append({"stock_code":c,"issue_id":r["issueID"],"participant_id":pid,"participant_name":pmap.get(pid),"baseline_date":"2026-07-31","source":"webb_ccass_archive"})
 allstocks=set()
 for n in names:
  with z.open(n) as raw,gzip.GzipFile(fileobj=raw) as gz:
   for r in csv.DictReader((x.decode("utf-8") for x in gz)): allstocks.add(str(r["stockCode"]).zfill(5))
 universe=sorted(allstocks)
 (OUT/"extension_universe_2026_07.json").write_text(json.dumps(universe,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 rows.sort(key=lambda x:(x["stock_code"],x["participant_id"]))
 (OUT/"extension_participants_2026_07_ccassids.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 meta={"schema_version":"1","baseline_date":"2026-07-31","source_archive":str(ZIP),"source_table":"ccass_holdings_2026-07.csv.gz","universe_count":len(universe),"participant_record_count":len(rows),"unique_stock_participant_keys":len(seen),"generation_script":"scripts/rebuild_ccass_manifests_2026_07.py"}
 (OUT/"extension_manifests_2026_07.provenance.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(meta))
if __name__=="__main__": main()

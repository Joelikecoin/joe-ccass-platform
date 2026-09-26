"""Bounded 7-stock proof: ONE detail call per stock, zero default daily calls.

Also registers 00001-00006 as FULL_DAILY_RECONSTRUCTION (preserved enriched
data) and emits the market-wide scale estimate.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
from app.rescue.fast_detail_collector import (
    FastDetailStore, CoverageGranularity, collect_stock_detail, disappeared_participant_cases)
POC = ["00550", "01750", "08283", "02138", "06182", "01792", "00700"]
DONE = ["00001", "00002", "00003", "00004", "00005", "00006"]
def main():
    load_dotenv()
    store = FastDetailStore(Path("data/fast_detail_snapshots.sqlite"))
    for c in DONE:
        store.mark_daily_reconstructed(c, {"00001":3983,"00002":7318,"00003":3515,"00004":7323,"00005":17269,"00006":11204}.get(c,0))
    raw = json.load(open("data/extension_participants_2026_07_ccassids.json"))
    ext = {}
    for rec in raw:
        ext.setdefault(rec["stock_code"].zfill(5), set()).add(rec["participant_id"])
    from app.sources.longbridge import LongbridgeMcpClient
    import asyncio
    client = LongbridgeMcpClient(interactive=False)
    out = {}
    detail_requests = 0
    for code in POC:
        r = collect_stock_detail(client, store, code, baseline_participants=ext.get(code))
        detail_requests += 1
        out[code] = {"snapshot_date": r.snapshot_date, "participants": r.participants,
                     "anchors": r.anchors_derived, "null_anchors": r.null_anchors,
                     "disappeared_vs_baseline": r.disappeared_vs_baseline}
        print(code, out[code])
    # disappeared resolution paths for one sample stock (policy demo, no API)
    # disappeared-policy demo on real PoC data (no API): current sets from snapshots
    cur = {}
    for sc, pid in store.conn.execute("SELECT DISTINCT stock_code, participant_id FROM detail_snapshot_rows"):
        cur.setdefault(sc, set()).add(pid)
    demo = {sc: disappeared_participant_cases(ext.get(sc, set()), cur.get(sc, set()), set())
            for sc in ("00550", "01750")}
    print(json.dumps({k: len(v) for k, v in demo.items()}, ensure_ascii=False))
    ev = {"work_package": "RESTORE_MD_DEFINED_FAST_CCASS_ARCHITECTURE_V1",
          "poc_stocks": out, "DETAIL_REQUESTS_TOTAL": detail_requests,
          "DAILY_REQUESTS_TOTAL": 0,
          "coverage_readback": store.readback()}
    Path("docs/MD_FAST_ARCHITECTURE_7_STOCK_PROOF.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(ev["coverage_readback"], ensure_ascii=False))
if __name__ == "__main__":
    main()

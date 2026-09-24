"""CCASS research surfaces — read-only adapters over the local archives.

Sources (both local, both complete):
- webbsite_full.sqlite : Webb archive 2007→2025-12 (holdings c1=issueID, c2=partID,
  c3=holding, c4=atDate; participants partID/ccassID/partName)
- gap_canonical.sqlite : gap pack 2025-12→2026-07 (stockCode/issueID mapping!)

Honest semantics: UNKNOWN never becomes zero; missing != no holdings;
resolved_source_date explicit; issued-share denominators UNKNOWN when missing.
"""
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

from app.doctor.models import (
    CcassChangeRow,
    CcassChangesResult,
    CcassConcentration,
    CcassHoldingRow,
    CcassHoldingsResult,
    DataQualityStatus,
    MarketActivity,
    ParticipantHistoryPoint,
    ParticipantHistoryResult,
    PositionStatus,
)

WEBB_DB = r"C:\Users\Joe Lau\.zcode\workspace\default\webbsite_full.sqlite"
GAP_DB = r"C:\Users\Joe Lau\.zcode\workspace\default\gap_canonical.sqlite"


def _ro(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


class CcassArchive:
    def __init__(self, webb_db: str = WEBB_DB, gap_db: str = GAP_DB):
        self.webb_db = webb_db
        self.gap_db = gap_db
        self._issue_map: dict[str, str] | None = None  # 5-digit code -> issueID

    def issue_map(self) -> dict[str, str]:
        """stockCode(5-digit) → issueID, from the gap pack (3,070 stocks)."""
        if self._issue_map is None:
            con = _ro(self.gap_db)
            self._issue_map = {
                str(r["stockCode"]).zfill(5): str(r["issueID"])
                for r in con.execute("SELECT DISTINCT stockCode, issueID FROM holdings")
            }
            con.close()
        return self._issue_map

    def issue_id(self, stock_code: str) -> Optional[str]:
        return self.issue_map().get(str(stock_code).zfill(5))

    # ---------- SURFACE 6: holdings by date ----------

    def get_ccass_holdings(self, stock_code: str, holdings_date: date) -> CcassHoldingsResult:
        issue_id = self.issue_id(stock_code)
        if issue_id is None:
            return CcassHoldingsResult(
                stock_code=stock_code, requested_date=holdings_date,
                data_quality=DataQualityStatus.UNKNOWN,
            )
        con = _ro(self.webb_db)
        rows = con.execute(
            "SELECT c2, c3 FROM holdings WHERE c1=? AND c4=? ORDER BY c3 DESC",
            (issue_id, holdings_date.isoformat()),
        ).fetchall()
        resolved: date = holdings_date
        dq = DataQualityStatus.VERIFIED
        if not rows:
            nearest = con.execute(
                "SELECT MAX(c4) FROM holdings WHERE c1=? AND c4<=?",
                (issue_id, holdings_date.isoformat()),
            ).fetchone()[0]
            if nearest:
                resolved = date.fromisoformat(nearest)
                dq = DataQualityStatus.PARTIAL
            else:
                dq = DataQualityStatus.UNKNOWN
        con.close()
        out_rows = [
            CcassHoldingRow(
                participant_id=str(r[0]),
                share_quantity=int(r[1]),
                position_status=PositionStatus.VALID,
                source_reference=f"webbsite_full:holdings issue={issue_id} date={resolved.isoformat()}",
            )
            for r in rows
        ]
        return CcassHoldingsResult(
            stock_code=stock_code,
            requested_date=holdings_date,
            resolved_source_date=resolved,
            rows=out_rows,
            data_quality=dq,
        )

    # ---------- SURFACE 7: participant history ----------

    def get_participant_history(self, stock_code: str, participant_id: str,
                                start: date, end: date) -> ParticipantHistoryResult:
        issue_id = self.issue_id(stock_code)
        points: list[ParticipantHistoryPoint] = []
        if issue_id is not None:
            con = _ro(self.webb_db)
            rows = con.execute(
                "SELECT c4, c3 FROM holdings WHERE c1=? AND c2=? AND c4 BETWEEN ? AND ? ORDER BY c4",
                (issue_id, participant_id, start.isoformat(), end.isoformat()),
            ).fetchall()
            con.close()
            prev = None
            for r in rows:
                d = date.fromisoformat(r[0])
                anomaly = None
                if prev is not None and (d - prev).days > 1:
                    anomaly = "GAP_IN_OBSERVATION"
                points.append(ParticipantHistoryPoint(holdings_date=d, share_quantity=int(r[1]), anomaly=anomaly))
                prev = d
        return ParticipantHistoryResult(
            stock_code=stock_code, participant_id=participant_id,
            start_date=start, end_date=end, points=points, anomalies_preserved=True,
        )

    # ---------- SURFACE 8: changes (derived from consecutive dated snapshots) ----------

    def get_ccass_changes(self, stock_code: str, start: date, end: date) -> CcassChangesResult:
        issue_id = self.issue_id(stock_code)
        rows_out: list[CcassChangeRow] = []
        if issue_id is not None:
            con = _ro(self.webb_db)
            snaps = con.execute(
                "SELECT DISTINCT c4 FROM holdings WHERE c1=? AND c4 BETWEEN ? AND ? ORDER BY c4",
                (issue_id, start.isoformat(), end.isoformat()),
            ).fetchall()
            prev_date = None
            prev_map: dict[str, int] = {}
            for (dstr,) in snaps:
                d = date.fromisoformat(dstr)
                cur = con.execute(
                    "SELECT c2, c3 FROM holdings WHERE c1=? AND c4=?",
                    (issue_id, dstr),
                ).fetchall()
                cur_map = {r[0]: int(r[1]) for r in cur}
                if prev_map:
                    for pid, after in sorted(cur_map.items()):
                        before = prev_map.get(pid)
                        if before is not None and after != before:
                            rows_out.append(CcassChangeRow(
                                holdings_date=d, estimated_trade_date=None,
                                participant_id=pid, before=before, after=after,
                                change=after - before,
                                change_percent=round((after - before) / before * 100, 4) if before else None,
                            ))
                    for pid, before in prev_map.items():
                        if pid not in cur_map and before:
                            rows_out.append(CcassChangeRow(
                                holdings_date=d, participant_id=pid, before=before, after=0,
                                change=-before, change_percent=-100.0,
                            ))
                prev_map = cur_map
                prev_date = d
            con.close()
        return CcassChangesResult(stock_code=stock_code, start_date=start, end_date=end, rows=rows_out)

    # ---------- SURFACE 9: concentration ----------

    def get_ccass_concentration(self, stock_code: str, holdings_date: date) -> CcassConcentration:
        h = self.get_ccass_holdings(stock_code, holdings_date)
        shares = [r.share_quantity for r in h.rows if r.share_quantity is not None]
        total = sum(shares) or None
        srt = sorted(shares, reverse=True)
        top = lambda n: sum(srt[:n]) if len(srt) >= n else (sum(srt) if srt else None)
        issued = None  # honest: issued-share denominator unavailable in these tables
        out = CcassConcentration(
            stock_code=stock_code, holdings_date=h.resolved_source_date or holdings_date,
            issued_shares=None, total_in_ccass=total,
            top_1=srt[0] if srt else None,
            top_5=top(5), top_10=top(10),
            participant_count=len(h.rows) or None,
            issued_shares_unavailable=issued is None,
        )
        if total:
            out.top1_pct_of_ccass = round((out.top_1 or 0) / total * 100, 4)
            out.top5_pct_of_ccass = round((out.top_5 or 0) / total * 100, 4)
            out.top10_pct_of_ccass = round((out.top_10 or 0) / total * 100, 4)
        if issued is None:
            out.issued_shares_unavailable = True
        return out

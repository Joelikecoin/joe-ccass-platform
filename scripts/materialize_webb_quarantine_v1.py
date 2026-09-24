"""Materialize lineage-preserving quarantine windows for negative Webb rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import subprocess
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


def _git_version() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--negative-ledger", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-sha256", default="")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source_hash = args.source_sha256.upper() or _sha256(args.database)
    code_version = _git_version()
    connection = sqlite3.connect(f"file:{args.database.resolve().as_posix()}?mode=ro", uri=True)
    with args.negative_ledger.open(encoding="utf-8-sig", newline="") as handle:
        negatives = list(csv.DictReader(handle))
    max_dates = {
        str(issue): str(max_date)
        for issue, max_date in connection.execute("SELECT c2,MAX(c1) FROM dailylog GROUP BY c2")
    }
    raw_windows: list[dict[str, object]] = []
    for index, negative in enumerate(negatives, start=1):
        issue = str(negative["issueID"])
        part = str(negative["partID"])
        rowid = int(str(negative["source_record_reference"]).split("rowid=")[1].split(";")[0])
        rows = list(connection.execute(
            "SELECT rowid,c1,c2,c3,c4 FROM holdings WHERE rowid BETWEEN ? AND ? ORDER BY rowid",
            (max(1, rowid - 5000), rowid + 5000),
        ))
        # The source table's native order is issue, participant, date; use the
        # ledger's rowid window and identity fields to isolate this pair.
        pair_rows = [row for row in rows if str(row[1]) == part and str(row[2]) == issue]
        negative_index = next(i for i, row in enumerate(pair_rows) if int(row[0]) == rowid)
        prior = next((row for row in reversed(pair_rows[:negative_index]) if int(row[3]) >= 0), None)
        following = next((row for row in pair_rows[negative_index + 1 :] if int(row[3]) >= 0), None)
        start = date.fromisoformat(str(negative["atDate"]))
        next_date = date.fromisoformat(str(following[4])) if following else None
        end = next_date - timedelta(days=1) if next_date else date.fromisoformat(max_dates[issue])
        raw_windows.append({
            "anomaly_id": f"NEG-{issue}-{part}-{negative['atDate']}-{rowid}",
            "issueID": issue,
            "partID": part,
            "negative_atDate": negative["atDate"],
            "raw_negative_value": negative["holding_value"],
            "previous_valid_date": prior[4] if prior else "",
            "previous_valid_value": int(prior[3]) if prior else "",
            "next_valid_date": following[4] if following else "",
            "next_valid_value": int(following[3]) if following else "",
            "quarantine_valid_from": start.isoformat(),
            "quarantine_valid_to": end.isoformat(),
            "quarantine_status": "OPEN_ENDED" if following is None else "CLOSED_BEFORE_NEXT_VALID",
            "source_reference": negative["source_record_reference"],
            "source_hash": source_hash,
            "forensic_report_reference": "WEBB_NEGATIVE_HOLDINGS_FORENSIC_LEDGER_V2.csv",
            "code_version": code_version,
            "origin_anomaly_id": f"NEG-{issue}-{part}-{negative['atDate']}-{rowid}",
        })

    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in raw_windows:
        grouped[(str(row["issueID"]), str(row["partID"]))].append(row)
    merged: list[dict[str, object]] = []
    for key, rows in grouped.items():
        rows.sort(key=lambda row: (str(row["quarantine_valid_from"]), str(row["quarantine_valid_to"])))
        current: dict[str, object] | None = None
        for row in rows:
            start = date.fromisoformat(str(row["quarantine_valid_from"]))
            end = date.fromisoformat(str(row["quarantine_valid_to"]))
            if current is None or start > date.fromisoformat(str(current["quarantine_valid_to"])) + timedelta(days=1):
                current = {**row, "merged_window_id": f"Q-{key[0]}-{key[1]}-{row['quarantine_valid_from']}", "origin_anomaly_ids": str(row["anomaly_id"])}
                merged.append(current)
            else:
                current["quarantine_valid_to"] = max(date.fromisoformat(str(current["quarantine_valid_to"])), end).isoformat()
                current["origin_anomaly_ids"] = f"{current['origin_anomaly_ids']};{row['anomaly_id']}"
                if str(row["quarantine_status"]) == "OPEN_ENDED":
                    current["quarantine_status"] = "OPEN_ENDED"

    dates_by_issue: dict[str, list[date]] = defaultdict(list)
    issue_list = sorted({str(row["issueID"]) for row in merged})
    placeholders = ",".join("?" for _ in issue_list)
    for issue, source_date in connection.execute(
        f"SELECT c2,c1 FROM dailylog WHERE c2 IN ({placeholders}) ORDER BY c2,c1", issue_list
    ):
        dates_by_issue[str(issue)].append(date.fromisoformat(str(source_date)))
    for row in merged:
        start = date.fromisoformat(str(row["quarantine_valid_from"]))
        end = date.fromisoformat(str(row["quarantine_valid_to"]))
        row["quarantined_trading_days"] = sum(start <= day <= end for day in dates_by_issue[str(row["issueID"])])
        row["quarantined_position_states"] = row["quarantined_trading_days"]

    fields = list(raw_windows[0]) if raw_windows else []
    with (args.output_dir / "WEBB_QUARANTINE_RAW_WINDOWS_V1.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(raw_windows)
    merged_fields = list(merged[0]) if merged else []
    with (args.output_dir / "WEBB_QUARANTINE_MERGED_WINDOWS_V1.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=merged_fields)
        writer.writeheader()
        writer.writerows(merged)
    total_days = sum(int(row["quarantined_trading_days"]) for row in merged)
    total_states = sum(int(row["quarantined_position_states"]) for row in merged)
    summary = {
        "raw_negative_count": len(raw_windows),
        "raw_quarantine_window_count": len(raw_windows),
        "merged_quarantine_window_count": len(merged),
        "quarantined_security_count": len({str(row["issueID"]) for row in merged}),
        "quarantined_participant_count": len({str(row["partID"]) for row in merged}),
        "total_quarantined_trading_days": total_days,
        "total_quarantined_position_states": total_states,
        "source_sha256": source_hash,
        "code_version": code_version,
        "all_92_negatives_classified": len(raw_windows) == 92,
        "unhandled_negative_count": 0,
    }
    (args.output_dir / "WEBB_QUARANTINE_SUMMARY_V1.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

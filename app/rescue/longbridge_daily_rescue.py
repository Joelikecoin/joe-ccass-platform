"""LONGBRIDGE_CCASS_DAILY_HISTORY_EMERGENCY_RESCUE_V2_ZC — rescue engine.

Preserves Longbridge broker_holding_daily raw history into an isolated durable
store (no production canonical merge; Codex stays production authority).

Verified runtime proof (2026-09-25, this machine, live MCP):
    broker_holding_daily("700.HK","A00003") -> 40 rows, 2026.07.31 -> 2026.09.24
    broker_holding_daily("700.HK","B01955") -> 40 rows, 2026.07.31 -> 2026.09.24
Symbol normalization rule (sample-verified live):
    canonical symbol = code with leading zeros stripped + ".HK"
    (3.HK/5.HK/6.HK/2318.HK/3888.HK/700.HK/9618.HK all return data;
     "00700.HK" is NOT assumed valid)
Date values arrive as "2026.09.24" and are stored ISO "2026-09-24".
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

RESCUE_ANCHOR_DATE = "2026-07-31"

MIGRATION = """
CREATE TABLE IF NOT EXISTS raw_daily (
    stock_code TEXT NOT NULL,
    symbol TEXT NOT NULL,
    participant_id TEXT NOT NULL,
    date TEXT NOT NULL,
    holding INTEGER,
    ratio REAL,
    chg REAL,
    source_system TEXT NOT NULL DEFAULT 'Longbridge',
    source_surface TEXT NOT NULL DEFAULT 'broker_holding_daily',
    fetched_at TEXT NOT NULL,
    raw_payload_hash TEXT NOT NULL,
    data_quality_status TEXT NOT NULL DEFAULT 'RECOVERED_CONFIRMED',
    PRIMARY KEY (stock_code, participant_id, date)
);
CREATE TABLE IF NOT EXISTS holding_detail_snapshots (
    stock_code TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS conflicts (
    conflict_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    participant_id TEXT NOT NULL,
    date TEXT NOT NULL,
    existing_json TEXT NOT NULL,
    incoming_json TEXT NOT NULL,
    detected_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS errors (
    error_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT,
    participant_id TEXT,
    kind TEXT NOT NULL,
    detail TEXT NOT NULL,
    occurred_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    state_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def canonical_symbol(code: str) -> str:
    """00003 -> 3.HK ; 02318 -> 2318.HK ; 700 -> 700.HK (live-verified rule)."""
    digits = str(code).strip().split(".")[0].lstrip("0") or "0"
    return f"{digits}.HK"


def stock_code_from_symbol(symbol: str) -> str:
    digits = symbol.split(".")[0]
    return digits.zfill(5)


def parse_lb_date(raw: str) -> str:
    """'2026.09.24' -> '2026-09-24'."""
    return raw.strip().replace(".", "-")


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


@dataclass
class StockResult:
    stock_code: str
    symbol: str
    participant_queries_attempted: int = 0
    participant_queries_nonempty: int = 0
    participant_queries_empty: int = 0
    participant_queries_failed: int = 0
    rows_saved: int = 0
    earliest_date: Optional[str] = None
    latest_date: Optional[str] = None
    detail_captured: bool = False


class RescueStore:
    """Isolated raw rescue store (SQLite). Never merges into production."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.executescript(MIGRATION)
        self.conn.commit()

    # -- capture ------------------------------------------------------------
    def capture_detail(self, stock_code: str, symbol: str, payload: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO holding_detail_snapshots VALUES (?,?,?,?)",
            (stock_code, symbol, datetime.now(timezone.utc).isoformat(),
             json.dumps(payload, ensure_ascii=False)),
        )
        self.conn.commit()

    def insert_daily_row(self, row: dict) -> str:
        """Returns 'saved' | 'duplicate_identical' | 'conflict'."""
        cur = self.conn.execute(
            "SELECT holding, ratio, chg, raw_payload_hash FROM raw_daily "
            "WHERE stock_code=? AND participant_id=? AND date=?",
            (row["stock_code"], row["participant_id"], row["date"]),
        )
        existing = cur.fetchone()
        if existing is None:
            self.conn.execute(
                "INSERT INTO raw_daily VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (row["stock_code"], row["symbol"], row["participant_id"], row["date"],
                 row["holding"], row["ratio"], row["chg"], row["source_system"],
                 row["source_surface"], row["fetched_at"], row["raw_payload_hash"],
                 row["data_quality_status"]),
            )
            self.conn.commit()
            return "saved"
        same = (existing[0] == row["holding"] and existing[1] == row["ratio"]
                and existing[2] == row["chg"])
        if same:
            return "duplicate_identical"
        self.conn.execute(
            "INSERT INTO conflicts (stock_code, participant_id, date, existing_json, "
            "incoming_json, detected_at) VALUES (?,?,?,?,?,?)",
            (row["stock_code"], row["participant_id"], row["date"],
             json.dumps({"holding": existing[0], "ratio": existing[1], "chg": existing[2]}),
             json.dumps({"holding": row["holding"], "ratio": row["ratio"], "chg": row["chg"]}),
             datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()
        return "conflict"

    def record_error(self, stock_code: Optional[str], participant_id: Optional[str],
                     kind: str, detail: str) -> None:
        self.conn.execute(
            "INSERT INTO errors (stock_code, participant_id, kind, detail, occurred_at) "
            "VALUES (?,?,?,?,?)",
            (stock_code, participant_id, kind, detail[:500],
             datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    # -- checkpoint -----------------------------------------------------------
    def save_checkpoint(self, state: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO checkpoints VALUES (1,?,?)",
            (json.dumps(state, ensure_ascii=False), datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    def load_checkpoint(self) -> Optional[dict]:
        row = self.conn.execute("SELECT state_json FROM checkpoints WHERE id=1").fetchone()
        return json.loads(row[0]) if row else None

    # -- readback -------------------------------------------------------------
    def readback(self) -> dict:
        q = lambda sql: self.conn.execute(sql).fetchone()[0]
        return {
            "TOTAL_ROWS": q("SELECT COUNT(*) FROM raw_daily"),
            "DISTINCT_STOCKS": q("SELECT COUNT(DISTINCT stock_code) FROM raw_daily"),
            "DISTINCT_PARTICIPANTS": q("SELECT COUNT(DISTINCT participant_id) FROM raw_daily"),
            "DISTINCT_DATES": q("SELECT COUNT(DISTINCT date) FROM raw_daily"),
            "EARLIEST_DATE": q("SELECT MIN(date) FROM raw_daily"),
            "LATEST_DATE": q("SELECT MAX(date) FROM raw_daily"),
            "DUPLICATE_IDENTICAL_COUNT": 0,  # idempotent skips never stored; counted in runner stats
            "CONFLICTING_DUPLICATE_COUNT": q("SELECT COUNT(*) FROM conflicts"),
            "ERROR_COUNT": q("SELECT COUNT(*) FROM errors"),
        }

    def stock_readback(self, stock_code: str, participant_id: str) -> dict:
        row = self.conn.execute(
            "SELECT COUNT(*), MIN(date), MAX(date) FROM raw_daily "
            "WHERE stock_code=? AND participant_id=?",
            (stock_code, participant_id),
        ).fetchone()
        return {"rows": row[0], "earliest": row[1], "latest": row[2]}

    def coverage_by_date(self) -> list:
        return self.conn.execute(
            "SELECT date, COUNT(DISTINCT stock_code), COUNT(DISTINCT participant_id), "
            "COUNT(*) FROM raw_daily GROUP BY date ORDER BY date"
        ).fetchall()

    def coverage_by_stock(self) -> list:
        return self.conn.execute(
            "SELECT stock_code, MIN(symbol), MIN(date), MAX(date), COUNT(DISTINCT date), "
            "COUNT(DISTINCT participant_id) FROM raw_daily GROUP BY stock_code ORDER BY stock_code"
        ).fetchall()

    def august_gap_stats(self, start: str = "2026-08-01", end: str = "2026-09-08") -> dict:
        row = self.conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT stock_code) FROM raw_daily "
            "WHERE date BETWEEN ? AND ?", (start, end),
        ).fetchone()
        return {"AUG_01_TO_SEP_08_ROWS": row[0], "AUG_01_TO_SEP_08_STOCK_COUNT": row[1]}


class EmptyKind:
    VALID_EMPTY_FOR_THIS_PARTICIPANT = "VALID_EMPTY_FOR_THIS_PARTICIPANT"
    INVALID_SYMBOL_FORMAT = "INVALID_SYMBOL_FORMAT"
    INVALID_PARTICIPANT_ID = "INVALID_PARTICIPANT_ID"
    RUNTIME_API_EMPTY = "RUNTIME/API_EMPTY"
    PARSER_EMPTY = "PARSER_EMPTY"
    UNKNOWN = "UNKNOWN"


def classify_empty(symbol: str, participant_id: str, exc: Optional[Exception],
                   detail_participants: set) -> str:
    if exc is not None:
        text = str(exc).lower()
        if "symbol" in text or "invalid" in text and "participant" not in text:
            return EmptyKind.INVALID_SYMBOL_FORMAT
        return EmptyKind.UNKNOWN
    if not participant_id or not participant_id.strip():
        return EmptyKind.INVALID_PARTICIPANT_ID
    if participant_id in detail_participants:
        # listed in current detail but daily returns nothing -> may be window-empty
        return EmptyKind.VALID_EMPTY_FOR_THIS_PARTICIPANT
    return EmptyKind.RUNTIME_API_EMPTY


def _row_from_payload(stock_code: str, symbol: str, participant_id: str,
                      item: dict, fetched_at: str) -> Optional[dict]:
    raw_date = str(item.get("date", "")).strip()
    if not raw_date:
        return None
    iso = parse_lb_date(raw_date)
    if iso < RESCUE_ANCHOR_DATE:
        return None  # keep anchor overlap row, drop pre-window history
    def _num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None
    holding = item.get("holding")
    return {
        "stock_code": stock_code,
        "symbol": symbol,
        "participant_id": participant_id,
        "date": iso,
        "holding": int(float(holding)) if holding not in (None, "") else None,
        "ratio": _num(item.get("ratio")),
        "chg": _num(item.get("chg")),
        "source_system": "Longbridge",
        "source_surface": "broker_holding_daily",
        "fetched_at": fetched_at,
        "raw_payload_hash": _hash(item),
        "data_quality_status": "RECOVERED_CONFIRMED",
    }


def _extract_list(payload: Any) -> list:
    if isinstance(payload, dict):
        for key in ("list", "rows", "data"):
            if key in payload and isinstance(payload[key], list):
                return payload[key]
        return []
    if isinstance(payload, list):
        return payload
    return []


def _call(client: Any, method: str, *args):
    """Client methods may be sync or async; engine accepts both."""
    import asyncio
    result = getattr(client, method)(*args)
    if hasattr(result, "__await__"):
        return asyncio.run(result)
    return result


def rescue_stock(client: Any, store: RescueStore, code: str,
                 extra_participants: Iterable[str] = (),
                 max_retries: int = 3) -> StockResult:
    """Extract daily history for one stock across the participant union."""
    symbol = canonical_symbol(code)
    stock_code = stock_code_from_symbol(symbol)
    result = StockResult(stock_code=stock_code, symbol=symbol)
    fetched_at = datetime.now(timezone.utc).isoformat()

    participants: list[str] = []
    detail_participants: set = set()
    try:
        detail = _extract_list(_call(client, 'broker_holding_detail', symbol))
        detail_payload = {"symbol": symbol, "participants": detail}
        store.capture_detail(stock_code, symbol, detail_payload)
        result.detail_captured = True
        for item in detail:
            pid = str(item.get("parti_number") or item.get("participant_id") or "").strip()
            if pid:
                participants.append(pid)
                detail_participants.add(pid)
    except Exception as exc:  # detail failure must not block daily rescue
        store.record_error(stock_code, None, "DETAIL_FAILED",
                           f"{type(exc).__name__}: {exc}")

    for pid in extra_participants:
        if pid and pid not in participants:
            participants.append(pid)

    for pid in participants:
        result.participant_queries_attempted += 1
        saved = 0
        ok = False
        for attempt in range(max_retries):
            try:
                payload = _call(client, 'broker_holding_daily', symbol, pid)
            except Exception as exc:
                if attempt == max_retries - 1:
                    store.record_error(stock_code, pid, "DAILY_FAILED",
                                       f"{type(exc).__name__}: {exc}")
                    result.participant_queries_failed += 1
                    continue
                continue
            items = _extract_list(payload)
            if not items:
                kind = classify_empty(symbol, pid, None, detail_participants)
                store.record_error(stock_code, pid, f"EMPTY:{kind}",
                                   "broker_holding_daily returned no rows")
                result.participant_queries_empty += 1
                ok = True
                break
            for item in items:
                row = _row_from_payload(stock_code, symbol, pid, item, fetched_at)
                if row is None:
                    continue
                outcome = store.insert_daily_row(row)
                if outcome == "saved":
                    saved += 1
            result.participant_queries_nonempty += 1
            ok = True
            break
        if not ok and result.participant_queries_failed == 0:
            result.participant_queries_failed += 1
        result.rows_saved += saved

    row = store.conn.execute(
        "SELECT COUNT(*), MIN(date), MAX(date) FROM raw_daily WHERE stock_code=?",
        (stock_code,)).fetchone()
    result.earliest_date, result.latest_date = row[1], row[2]
    return result


def build_universe_from_turso(pipeline_url: str, token: str) -> dict:
    """Priority 3 universe: canonical production `stocks` table.

    Priority 1 (extension dataset) and 2 (full security master) are home-machine
    assets and are NOT assumed available here; the runner records that honestly.
    """
    import httpx
    resp = httpx.post(
        pipeline_url.rstrip("/") + "/v2/pipeline",
        headers={"Authorization": f"Bearer {token}"},
        json={"requests": [{"type": "execute",
                            "stmt": {"sql": "SELECT code FROM stocks ORDER BY code"}}]},
        timeout=30,
    )
    res = resp.json()["results"][0]
    if res["type"] == "error":
        raise RuntimeError(f"universe query failed: {res['error']['message']}")
    codes = []
    for row in res["response"]["result"]["rows"]:
        val = row[0]
        if isinstance(val, dict):  # Turso pipeline value envelope
            val = val.get("value")
        codes.append(str(val))
    return {"STOCK_UNIVERSE_COUNT": len(codes),
            "universe_priority": "3_production_stocks_table",
            "PRIORITY1_EXTENSION_UNIVERSE_AVAILABLE": False,
            "codes": codes}

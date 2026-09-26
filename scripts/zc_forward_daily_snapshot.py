"""Forward daily CCASS snapshot job (16:35 HKT, Mon-Fri) — FAST detail-only path.

One active stock = ONE broker_holding_detail call. broker_holding_daily is
NEVER used by this job.

Single-instance safety: an exclusive lock file guards the write target. If a
live compatible CCASS production writer owns the lock, this job DEFERS (exit 0,
logged) — it never kills or competes with a valid production job. A stale lock
(owner PID dead) is taken over.

Resumable: progress checkpoint after every 25 stocks; rerun skips stocks that
already have a snapshot row for today's snapshot date.

Usage:
  python -m scripts.zc_forward_daily_snapshot            # full universe
  python -m scripts.zc_forward_daily_snapshot --limit 2  # bounded smoke test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

UNIVERSE = Path("data/extension_universe_2026_07.json")
DB = Path("data/fast_detail_snapshots.sqlite")
LOCK = Path("data/forward_snapshot.lock")
LOG_DIR = Path("logs")
CHECKPOINT_EVERY = 25


def _pid_alive(pid: int) -> bool:
    """Windows-safe liveness probe (never uses os.kill — on Windows a non-zero
    signal would TERMINATE the target process)."""
    import ctypes
    k32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return False
    try:
        code = ctypes.c_ulong()
        if k32.GetExitCodeProcess(h, ctypes.byref(code)):
            return code.value == STILL_ACTIVE
        return False
    finally:
        k32.CloseHandle(h)


def acquire_lock(lock_path: Path) -> Optional[int]:
    """Exclusive create; stale (dead-PID) locks are taken over. Returns my pid or None."""
    for _ in range(2):
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return os.getpid()
        except FileExistsError:
            try:
                owner = int(lock_path.read_text().strip())
                if _pid_alive(owner):
                    return None  # live writer owns it — defer
                lock_path.unlink(missing_ok=True)  # stale lock, take over
            except (ValueError, OSError):
                lock_path.unlink(missing_ok=True)
    return None


def already_done_today(store, code: str) -> bool:
    """Done = already fetched in THIS job's calendar day (API snapshot date can
    legitimately stay on the previous trading day — fetch date decides)."""
    today = datetime.now().strftime("%Y-%m-%d")
    row = store.conn.execute(
        "SELECT fetched_at FROM detail_snapshot_rows WHERE stock_code=? LIMIT 1",
        (code,)).fetchone()
    return bool(row and row[0][:10] == today)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="bounded smoke test")
    ap.add_argument("--db", default=str(DB))
    args = ap.parse_args()
    load_dotenv = __import__("dotenv").load_dotenv
    load_dotenv()

    LOG_DIR.mkdir(exist_ok=True)
    log_path = LOG_DIR / f"forward_snapshot_{datetime.now():%Y%m%d}.log"
    def log(msg):
        line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
        print(line, flush=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    pid = acquire_lock(LOCK)
    if pid is None:
        log("DEFER: another live CCASS production writer owns the lock — not competing")
        return 0
    try:
        from app.rescue.fast_detail_collector import FastDetailStore, collect_stock_detail
        from app.sources.longbridge import LongbridgeMcpClient
        store = FastDetailStore(Path(args.db))
        codes = json.load(open(UNIVERSE, encoding="utf-8"))
        if args.limit:
            codes = codes[: args.limit]
        log(f"start universe={len(codes)} db={args.db}")
        client = LongbridgeMcpClient(interactive=False)
        done = failed = 0
        t0 = time.time()
        for i, code in enumerate(codes, 1):
            try:
                if already_done_today(store, code):
                    done += 1
                    continue
                collect_stock_detail(client, store, code)
                done += 1
            except Exception as exc:
                failed += 1
                log(f"FAIL {code}: {type(exc).__name__}: {str(exc)[:120]}")
            if i % CHECKPOINT_EVERY == 0:
                log(f"checkpoint {i}/{len(codes)} done={done} failed={failed} "
                    f"elapsed={time.time()-t0:.0f}s")
        log(f"end done={done} failed={failed} elapsed={time.time()-t0:.0f}s "
            f"readback={json.dumps(store.readback(), ensure_ascii=False)}")
        return 0
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())

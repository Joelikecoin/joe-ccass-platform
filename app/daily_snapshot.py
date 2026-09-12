from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas_market_calendars as mcal

from app.services.longbridge import LongbridgeHoldingsService
from ccass_core.normalize import normalize_stock_code

logger = logging.getLogger(__name__)
_HK_TZ = ZoneInfo("Asia/Hong_Kong")
_DAILY_CALENDAR = mcal.get_calendar("XHKG")

# Reference-approved packaged watchlist. Research is intentionally excluded.
LSHAPE79 = (
    "01449",
    "02497",
    "01871",
    "01582",
    "01927",
    "01941",
    "01433",
    "01843",
    "02455",
    "01615",
    "01284",
    "02129",
    "01407",
    "01545",
    "01650",
    "01955",
    "02263",
    "01455",
    "01960",
    "01793",
    "01947",
    "02347",
    "02457",
    "01832",
    "01156",
)
CAIJI = (
    "06162",
    "01869",
    "00550",
    "01449",
    "08232",
    "03321",
    "01613",
    "08483",
    "09978",
    "02503",
    "08201",
    "06610",
    "01536",
    "08283",
    "08121",
    "08496",
    "01323",
    "00033",
    "01592",
    "06939",
    "00256",
    "00397",
    "08178",
    "02699",
    "08611",
    "01676",
    "01417",
    "01657",
)
DAILY_GROUPS = {"lshape79": LSHAPE79, "caiji": CAIJI}


def daily_watchlist(groups: tuple[str, ...] = ("lshape79", "caiji")) -> tuple[str, ...]:
    return tuple(dict.fromkeys(code for group in groups for code in DAILY_GROUPS[group]))


def hkt_now() -> datetime:
    return datetime.now(_HK_TZ)


def _calendar_dates(day: date) -> set[date]:
    schedule = _DAILY_CALENDAR.schedule(start_date=day, end_date=day)
    return {stamp.date() for stamp in schedule.index}


def next_trading_day(day: date) -> date:
    candidate = day + timedelta(days=1)
    for _ in range(14):
        if _calendar_dates(candidate):
            return candidate
        candidate += timedelta(days=1)
    raise RuntimeError("XHKG calendar did not provide a next trading day")


def is_trading_day(day: date) -> bool:
    return bool(_calendar_dates(day))


async def run_daily_snapshot(
    stocks: tuple[str, ...] | None = None,
    *,
    service: LongbridgeHoldingsService | None = None,
    dry_run: bool = False,
    pacing_seconds: float = 1.5,
) -> dict[str, object]:
    started = time.monotonic()
    job_id = uuid.uuid4().hex
    requested = stocks or daily_watchlist()
    codes = tuple(dict.fromkeys(normalize_stock_code(code) for code in requested))
    now = hkt_now()
    if not is_trading_day(now.date()):
        return {
            "job_id": job_id,
            "status": "skipped_holiday",
            "date_hkt": now.date().isoformat(),
            "next_trading_day": next_trading_day(now.date()).isoformat(),
            "total": len(codes),
            "succeeded": 0,
            "failed": 0,
            "skipped": len(codes),
            "current_code": None,
            "elapsed_s": round(time.monotonic() - started, 3),
            "results": [],
        }
    if dry_run:
        return {
            "job_id": job_id,
            "status": "complete",
            "date_hkt": now.date().isoformat(),
            "total": len(codes),
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "current_code": None,
            "elapsed_s": round(time.monotonic() - started, 3),
            "dry_run": True,
            "results": [],
        }

    collector = service or LongbridgeHoldingsService()
    results: list[dict[str, object]] = []
    for index, code in enumerate(codes):
        item_started = time.monotonic()
        status = "ERROR"
        error = None
        source_date = None
        rows = 0
        for attempt in range(2):
            try:
                response = await asyncio.wait_for(collector.fetch_and_persist(code), timeout=60)
                if response.metadata.holdings_date is None:
                    raise RuntimeError("source omitted authoritative holdings date")
                source_date = response.metadata.holdings_date.isoformat()
                rows = len(response.holdings)
                status = "COMPLETE"
                error = None
                break
            except Exception as exc:
                error = type(exc).__name__
                if attempt == 0:
                    await asyncio.sleep(1.0)
        item = {
            "stock_code": code,
            "status": status,
            "source_date": source_date,
            "rows": rows,
            "persist_status": "persisted" if status == "COMPLETE" else "not_persisted",
            "duration_s": round(time.monotonic() - item_started, 3),
            "error": error,
        }
        results.append(item)
        succeeded = sum(result["status"] == "COMPLETE" for result in results)
        logger.info(
            "daily snapshot job=%s stock=%s status=%s source_date=%s rows=%s elapsed_s=%s",
            job_id,
            code,
            status,
            source_date,
            rows,
            item["duration_s"],
        )
        logger.info(
            "daily snapshot progress job=%s total=%s succeeded=%s failed=%s current_code=%s elapsed_s=%s",
            job_id,
            len(codes),
            succeeded,
            len(results) - succeeded,
            code,
            round(time.monotonic() - started, 3),
        )
        if index + 1 < len(codes):
            await asyncio.sleep(max(1.5, pacing_seconds))
    succeeded = sum(result["status"] == "COMPLETE" for result in results)
    failed = len(results) - succeeded
    return {
        "job_id": job_id,
        "status": "complete" if failed == 0 else "partial" if succeeded else "error",
        "date_hkt": now.date().isoformat(),
        "total": len(codes),
        "succeeded": succeeded,
        "failed": failed,
        "skipped": 0,
        "current_code": None,
        "elapsed_s": round(time.monotonic() - started, 3),
        "results": results,
    }

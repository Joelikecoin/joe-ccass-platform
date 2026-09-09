from __future__ import annotations

from pathlib import Path
from datetime import UTC, date, datetime
import asyncio
import json
import os
import time
from typing import Any

from app.config import Settings, get_settings
from app.longbridge_persistence import build_response, persist_response
from app.models import CcassResponse, PriceHistoryMetadata, PriceHistoryResponse, PriceHistoryRow
from app.sources.longbridge import LongbridgeMcpClient, normalize_longbridge_symbol


def _trace(stage: str, *, stock_code: str, started: float | None = None, completed: bool | None = None, status: str = "", exception: str = "", timeout: bool = False) -> None:
    if os.getenv("P0_LONGBRIDGE_TRACE") != "1" or str(stock_code).zfill(5) not in {"06182", "00001"}: return
    payload = {"stage": stage, "stock": str(stock_code).zfill(5), "ts": time.time(), "elapsed_ms": round((time.perf_counter() - started) * 1000, 1) if started is not None else None, "completed": completed, "status": status, "exception_type": exception, "timeout": timeout}
    print("LB_TRACE " + json.dumps(payload, separators=(",", ":")), flush=True)


class LongbridgeHoldingsService:
    def __init__(self, *, settings: Settings | None = None, client: LongbridgeMcpClient | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = client or LongbridgeMcpClient()

    async def get_holdings(self, code: str, limit: int = 15) -> CcassResponse:
        """Gateway adapter for the current Longbridge holdings source."""
        # Keep the complete persisted snapshot; the gateway applies any
        # presentation limit after source selection.
        return await self.fetch_and_persist(code)

    async def fetch_and_persist(self, stock_code: str) -> CcassResponse:
        request_started = time.perf_counter(); _trace("LB_REQUEST_START", stock_code=stock_code, started=request_started, status="started")
        _trace("LB_MCP_CLIENT_CREATE_START", stock_code=stock_code, started=request_started)
        symbol = normalize_longbridge_symbol(stock_code)
        _trace("LB_MCP_CLIENT_CREATE_END", stock_code=stock_code, started=request_started, completed=True, status="ready")
        _trace("LB_NORMALIZE_START", stock_code=stock_code, started=request_started); _trace("LB_NORMALIZE_END", stock_code=stock_code, started=request_started, completed=True, status="symbol_ready")
        detail_started = time.perf_counter(); _trace("LB_BROKER_HOLDING_DETAIL_START", stock_code=stock_code, started=detail_started)
        try: payload = await self.client.broker_holding_detail(symbol)
        except asyncio.TimeoutError as exc: _trace("LB_BROKER_HOLDING_DETAIL_END", stock_code=stock_code, started=detail_started, completed=False, exception=type(exc).__name__, timeout=True); raise
        except Exception as exc: _trace("LB_BROKER_HOLDING_DETAIL_END", stock_code=stock_code, started=detail_started, completed=False, exception=type(exc).__name__); raise
        _trace("LB_BROKER_HOLDING_DETAIL_END", stock_code=stock_code, started=detail_started, completed=True, status="returned")
        static_started = time.perf_counter(); _trace("LB_STATIC_INFO_START", stock_code=stock_code, started=static_started)
        try: issued_shares = await self._issued_shares(symbol)
        except asyncio.TimeoutError as exc: _trace("LB_STATIC_INFO_END", stock_code=stock_code, started=static_started, completed=False, exception=type(exc).__name__, timeout=True); raise
        except Exception as exc: _trace("LB_STATIC_INFO_END", stock_code=stock_code, started=static_started, completed=False, exception=type(exc).__name__); raise
        _trace("LB_STATIC_INFO_END", stock_code=stock_code, started=static_started, completed=True, status="returned")
        parse_started = time.perf_counter(); _trace("LB_PARSE_START", stock_code=stock_code, started=parse_started)
        response = build_response(payload, stock_code=stock_code, issue_id=0, issued_shares=issued_shares)
        _trace("LB_PARSE_END", stock_code=stock_code, started=parse_started, completed=True, status="parsed")
        _trace("LB_VALIDATE_START", stock_code=stock_code, started=parse_started); _trace("LB_VALIDATE_END", stock_code=stock_code, started=parse_started, completed=True, status="validated")
        persist_started = time.perf_counter(); _trace("LB_TURSO_PERSIST_START", stock_code=stock_code, started=persist_started)
        try: persist_response(response, db_path=Path(self.settings.ccass_sqlite_path))
        except Exception as exc: _trace("LB_TURSO_PERSIST_END", stock_code=stock_code, started=persist_started, completed=False, exception=type(exc).__name__); raise
        _trace("LB_TURSO_PERSIST_END", stock_code=stock_code, started=persist_started, completed=True, status="persisted")
        _trace("LB_REQUEST_END", stock_code=stock_code, started=request_started, completed=True, status="success")
        return response

    async def _issued_shares(self, symbol: str) -> int | None:
        payload = await self.client.static_info([symbol])
        items = payload.get("list") or payload.get("items") or payload.get("data") or []
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list) or not items:
            return None
        value = items[0].get("total_shares") if isinstance(items[0], dict) else None
        try:
            parsed = int(float(value)) if value is not None else None
        except (TypeError, ValueError):
            return None
        return parsed if parsed and parsed > 0 else None

    async def get_changes(self, stock_code: str, period: str) -> dict[str, Any]:
        symbol = normalize_longbridge_symbol(stock_code)
        payload = await self.client.broker_holding(symbol, period)
        return _normalize_period_payload(payload, period=period)

    async def get_enrichment(self, stock_code: str, broker_id: str) -> dict[str, Any]:
        symbol = normalize_longbridge_symbol(stock_code)
        payloads = await self.client.call_enrichment(symbol, broker_id)
        periods = {
            period: _normalize_period_payload(payloads.get(period) or {}, period=period)
            for period in ("rct_1", "rct_5", "rct_20", "rct_60")
        }
        daily_payload = payloads.get("daily") or {}
        rows = daily_payload.get("list") or []
        daily = {
            **daily_payload,
            "list": [{**row, "date": _normalize_date(row.get("date"))} for row in rows if isinstance(row, dict)],
            "symbol": symbol,
            "source": "longbridge",
        }
        return {"periods": periods, "daily": daily}

    async def get_daily(self, stock_code: str, broker_id: str) -> dict[str, Any]:
        symbol = normalize_longbridge_symbol(stock_code)
        payload = await self.client.broker_holding_daily(symbol, broker_id)
        rows = payload.get("list") or []
        if not isinstance(rows, list):
            raise RuntimeError("Longbridge daily holdings payload has invalid list")
        normalized = []
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError("Longbridge daily holdings row is invalid")
            normalized.append({**row, "date": _normalize_date(row.get("date"))})
        return {**payload, "list": normalized, "symbol": symbol, "source": "longbridge"}

    async def get_static_info(self, stock_code: str) -> dict[str, Any]:
        symbol = normalize_longbridge_symbol(stock_code)
        payload = await self.client.static_info([symbol])
        return {**payload, "symbol": symbol, "source": "longbridge"}

    async def get_price_history(
        self, stock_code: str, *, start_date: date | None = None, end_date: date | None = None
    ) -> PriceHistoryResponse:
        symbol = normalize_longbridge_symbol(stock_code)
        end = end_date or date.today()
        start = start_date or date(end.year - 1, end.month, end.day)
        price_payload = await self.client.call_price(symbol, start.isoformat(), end.isoformat())
        quote_payload = price_payload.get("quote") or {}
        history_payload = price_payload.get("history") or {}
        quote_item = _first_payload_item(quote_payload)
        raw_rows = _payload_list(history_payload)
        prices = [_price_row(item) for item in raw_rows if isinstance(item, dict)]
        prices = [row for row in prices if row is not None]
        if not prices and quote_item:
            row = _price_row(quote_item)
            if row is not None:
                prices = [row]
        if not prices:
            raise RuntimeError("Longbridge returned no usable price data")
        prices.sort(key=lambda row: row.price_date)
        return PriceHistoryResponse(
            metadata=PriceHistoryMetadata(
                code=stock_code,
                ticker=symbol,
                price_date_from=prices[0].price_date,
                price_date_to=prices[-1].price_date,
                source_name="Longbridge",
                source_url=f"longbridge://history_candlesticks_by_date/{symbol}",
                fetched_at=datetime.now(UTC),
                adjustment_state="unadjusted",
                currency="HKD",
            ),
            prices=prices,
        )

def _normalize_date(value: object) -> str | None:
    if value is None or not str(value).strip():
        return None
    raw = str(value).strip().replace(".", "-")
    return date.fromisoformat(raw).isoformat()


def _normalize_period_payload(payload: dict[str, Any], *, period: str) -> dict[str, Any]:
    normalized: dict[str, Any] = {"buy": [], "sell": []}
    for side in ("buy", "sell"):
        rows = payload.get(side) or []
        if not isinstance(rows, list):
            raise RuntimeError(f"Longbridge {period} payload has invalid {side} list")
        normalized[side] = [dict(row) for row in rows if isinstance(row, dict)]
    normalized.update(
        {
            "updated_at": _normalize_date(payload.get("updated_at")),
            "period": period,
            "source": "longbridge",
        }
    )
    return normalized


def _payload_list(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("list", "items", "data", "candlesticks", "bars"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _first_payload_item(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, dict) and any(key in payload for key in ("last_done", "last", "close")):
        return payload
    rows = _payload_list(payload)
    return rows[0] if rows and isinstance(rows[0], dict) else None


def _price_row(item: dict[str, Any]) -> PriceHistoryRow | None:
    def value(*keys: str):
        for key in keys:
            if key in item and item[key] is not None:
                return item[key]
        return None

    raw_date = value("timestamp", "date", "time")
    if raw_date is None:
        return None
    try:
        text = str(raw_date).replace("Z", "+00:00")
        if text.isdigit():
            parsed_date = datetime.fromtimestamp(float(text), tz=UTC).date()
        else:
            parsed_date = datetime.fromisoformat(text).date()
    except (TypeError, ValueError, OverflowError):
        try:
            parsed_date = date.fromisoformat(str(raw_date).replace(".", "-"))
        except ValueError:
            return None

    def number(*keys: str):
        raw = value(*keys)
        try:
            return float(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    close = number("close", "last_done", "price")
    if close is None:
        return None
    volume = number("volume")
    turnover = number("turnover")
    return PriceHistoryRow(
        price_date=parsed_date,
        open=number("open"), high=number("high"), low=number("low"), close=close,
        vwap=number("vwap"), volume=int(volume) if volume is not None else None,
        turnover=turnover, price_source="Longbridge",
        turnover_est=turnover, vwap_est=number("vwap"),
    )


def get_longbridge_holdings_service() -> LongbridgeHoldingsService:
    return LongbridgeHoldingsService()


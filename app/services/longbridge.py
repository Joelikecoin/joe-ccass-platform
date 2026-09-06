from __future__ import annotations

from pathlib import Path
from datetime import date
from typing import Any

from app.config import Settings, get_settings
from app.longbridge_persistence import build_response, persist_response
from app.models import CcassResponse
from app.sources.longbridge import LongbridgeMcpClient, normalize_longbridge_symbol


class LongbridgeHoldingsService:
    def __init__(self, *, settings: Settings | None = None, client: LongbridgeMcpClient | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = client or LongbridgeMcpClient()

    async def fetch_and_persist(self, stock_code: str) -> CcassResponse:
        symbol = normalize_longbridge_symbol(stock_code)
        payload = await self.client.broker_holding_detail(symbol)
        issued_shares = await self._issued_shares(symbol)
        response = build_response(
            payload,
            stock_code=stock_code,
            issue_id=0,
            issued_shares=issued_shares,
        )
        persist_response(response, db_path=Path(self.settings.ccass_sqlite_path))
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


def get_longbridge_holdings_service() -> LongbridgeHoldingsService:
    return LongbridgeHoldingsService()

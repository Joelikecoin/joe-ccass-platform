"""Official Longbridge MCP read-only holdings client."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx


class LongbridgeMcpClient:
    """Call the official Longbridge MCP tool without touching the Webb router."""

    def __init__(self, *, endpoint: str | None = None, access_token: str | None = None) -> None:
        self.endpoint = endpoint or os.getenv("LONGBRIDGE_MCP_URL", "")
        self.access_token = access_token or os.getenv("LONGBRIDGE_ACCESS_TOKEN", "")
        if not self.endpoint:
            raise RuntimeError("LONGBRIDGE_MCP_URL is required")
        if not self.access_token:
            raise RuntimeError("LONGBRIDGE_ACCESS_TOKEN is required")

    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.endpoint,
                json=request,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            response.raise_for_status()
            payload = response.json()
        if "error" in payload:
            raise RuntimeError(str(payload["error"]))
        result = payload.get("result", payload)
        content = result.get("content") if isinstance(result, dict) else None
        if content:
            text = next((item.get("text") for item in content if item.get("type") == "text"), None)
            if text:
                result = json.loads(text)
        if not isinstance(result, dict):
            raise RuntimeError("Longbridge MCP returned an invalid holdings payload")
        return result

    async def broker_holding_detail(self, symbol: str) -> dict[str, Any]:
        return await self._call_tool(
            "longbridge_broker_holding_detail", {"symbol": symbol}
        )

    async def broker_holding(self, symbol: str, period: str) -> dict[str, Any]:
        if period not in {"rct_1", "rct_5", "rct_20", "rct_60"}:
            raise ValueError(f"unsupported Longbridge holding period: {period}")
        return await self._call_tool(
            "longbridge_broker_holding", {"symbol": symbol, "period": period}
        )

    async def broker_holding_daily(self, symbol: str, broker_id: str) -> dict[str, Any]:
        if not broker_id.strip():
            raise ValueError("broker_id is required")
        return await self._call_tool(
            "longbridge_broker_holding_daily",
            {"symbol": symbol, "broker_id": broker_id.strip()},
        )

    async def participants(self, symbol: str) -> dict[str, Any]:
        return await self._call_tool("longbridge_participants", {"symbol": symbol})

    async def static_info(self, symbols: list[str]) -> dict[str, Any]:
        if not symbols:
            raise ValueError("at least one symbol is required")
        return await self._call_tool("longbridge_static_info", {"symbols": symbols})


def normalize_longbridge_symbol(stock_code: str) -> str:
    digits = "".join(ch for ch in str(stock_code).strip() if ch.isdigit())
    if not digits or len(digits) > 5:
        raise ValueError(f"invalid HK stock code: {stock_code!r}")
    return f"{int(digits):d}.HK"

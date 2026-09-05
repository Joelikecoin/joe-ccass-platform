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

    async def broker_holding_detail(self, symbol: str) -> dict[str, Any]:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "longbridge_broker_holding_detail",
                "arguments": {"symbol": symbol},
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


def normalize_longbridge_symbol(stock_code: str) -> str:
    digits = "".join(ch for ch in str(stock_code).strip() if ch.isdigit())
    if not digits or len(digits) > 5:
        raise ValueError(f"invalid HK stock code: {stock_code!r}")
    return f"{int(digits):d}.HK"

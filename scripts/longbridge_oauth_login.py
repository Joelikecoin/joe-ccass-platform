"""Run Longbridge OAuth on the Windows host and verify read-only tools."""

from __future__ import annotations

import asyncio

from app.sources.longbridge import LongbridgeMcpClient, _oauth_cache_path


async def main() -> None:
    cache = _oauth_cache_path()
    client = LongbridgeMcpClient()
    # Use the official MCP tool names for this verification helper. The app's
    # higher-level wrappers are intentionally not changed by the auth fix.
    detail = await client._call_tool("broker_holding_detail", {"symbol": "6182.HK"})
    rows = detail.get("list") or []
    b01438 = next((row for row in rows if row.get("parti_number") == "B01438"), None)
    rct1 = await client._call_tool(
        "broker_holding", {"symbol": "6182.HK", "period": "rct_1"}
    )
    daily = await client._call_tool(
        "broker_holding_daily", {"symbol": "6182.HK", "broker_id": "B01438"}
    )

    print("TOKEN_CACHE_CREATED", cache.is_file())
    print("DATA_DATE", detail.get("updated_at"))
    print("HOLDINGS_ROW_COUNT", len(rows))
    print("B01438_SHARES", (b01438 or {}).get("shares", {}).get("value"))
    print("RCT1_STATUS", "PASS" if (rct1.get("buy") or rct1.get("sell")) else "EMPTY")
    print("BROKER_DAILY_STATUS", "PASS" if len(daily.get("list") or []) > 1 else "PARTIAL")


if __name__ == "__main__":
    asyncio.run(main())

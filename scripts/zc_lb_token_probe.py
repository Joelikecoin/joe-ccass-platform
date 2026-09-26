"""One-shot probe: is the .env LONGBRIDGE_ACCESS_TOKEN still valid?"""
from __future__ import annotations

import asyncio
import os
import sys


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv(".env", override=True)
    token = os.getenv("LONGBRIDGE_ACCESS_TOKEN") or ""
    print("token_present", bool(token), "len", len(token))
    print("token_tail", repr(token[-4:]) if token else "-")
    print("has_cr", "\r" in token)

    if not token:
        print("VERDICT NO_TOKEN")
        return 2

    from app.sources.longbridge import LongbridgeMcpClient

    async def probe() -> int:
        client = LongbridgeMcpClient(access_token=token)
        try:
            result = await client._call_tool(
                "broker_holding_detail", {"symbol": "1.HK"}
            )
            rows = result if isinstance(result, list) else result.get("rows", result)
            n = len(rows) if hasattr(rows, "__len__") else -1
            print("probe_ok rows", n)
            print("VERDICT TOKEN_VALID")
            return 0
        except Exception as exc:  # noqa: BLE001
            print("probe_fail", type(exc).__name__, str(exc)[:400])
            print("VERDICT TOKEN_REJECTED")
            return 1
        finally:
            pass

    try:
        return asyncio.run(probe())
    except Exception as exc:  # noqa: BLE001
        print("fatal", type(exc).__name__, str(exc)[:300])
        print("VERDICT TOKEN_REJECTED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

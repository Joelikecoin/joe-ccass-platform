"""Official Longbridge MCP read-only holdings client."""

from __future__ import annotations

import json
import os
import asyncio
import threading
import webbrowser
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken


class _FileTokenStorage(TokenStorage):
    """Small local OAuth cache; secrets never enter the repository."""

    def __init__(self, path: Path) -> None:
        self.path = path

    async def get_tokens(self) -> OAuthToken | None:
        try:
            return OAuthToken.model_validate_json(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            return None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(tokens.model_dump_json(), encoding="utf-8")

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        info = self.path.with_name("client.json")
        try:
            return OAuthClientInformationFull.model_validate_json(info.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            return None

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.with_name("client.json").write_text(
            client_info.model_dump_json(), encoding="utf-8"
        )


def _oauth_cache_path() -> Path:
    root = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
    return Path(root) / "JoeCCASS" / "longbridge" / "oauth_tokens.json"


async def _open_authorization(url: str) -> None:
    if not webbrowser.open(url):
        raise RuntimeError(f"Open this Longbridge OAuth URL in a browser: {url}")


async def _reject_interactive_oauth(_url: str) -> None:
    raise RuntimeError("LONG_BRIDGE_AUTH_UNAVAILABLE: interactive OAuth is disabled for request runtime")


async def _reject_interactive_callback() -> tuple[str, str | None]:
    raise RuntimeError("LONG_BRIDGE_AUTH_UNAVAILABLE: interactive OAuth is disabled for request runtime")


def _oauth_callback() -> tuple[callable, callable]:
    """Return handlers backed by a listener bound before browser authorization."""
    import http.server
    from urllib.parse import parse_qs, urlparse

    state: dict[str, str | None] = {"code": None, "state": None}
    ready = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            query = parse_qs(urlparse(self.path).query)
            state["code"] = query.get("code", [None])[0]
            state["state"] = query.get("state", [None])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Longbridge authorization complete. You may close this tab.")
            ready.set()

        def log_message(self, *_args):
            return

    # Bind before opening the browser so a host browser can reach the callback.
    server = http.server.HTTPServer(("127.0.0.1", 8765), Handler)
    server.timeout = 1

    def serve() -> None:
        while not ready.is_set():
            server.handle_request()
        server.server_close()

    threading.Thread(target=serve, name="longbridge-oauth-callback", daemon=True).start()

    async def redirect(url: str) -> None:
        await _open_authorization(url)

    async def callback() -> tuple[str, str | None]:
        loop = asyncio.get_running_loop()

        def wait_for_callback() -> tuple[str, str | None]:
            if not ready.wait(timeout=300):
                server.server_close()
                raise TimeoutError("Timed out waiting for Longbridge OAuth callback")
            return str(state["code"] or ""), state["state"]

        return await loop.run_in_executor(None, wait_for_callback)

    return redirect, callback


class LongbridgeMcpClient:
    """Call the official Longbridge MCP tool without touching the Webb router."""

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        access_token: str | None = None,
        interactive: bool = False,
    ) -> None:
        self.endpoint = endpoint or os.getenv("LONGBRIDGE_MCP_URL", "https://mcp.longbridge.com")
        self.access_token = access_token or os.getenv("LONGBRIDGE_ACCESS_TOKEN")
        self._oauth = None
        if not self.endpoint:
            raise RuntimeError("Longbridge MCP endpoint is required")
        if not self.access_token:
            # Request handlers may reuse cached OAuth tokens through the
            # provider, but must never start a localhost callback listener.
            # The explicit login script opts into the interactive bootstrap.
            redirect, callback = _oauth_callback() if interactive else (
                _reject_interactive_oauth,
                _reject_interactive_callback,
            )
            self._oauth = OAuthClientProvider(
                self.endpoint,
                OAuthClientMetadata(
                    redirect_uris=["http://127.0.0.1:8765/callback"],
                    token_endpoint_auth_method="none",
                    client_name="Joe CCASS Platform",
                    scope="market_data",
                ),
                _FileTokenStorage(_oauth_cache_path()),
                redirect_handler=redirect,
                callback_handler=callback,
            )

    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        async with streamablehttp_client(
            self.endpoint,
            headers=self._auth_headers(),
            timeout=30,
            sse_read_timeout=300,
            auth=self._oauth,
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
        if getattr(result, "is_error", False):
            raise RuntimeError(str(result.content))
        content = getattr(result, "content", None) or []
        text = next((item.text for item in content if getattr(item, "text", None)), None)
        if text:
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                raise RuntimeError("Longbridge MCP returned non-JSON tool content") from None
        if not isinstance(result, (dict, list)):
            raise RuntimeError("Longbridge MCP returned an invalid JSON payload")
        return result

    def _auth_headers(self) -> dict[str, str] | None:
        """Return the explicit bearer credential for every MCP transport session."""
        if not self.access_token:
            return None
        return {"Authorization": f"Bearer {self.access_token}"}

    async def call_enrichment(self, symbol: str, broker_id: str) -> dict[str, Any]:
        """Fetch period changes and broker history over one shared MCP session."""
        names = [
            ("rct_1", "broker_holding", {"symbol": symbol, "period": "rct_1"}),
            ("rct_5", "broker_holding", {"symbol": symbol, "period": "rct_5"}),
            ("rct_20", "broker_holding", {"symbol": symbol, "period": "rct_20"}),
            ("rct_60", "broker_holding", {"symbol": symbol, "period": "rct_60"}),
            ("daily", "broker_holding_daily", {"symbol": symbol, "broker_id": broker_id}),
        ]
        output: dict[str, Any] = {}
        async with streamablehttp_client(
            self.endpoint,
            headers=self._auth_headers(),
            timeout=30,
            sse_read_timeout=300,
            auth=self._oauth,
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                for key, name, arguments in names:
                    result = await session.call_tool(name, arguments)
                    is_error = bool(getattr(result, "is_error", False))
                    content = getattr(result, "content", None) or []
                    text = next((item.text for item in content if getattr(item, "text", None)), None)
                    parsed: Any = {}
                    if text and not is_error:
                        parsed = json.loads(text)
                    if is_error:
                        raise RuntimeError(f"Longbridge {key} tool error")
                    if key in {"rct_1", "rct_5", "rct_20", "rct_60"}:
                        buy = parsed.get("buy") if isinstance(parsed, dict) else []
                        sell = parsed.get("sell") if isinstance(parsed, dict) else []
                        row_count = (len(buy) if isinstance(buy, list) else 0) + (len(sell) if isinstance(sell, list) else 0)
                        if row_count == 0:
                            # Retry only this empty period through a fresh
                            # authenticated transport/session.  A transient
                            # empty result must never be accepted as success.
                            parsed = await self._call_tool(name, arguments)
                            retry_buy = parsed.get("buy") if isinstance(parsed, dict) else []
                            retry_sell = parsed.get("sell") if isinstance(parsed, dict) else []
                            retry_count = (len(retry_buy) if isinstance(retry_buy, list) else 0) + (len(retry_sell) if isinstance(retry_sell, list) else 0)
                            if retry_count == 0:
                                raise RuntimeError(f"Longbridge {key} returned no rows after retry")
                    output[key] = parsed
        return output

    async def call_price(self, symbol: str, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch quote and daily candles over one authenticated MCP session."""
        output: dict[str, Any] = {}
        calls = (
            ("quote", "quote", {"symbols": [symbol]}),
            (
                "history",
                "history_candlesticks_by_date",
                {"symbol": symbol, "start_date": start_date, "end_date": end_date},
            ),
        )
        async with streamablehttp_client(
            self.endpoint,
            headers=self._auth_headers(),
            timeout=30,
            sse_read_timeout=300,
            auth=self._oauth,
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                for key, name, arguments in calls:
                    result = await session.call_tool(name, arguments)
                    if getattr(result, "is_error", False):
                        raise RuntimeError(f"Longbridge {key} tool error")
                    content = getattr(result, "content", None) or []
                    text = next((item.text for item in content if getattr(item, "text", None)), None)
                    output[key] = json.loads(text) if text else {}
        return output

    async def broker_holding_detail(self, symbol: str) -> dict[str, Any]:
        return await self._call_tool(
            "broker_holding_detail", {"symbol": symbol}
        )

    async def broker_holding(self, symbol: str, period: str) -> dict[str, Any]:
        if period not in {"rct_1", "rct_5", "rct_20", "rct_60"}:
            raise ValueError(f"unsupported Longbridge holding period: {period}")
        return await self._call_tool(
            "broker_holding", {"symbol": symbol, "period": period}
        )

    async def broker_holding_daily(self, symbol: str, broker_id: str) -> dict[str, Any]:
        if not broker_id.strip():
            raise ValueError("broker_id is required")
        return await self._call_tool(
            "broker_holding_daily",
            {"symbol": symbol, "broker_id": broker_id.strip()},
        )

    async def participants(self, symbol: str) -> dict[str, Any]:
        return await self._call_tool("participants", {"symbol": symbol})

    async def static_info(self, symbols: list[str]) -> dict[str, Any]:
        if not symbols:
            raise ValueError("at least one symbol is required")
        result = await self._call_tool("static_info", {"symbols": symbols})
        if isinstance(result, list):
            return {"list": result}
        if not isinstance(result, dict):
            raise RuntimeError("Longbridge static_info returned an invalid payload")
        return result

    async def quote(self, symbol: str) -> dict[str, Any]:
        """Return the authenticated Longbridge quote payload."""
        return await self._call_tool("quote", {"symbols": [symbol]})

    async def history_candlesticks_by_date(
        self, symbol: str, start_date: str, end_date: str
    ) -> dict[str, Any]:
        """Return daily Longbridge candles for an inclusive date range."""
        return await self._call_tool(
            "history_candlesticks_by_date",
            {"symbol": symbol, "start_date": start_date, "end_date": end_date},
        )


def normalize_longbridge_symbol(stock_code: str) -> str:
    digits = "".join(ch for ch in str(stock_code).strip() if ch.isdigit())
    if not digits or len(digits) > 5:
        raise ValueError(f"invalid HK stock code: {stock_code!r}")
    return f"{int(digits):d}.HK"

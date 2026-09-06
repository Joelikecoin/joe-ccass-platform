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


def _oauth_callback() -> tuple[callable, callable]:
    """Return redirect/callback handlers backed by a temporary localhost listener."""
    state: dict[str, str | None] = {"code": None, "state": None}
    ready = threading.Event()

    async def redirect(url: str) -> None:
        await _open_authorization(url)

    async def callback() -> tuple[str, str | None]:
        loop = asyncio.get_running_loop()

        def wait_for_callback() -> tuple[str, str | None]:
            import http.server
            from urllib.parse import parse_qs, urlparse

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

            server = http.server.HTTPServer(("127.0.0.1", 8765), Handler)
            server.timeout = 300
            while not ready.is_set():
                server.handle_request()
            server.server_close()
            return str(state["code"] or ""), state["state"]

        return await loop.run_in_executor(None, wait_for_callback)

    return redirect, callback


class LongbridgeMcpClient:
    """Call the official Longbridge MCP tool without touching the Webb router."""

    def __init__(self, *, endpoint: str | None = None, access_token: str | None = None) -> None:
        self.endpoint = endpoint or os.getenv("LONGBRIDGE_MCP_URL", "https://mcp.longbridge.com")
        self.access_token = access_token or os.getenv("LONGBRIDGE_ACCESS_TOKEN")
        self._oauth = None
        if not self.endpoint:
            raise RuntimeError("Longbridge MCP endpoint is required")
        if not self.access_token:
            redirect, callback = _oauth_callback()
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

    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else None
        async with streamablehttp_client(
            self.endpoint,
            headers=headers,
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

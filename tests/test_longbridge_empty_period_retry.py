from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.sources import longbridge as module


class _Result:
    is_error = False

    def __init__(self, payload):
        self.content = [SimpleNamespace(text=__import__("json").dumps(payload))]


class _Session:
    def __init__(self, payloads):
        self.payloads = payloads

    async def initialize(self):
        return None

    async def call_tool(self, name, arguments):
        return _Result(self.payloads[arguments.get("period", "daily")])

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False


class _Transport:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return (None, None, None)

    async def __aexit__(self, *_args):
        return False


def _install_shared_session(monkeypatch, payloads):
    monkeypatch.setattr(module, "streamablehttp_client", lambda *args, **kwargs: _Transport(None))
    monkeypatch.setattr(module, "ClientSession", lambda *_args: _Session(payloads))


def _payload(rows=1):
    return {"buy": [{"parti_number": "B1"}] * rows, "sell": []}


@pytest.mark.asyncio
async def test_non_empty_period_is_not_retried(monkeypatch):
    payloads = {period: _payload() for period in ("rct_1", "rct_5", "rct_20", "rct_60")}
    payloads["daily"] = {"list": []}
    _install_shared_session(monkeypatch, payloads)
    client = module.LongbridgeMcpClient(access_token="test-token")
    retry = AsyncMock()
    monkeypatch.setattr(client, "_call_tool", retry)

    result = await client.call_enrichment("6182.HK", "B1")

    assert result["rct_20"]["buy"]
    retry.assert_not_awaited()


@pytest.mark.asyncio
async def test_empty_period_retries_via_fresh_call(monkeypatch):
    payloads = {period: _payload() for period in ("rct_1", "rct_5", "rct_60")}
    payloads["rct_20"] = _payload(0)
    payloads["daily"] = {"list": []}
    _install_shared_session(monkeypatch, payloads)
    client = module.LongbridgeMcpClient(access_token="test-token")
    retry = AsyncMock(return_value=_payload(2))
    monkeypatch.setattr(client, "_call_tool", retry)

    result = await client.call_enrichment("6182.HK", "B1")

    assert len(result["rct_20"]["buy"]) == 2
    retry.assert_awaited_once_with("broker_holding", {"symbol": "6182.HK", "period": "rct_20"})


@pytest.mark.asyncio
async def test_second_empty_period_fails_loud(monkeypatch):
    payloads = {period: _payload() for period in ("rct_1", "rct_5", "rct_60")}
    payloads["rct_20"] = _payload(0)
    payloads["daily"] = {"list": []}
    _install_shared_session(monkeypatch, payloads)
    client = module.LongbridgeMcpClient(access_token="test-token")
    monkeypatch.setattr(client, "_call_tool", AsyncMock(return_value=_payload(0)))

    with pytest.raises(RuntimeError, match="rct_20 returned no rows after retry"):
        await client.call_enrichment("6182.HK", "B1")


def test_retry_uses_authenticated_headers():
    client = module.LongbridgeMcpClient(access_token="secret")
    assert client._auth_headers() == {"Authorization": "Bearer secret"}

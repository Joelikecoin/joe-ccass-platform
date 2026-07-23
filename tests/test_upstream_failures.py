import logging

import httpx
import pytest
import respx

from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.sources.webbsite import WebbsiteClient


def make_client() -> WebbsiteClient:
    return WebbsiteClient(
        Settings(
            webbsite_base_url="https://primary.example",
            webbsite_fallback_base_url="https://fallback.example",
            min_request_interval_seconds=0,
            request_timeout_seconds=0.1,
            api_key="must-not-appear",
        )
    )


@respx.mock
async def test_fetch_sends_browser_navigation_headers():
    route = respx.get("https://primary.example/page").mock(
        return_value=httpx.Response(
            200,
            text="<html><body>ok</body></html>",
            headers={"content-type": "text/html; charset=utf-8"},
        )
    )

    await make_client()._fetch("/page", {"code": "700"})

    headers = route.calls[0].request.headers
    assert headers["user-agent"].startswith("Mozilla/5.0")
    assert headers["accept"].startswith("text/html")
    assert headers["accept-language"].startswith("en-GB")
    assert headers["accept-encoding"] == "gzip, deflate"
    assert headers["cache-control"] == "no-cache"
    assert headers["dnt"] == "1"
    assert headers["pragma"] == "no-cache"
    assert headers["referer"] == "https://primary.example/"
    assert "Google Chrome" in headers["sec-ch-ua"]
    assert headers["sec-ch-ua-mobile"] == "?0"
    assert headers["sec-ch-ua-platform"] == '"Windows"'
    assert headers["sec-fetch-dest"] == "document"
    assert headers["sec-fetch-mode"] == "navigate"
    assert headers["sec-fetch-site"] == "same-origin"
    assert headers["sec-fetch-user"] == "?1"
    assert headers["priority"] == "u=0, i"
    assert headers["upgrade-insecure-requests"] == "1"
    assert "authorization" not in headers
    assert "x-api-key" not in headers


@pytest.mark.parametrize(
    ("status_code", "error_code", "public_status", "error_type"),
    [
        (403, ErrorCode.SOURCE_FORBIDDEN, 502, "forbidden"),
        (429, ErrorCode.SOURCE_RATE_LIMITED, 503, "rate_limited"),
        (502, ErrorCode.SOURCE_UNAVAILABLE, 502, "server_error"),
    ],
)
@respx.mock
async def test_fetch_classifies_http_failures(
    caplog, status_code, error_code, public_status, error_type
):
    for hostname in ("primary.example", "fallback.example"):
        respx.get(f"https://{hostname}/page").mock(
            return_value=httpx.Response(status_code, text="upstream failure")
        )

    with caplog.at_level(logging.WARNING), pytest.raises(PlatformError) as caught:
        await make_client()._fetch("/page", {"code": "700", "key": "must-not-appear"})

    assert caught.value.code == error_code
    assert caught.value.status_code == public_status
    assert caplog.text.count(f"status_code={status_code}") == 2
    assert caplog.text.count(f"error_type={error_type}") == 2
    assert "hostname=primary.example" in caplog.text
    assert "hostname=fallback.example" in caplog.text
    assert "must-not-appear" not in caplog.text


@respx.mock
async def test_fetch_only_reports_timeout_for_true_timeouts(caplog):
    for hostname in ("primary.example", "fallback.example"):
        respx.get(f"https://{hostname}/page").mock(side_effect=httpx.ReadTimeout("slow"))

    with caplog.at_level(logging.WARNING), pytest.raises(PlatformError) as caught:
        await make_client()._fetch("/page", {"code": "700"})

    assert caught.value.code == ErrorCode.SOURCE_TIMEOUT
    assert caught.value.status_code == 504
    assert caplog.text.count("status_code=none error_type=timeout") == 2


@respx.mock
async def test_mixed_timeout_and_server_error_is_not_reported_as_timeout():
    respx.get("https://primary.example/page").mock(side_effect=httpx.ReadTimeout("slow"))
    respx.get("https://fallback.example/page").mock(
        return_value=httpx.Response(503, text="unavailable")
    )

    with pytest.raises(PlatformError) as caught:
        await make_client()._fetch("/page", {"code": "700"})

    assert caught.value.code == ErrorCode.SOURCE_UNAVAILABLE
    assert caught.value.status_code == 502

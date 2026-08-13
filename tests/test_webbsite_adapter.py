from datetime import date
from pathlib import Path

import httpx
import pytest
import respx

from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.sources.registry import SourceCapability
from app.sources.webbsite import FetchedPage, WebbsiteClient
from ccass_core.collector import CollectorConfig, collect_watchlist

FIXTURES = Path(__file__).parent / "fixtures" / "webbsite"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def settings(**overrides) -> Settings:
    values = {
        "webbsite_base_url": "https://primary.example",
        "webbsite_fallback_base_url": "https://fallback.example",
        "min_request_interval_seconds": 0,
        "source_retry_attempts": 1,
    }
    values.update(overrides)
    return Settings(**values)


def _mock_landing_pages(body: bytes = b"<html><body>landing</body></html>"):
    for hostname in ("primary.example", "fallback.example"):
        respx.get(f"https://{hostname}/").mock(
            return_value=httpx.Response(
                200,
                content=body,
                headers={"content-type": "text/html; charset=utf-8"},
            )
        )


async def test_adapter_uses_single_code_request_and_builds_complete_normalized_output(
    monkeypatch,
):
    client = WebbsiteClient(settings())
    assert client.definition.capabilities == frozenset({SourceCapability.LATEST})
    assert client.definition.parser_id == "webbsite-holdings"
    assert client.definition.parser_version == "2"
    calls = []

    async def fake_fetch(path, params):
        calls.append((path, params))
        return FetchedPage(
            fixture("holdings_normal.html"),
            "https://primary.example/ccass/choldings.asp?sc=1592",
            False,
        )

    monkeypatch.setattr(client, "_fetch", fake_fetch)
    response = await client.get_holdings("01592", limit=2)

    assert calls == [("/ccass/choldings.asp", {"sc": "1592"})]
    assert response.metadata.code == "01592"
    assert response.metadata.issue_id == 15_920
    assert response.metadata.holdings_date == date(2026, 7, 20)
    assert response.metadata.source_name == "Webb-site mirror"
    assert response.metadata.source_url.endswith("choldings.asp?sc=1592")
    assert not response.metadata.cached
    assert response.metadata.fetched_at.date() >= response.metadata.holdings_date
    assert [row.rank for row in response.holdings] == [1, 2]
    assert response.holdings_summary.participant_count == 4
    assert response.holdings_summary.top5_pct_of_issued == 80.0
    assert any(
        "percentage values use the source page" in warning
        for warning in response.data_quality_warnings
    )


async def test_parser_error_propagates_without_empty_success(monkeypatch):
    client = WebbsiteClient(settings())

    async def fake_fetch(path, params):
        return FetchedPage(
            fixture("holdings_malformed.html"),
            "https://primary.example/ccass/choldings.asp?sc=1592",
            False,
        )

    monkeypatch.setattr(client, "_fetch", fake_fetch)
    with pytest.raises(PlatformError) as caught:
        await client.get_holdings("01592")

    assert caught.value.code == ErrorCode.PARSE_ERROR


@respx.mock
async def test_fetch_rejects_wrong_content_type_on_all_mirrors():
    _mock_landing_pages()
    for hostname in ("primary.example", "fallback.example"):
        respx.get(f"https://{hostname}/ccass/choldings.asp").mock(
            return_value=httpx.Response(
                200,
                content=b'{"not":"html"}',
                headers={"content-type": "application/json"},
            )
        )

    with pytest.raises(PlatformError) as caught:
        await WebbsiteClient(settings()).get_holdings("01592")

    assert caught.value.code == ErrorCode.SOURCE_CHANGED
    assert "content_type=application/json" in caught.value.message
    assert "url=https://primary.example/ccass/choldings.asp" in caught.value.message


@pytest.mark.parametrize(
    ("body", "error_code"),
    [
        (b"", ErrorCode.SOURCE_CHANGED),
        (
            b"<html><head><title>Sign in</title></head>"
            b'<body><input type="password"></body></html>',
            ErrorCode.SOURCE_FORBIDDEN,
        ),
        (
            b"<html><head><title>Error</title></head>"
            b"<body>Internal server error</body></html>",
            ErrorCode.SOURCE_CHANGED,
        ),
        (b"<html><body>incomplete", ErrorCode.SOURCE_CHANGED),
    ],
)
@respx.mock
async def test_fetch_rejects_empty_login_error_and_incomplete_html(body, error_code):
    _mock_landing_pages()
    for hostname in ("primary.example", "fallback.example"):
        respx.get(f"https://{hostname}/ccass/choldings.asp").mock(
            return_value=httpx.Response(
                200,
                content=body,
                headers={"content-type": "text/html; charset=utf-8"},
            )
        )

    with pytest.raises(PlatformError) as caught:
        await WebbsiteClient(settings()).get_holdings("01592")

    assert caught.value.code == error_code
    assert "status=200" in caught.value.message
    assert "url=https://primary.example/ccass/choldings.asp" in caught.value.message


@pytest.mark.parametrize("declared", [True, False])
@respx.mock
async def test_fetch_enforces_declared_and_streamed_size_limits(declared):
    _mock_landing_pages()
    body = b"<html><body>oversize</body></html>"
    headers = {"content-type": "text/html"}
    if declared:
        headers["content-length"] = str(len(body))
        response = httpx.Response(200, content=body, headers=headers)
    else:
        response = httpx.Response(200, stream=httpx.ByteStream(body), headers=headers)
    for hostname in ("primary.example", "fallback.example"):
        respx.get(f"https://{hostname}/ccass/choldings.asp").mock(return_value=response)

    with pytest.raises(PlatformError) as caught:
        await WebbsiteClient(settings(webbsite_max_bytes=10)).get_holdings("01592")

    assert caught.value.code == ErrorCode.TOO_LARGE


@respx.mock
async def test_invalid_primary_page_isolated_when_fallback_is_valid():
    _mock_landing_pages()
    respx.get("https://primary.example/ccass/choldings.asp").mock(
        return_value=httpx.Response(
            200,
            content=b'{"wrong":"type"}',
            headers={"content-type": "application/json"},
        )
    )
    respx.get("https://fallback.example/ccass/choldings.asp").mock(
        return_value=httpx.Response(
            200,
            text=fixture("holdings_normal.html"),
            headers={"content-type": "text/html; charset=utf-8"},
        )
    )

    response = await WebbsiteClient(settings()).get_holdings("01592")

    assert response.metadata.source_url.startswith("https://fallback.example/")
    assert response.metadata.issue_id == 15_920

@respx.mock
async def test_fetch_cache_preserves_source_reference_and_avoids_repeat_request():
    _mock_landing_pages()
    route = respx.get("https://primary.example/ccass/choldings.asp").mock(
        return_value=httpx.Response(
            200,
            text=fixture("holdings_normal.html"),
            headers={"content-type": "text/html; charset=utf-8"},
        )
    )
    client = WebbsiteClient(settings(cache_ttl_seconds=60))

    first = await client.get_holdings("01592")
    second = await client.get_holdings("01592")

    assert route.call_count == 1
    assert not first.metadata.cached
    assert second.metadata.cached
    assert second.metadata.source_url == first.metadata.source_url


@respx.mock
async def test_fetch_persists_session_cookies_between_requests():
    request_cookies: list[str | None] = []
    call_state = {"count": 0}

    def callback(request: httpx.Request) -> httpx.Response:
        call_state["count"] += 1
        request_cookies.append(request.headers.get("cookie"))
        headers = {"content-type": "text/html; charset=utf-8"}
        if call_state["count"] == 1:
            headers["set-cookie"] = "webbsite-session=abc123; Path=/; HttpOnly"
        return httpx.Response(
            200,
            text=fixture("holdings_normal.html"),
            headers=headers,
            request=request,
        )

    root_route = respx.get("https://primary.example/").mock(side_effect=callback)
    route = respx.get("https://primary.example/ccass/choldings.asp").mock(
        side_effect=callback
    )
    client = WebbsiteClient(settings(cache_ttl_seconds=0))

    first = await client.get_holdings("01592")
    second = await client.get_holdings("01592")

    assert root_route.call_count == 1
    assert route.call_count == 2
    assert request_cookies == [None, "webbsite-session=abc123", "webbsite-session=abc123"]
    assert not first.metadata.cached
    assert not second.metadata.cached


@respx.mock
async def test_fetch_primes_session_before_holdings_request():
    landing_requests: list[str | None] = []
    holding_requests: list[str | None] = []

    def landing_callback(request: httpx.Request) -> httpx.Response:
        landing_requests.append(request.headers.get("cookie"))
        return httpx.Response(
            200,
            content=b"<html><body>landing</body></html>",
            headers={
                "content-type": "text/html; charset=utf-8",
                "set-cookie": "webbsite-session=prime123; Path=/; HttpOnly",
            },
            request=request,
        )

    def holdings_callback(request: httpx.Request) -> httpx.Response:
        holding_requests.append(request.headers.get("cookie"))
        return httpx.Response(
            200,
            text=fixture("holdings_normal.html"),
            headers={"content-type": "text/html; charset=utf-8"},
            request=request,
        )

    respx.get("https://primary.example/").mock(side_effect=landing_callback)
    respx.get("https://primary.example/ccass/choldings.asp").mock(
        side_effect=holdings_callback
    )
    client = WebbsiteClient(settings(cache_ttl_seconds=0))

    await client.get_holdings("01592")
    await client.get_holdings("01592")

    assert landing_requests == [None]
    assert holding_requests == [
        "webbsite-session=prime123",
        "webbsite-session=prime123",
    ]


@respx.mock
async def test_fetch_reports_login_redirect_target_in_failure_details():
    _mock_landing_pages()
    respx.get("https://primary.example/ccass/choldings.asp").mock(
        return_value=httpx.Response(
            302,
            headers={
                "location": "https://primary.example/login",
                "content-type": "text/html; charset=utf-8",
            },
        )
    )
    respx.get("https://primary.example/login").mock(
        return_value=httpx.Response(
            200,
            text=(
                "<html><head><title>Login</title></head>"
                '<body><input type="password"></body></html>'
            ),
            headers={"content-type": "text/html; charset=utf-8"},
        )
    )
    respx.get("https://fallback.example/ccass/choldings.asp").mock(
        return_value=httpx.Response(
            200,
            text=(
                "<html><head><title>Login</title></head>"
                '<body><input type="password"></body></html>'
            ),
            headers={"content-type": "text/html; charset=utf-8"},
        )
    )

    with pytest.raises(PlatformError) as caught:
        await WebbsiteClient(settings()).get_holdings("01592")

    assert caught.value.code == ErrorCode.SOURCE_FORBIDDEN
    assert "redirect=https://primary.example/login" in caught.value.message
    assert "content_type=text/html; charset=utf-8" in caught.value.message
    assert "login page detected" in caught.value.message
    assert "url=https://primary.example/ccass/choldings.asp" in caught.value.message


@respx.mock
async def test_fetch_classifies_challenge_page_without_parser_call():
    _mock_landing_pages()
    challenge = (
        "<html><head><title>Just a moment...</title></head>"
        '<body><form id="cf-chl-test"></form></body></html>'
    )
    for hostname in ("primary.example", "fallback.example"):
        respx.get(f"https://{hostname}/ccass/choldings.asp").mock(
            return_value=httpx.Response(
                200,
                text=challenge,
                headers={"content-type": "text/html"},
            )
        )

    with pytest.raises(PlatformError) as caught:
        await WebbsiteClient(settings()).get_holdings("01592")

    assert caught.value.code == ErrorCode.SOURCE_FORBIDDEN
    assert "cloudflare challenge detected" in caught.value.message


@respx.mock
async def test_registry_retry_attempts_are_bounded_across_mirrors():
    _mock_landing_pages()
    routes = []
    for hostname in ("primary.example", "fallback.example"):
        routes.append(
            respx.get(f"https://{hostname}/ccass/choldings.asp").mock(
                return_value=httpx.Response(503, text="unavailable")
            )
        )

    with pytest.raises(PlatformError) as caught:
        await WebbsiteClient(settings(source_retry_attempts=2)).get_holdings("01592")

    assert caught.value.code == ErrorCode.SOURCE_UNAVAILABLE
    assert [route.call_count for route in routes] == [2, 2]


@respx.mock
async def test_disabled_adapter_fails_before_network_call():
    client = WebbsiteClient(settings(webbsite_enabled=False))

    with pytest.raises(PlatformError) as caught:
        await client.get_holdings("01592")

    assert caught.value.code == ErrorCode.SOURCE_DISABLED
    assert not respx.calls


async def test_offline_adapter_to_collector_vertical_integration(tmp_path, monkeypatch):
    client = WebbsiteClient(settings())

    async def fake_fetch(path, params):
        assert (path, params) == ("/ccass/choldings.asp", {"sc": "1592"})
        return FetchedPage(
            fixture("holdings_normal.html"),
            "https://fixture.invalid/ccass/choldings.asp?sc=1592",
            False,
        )

    monkeypatch.setattr(client, "_fetch", fake_fetch)
    config = CollectorConfig(
        watchlist=("1592",),
        sqlite_path=tmp_path / "must-not-exist.db",
        csv_output_path=tmp_path / "must-not-exist.csv",
        source_mode="webbsite",
        dry_run=True,
        holdings_limit=3,
    )

    collected, failures = await collect_watchlist(
        config,
        fetcher=lambda code, limit: client.get_holdings(code, limit=limit),
    )

    assert failures == {}
    assert len(collected) == 1
    assert collected[0].metadata.code == "01592"
    assert collected[0].metadata.issue_id == 15_920
    assert [row.rank for row in collected[0].holdings] == [1, 2, 3]
    assert collected[0].holdings_summary.participant_count == 4
    assert not config.sqlite_path.exists()
    assert not config.csv_output_path.exists()

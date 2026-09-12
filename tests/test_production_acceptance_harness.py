import json

import httpx

from scripts.production_acceptance_harness import AcceptanceHarness


def _harness(handler, *, api_key="test-key"):
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    return AcceptanceHarness(
        base_url="https://production.example/",
        api_key=api_key,
        stocks=("00005",),
        client=client,
        timeout_seconds=1,
    )


def _payload(*, source="Longbridge", cached=False, stale=False):
    return {
        "metadata": {
            "source_name": source,
            "fetched_at": "2026-09-12T01:00:00+00:00",
            "holdings_date": "2026-09-11",
            "cached": cached,
            "stale": stale,
        },
        "holdings": [{"participant_id": "A", "shares": 100}],
    }


def test_missing_auth_is_blocked_without_sending_authorization():
    seen = []

    def handler(request):
        seen.append(request.headers.get("authorization"))
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/openapi.json":
            return httpx.Response(200, json={"paths": {}})
        return httpx.Response(401, json={})

    harness = _harness(handler, api_key=None)
    try:
        report = harness.run().as_dict()
    finally:
        harness.close()
    assert any(item["name"] == "auth" and item["state"] == "BLOCKED" for item in report["checks"])
    assert all(value is None for value in seen)


def test_live_holdings_passes_and_preserves_no_cache_contract():
    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/openapi.json":
            return httpx.Response(200, json={"paths": {
                "/api/v1/stocks/{stock_code}/holdings": {},
                "/api/v1/stocks/{stock_code}/changes": {},
                "/api/v1/stocks/{stock_code}/big-changes": {},
                "/api/v1/stocks/{stock_code}/concentration": {},
            }})
        return httpx.Response(200, json=_payload())

    harness = _harness(handler)
    try:
        checks = harness.run().checks
    finally:
        harness.close()
    holdings = next(check for check in checks if check.name == "holdings:00005")
    assert holdings.state == "PASS"
    assert holdings.details["cached"] is False


def test_stale_holdings_are_not_live_pass():
    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={})
        if request.url.path == "/openapi.json":
            return httpx.Response(200, json={"paths": {}})
        return httpx.Response(200, json=_payload(cached=True, stale=True))

    harness = _harness(handler)
    try:
        checks = harness.run().checks
    finally:
        harness.close()
    holdings = next(check for check in checks if check.name == "holdings:00005")
    assert holdings.state == "STALE"


def test_server_failure_is_unavailable():
    def handler(request):
        return httpx.Response(503, json={"detail": "temporarily unavailable"})

    harness = _harness(handler)
    try:
        checks = harness.run().checks
    finally:
        harness.close()
    assert next(check for check in checks if check.name == "holdings:00005").state == "UNAVAILABLE"


def test_timeout_is_terminal_error_and_records_budget():
    def handler(request):
        raise httpx.ReadTimeout("controlled timeout", request=request)

    harness = _harness(handler)
    try:
        checks = harness.run().checks
    finally:
        harness.close()
    health = next(check for check in checks if check.name == "health")
    assert health.state == "ERROR"
    assert "elapsed_s" in health.details

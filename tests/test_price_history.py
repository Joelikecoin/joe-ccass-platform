from datetime import UTC, date, datetime

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.api import app
from app.models import PriceHistoryMetadata, PriceHistoryResponse, PriceHistoryRow
from app.services.price_history import get_price_history_service
from app.sources.price_history import YAHOO_CHART_BASE_URL, YahooFinancePriceHistorySource


def _price_history_response() -> PriceHistoryResponse:
    return PriceHistoryResponse(
        metadata=PriceHistoryMetadata(
            code="01592",
            name="Sample Company",
            ticker="01592.HK",
            price_date_from=date(2026, 7, 19),
            price_date_to=date(2026, 7, 20),
            source_name="Yahoo Finance",
            source_url=f"{YAHOO_CHART_BASE_URL}01592.HK",
            fetched_at=datetime(2026, 7, 21, 9, 0, 0, tzinfo=UTC),
            adjustment_state="adjusted",
            currency="HKD",
            adjustment_note="Adjusted close values are available from Yahoo Finance.",
        ),
        prices=[
            PriceHistoryRow(
                price_date=date(2026, 7, 19),
                open=1.0,
                high=1.1,
                low=0.9,
                close=1.05,
                adjusted_close=1.01,
                volume=1000,
                turnover=1050.0,
            ),
            PriceHistoryRow(
                price_date=date(2026, 7, 20),
                open=1.2,
                high=1.3,
                low=1.1,
                close=1.25,
                adjusted_close=1.21,
                volume=2000,
                turnover=2500.0,
            ),
        ],
    )


@pytest.mark.asyncio
@respx.mock
async def test_yahoo_price_history_source_parses_adjusted_close_and_turnover():
    source = YahooFinancePriceHistorySource()
    start_date = date(2026, 7, 19)
    end_date = date(2026, 7, 20)
    route = respx.get(f"{YAHOO_CHART_BASE_URL}01592.HK").mock(
        return_value=httpx.Response(
            200,
            json={
                "chart": {
                    "result": [
                        {
                            "meta": {
                                "symbol": "01592.HK",
                                "longName": "Sample Company",
                                "currency": "HKD",
                            },
                            "timestamp": [
                                int(datetime(2026, 7, 19, tzinfo=UTC).timestamp()),
                                int(datetime(2026, 7, 20, tzinfo=UTC).timestamp()),
                            ],
                            "indicators": {
                                "quote": [
                                    {
                                        "open": [1.0, 1.2],
                                        "high": [1.1, 1.3],
                                        "low": [0.9, 1.1],
                                        "close": [1.05, 1.25],
                                        "volume": [1000, 2000],
                                    }
                                ],
                                "adjclose": [{"adjclose": [1.01, 1.21]}],
                            },
                        }
                    ],
                    "error": None,
                }
            },
        )
    )

    response = await source.get_price_history("1592", start_date=start_date, end_date=end_date)

    assert route.called
    assert route.calls[0].request.url.params["interval"] == "1d"
    assert route.calls[0].request.url.params["includeAdjustedClose"] == "true"
    assert response.metadata.code == "01592"
    assert response.metadata.ticker == "01592.HK"
    assert response.metadata.source_name == "Yahoo Finance"
    assert response.metadata.adjustment_state == "adjusted"
    assert response.metadata.data_as_of == date(2026, 7, 20)
    assert response.prices[0].turnover == 1050.0
    assert response.prices[1].adjusted_close == 1.21
    assert response.data_quality_warnings == []


def test_api_price_history_endpoint_returns_json_payload():
    service = _price_history_response()

    class FixturePriceHistoryService:
        def __init__(self, response: PriceHistoryResponse):
            self.response = response
            self.calls = []

        async def get_price_history(self, code, start_date=None, end_date=None):
            self.calls.append((code, start_date, end_date))
            return self.response

    fixture_service = FixturePriceHistoryService(service)
    app.dependency_overrides[get_price_history_service] = lambda: fixture_service
    client = TestClient(app)
    try:
        response = client.get(
            "/api/v1/stocks/1592/prices",
            params={"start_date": "2026-07-19", "end_date": "2026-07-20"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["code"] == "01592"
    assert body["metadata"]["source_name"] == "Yahoo Finance"
    assert body["prices"][0]["price_date"] == "2026-07-19"
    assert fixture_service.calls == [("1592", date(2026, 7, 19), date(2026, 7, 20))]

from fastapi.testclient import TestClient

from app.api import app
from app.services.ccass import get_ccass_service
from ccass_core.report import SECTION_HEADINGS


class FixtureService:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def get_stock_data(self, code, holdings_limit=15):
        self.calls.append((code, holdings_limit))
        return self.response


def test_markdown_report_endpoint_reuses_core_without_breaking_json_api(current_response):
    service = FixtureService(current_response)
    app.dependency_overrides[get_ccass_service] = lambda: service
    client = TestClient(app)
    try:
        report_response = client.get(
            "/api/v1/ccass/1592/report",
            params={"holdings_limit": 25, "big_change_threshold": 500},
        )
        json_response = client.get("/api/v1/ccass/1592", params={"holdings_limit": 25})
    finally:
        app.dependency_overrides.clear()

    assert report_response.status_code == 200
    assert report_response.headers["content-type"].startswith("text/markdown")
    assert report_response.text.startswith("# CCASS Report — 01592")
    assert [line for line in report_response.text.splitlines() if line.startswith("## ")] == list(
        SECTION_HEADINGS
    )
    assert json_response.status_code == 200
    assert json_response.json()["metadata"]["code"] == "01592"
    assert service.calls == [("01592", 25), ("1592", 25)]

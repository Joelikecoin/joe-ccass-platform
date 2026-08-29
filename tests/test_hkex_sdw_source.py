from datetime import date
from pathlib import Path

import pytest

from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.domain.history import HistoricalSnapshot
from app.services.ccass import CcassService
from app.services.request_context import REQUESTED_CCASS_SNAPSHOT_DATE
from app.sources.hkex_sdw import FetchedPage, HKEXSdwClient
from app.sources.hkex_sdw_parser import parse_hkex_sdw_holdings
from app.sources.registry import WEBBSITE_SOURCE_ID
from app.storage.history import NormalizedSnapshotRepository
from app.streamlit_ui import PreparedReport, build_research_dashboard_markdown


def test_hkex_sdw_parser_accepts_existing_holdings_shape_and_txt_stock_code_fallback():
    html = """
    <html>
      <head><title>HKEX SDW Holdings</title></head>
      <body>
        <h2>FICTITIOUS LIMITED</h2>
        <p>CCASS holdings on 2026-07-20</p>
        <form>
          <input name="i" value="1592" />
          <input name="txtStockCode" value="01592" />
        </form>
        <div class="ccass-search-summary-table">
          <div class="ccass-search-datarow">
            <div class="summary-category">總數</div>
            <div class="shareholding"><div class="value">100</div></div>
            <div class="number-of-participants"><div class="value">2</div></div>
            <div class="percent-of-participants"><div class="value">80.0</div></div>
          </div>
          <div class="ccass-search-remarks"><div class="summary-value">125</div></div>
        </div>
        <table>
          <tr>
            <th>Rank</th><th>CCASS ID</th><th>Participant</th><th>Holding</th>
            <th>Last change</th><th>%</th><th>Cumul.</th>
          </tr>
          <tr>
            <td>1</td><td>A00001</td><td>Broker Alpha</td><td>60</td>
            <td>26-07-19</td><td>48.0</td><td>48.0</td>
          </tr>
          <tr>
            <td>2</td><td>B00002</td><td>Investor Beta</td><td>40</td>
            <td>2026-07-18</td><td>32.0</td><td>80.0</td>
          </tr>
        </table>
      </body>
    </html>
    """

    parsed = parse_hkex_sdw_holdings(html, requested_code="01592")

    assert parsed.code == "01592"
    assert parsed.issue_id == 1_592
    assert parsed.name == "FICTITIOUS LIMITED"
    assert parsed.holdings_date.isoformat() == "2026-07-20"
    assert parsed.holdings[0].last_change == date(2026, 7, 19)
    assert [row.rank for row in parsed.holdings] == [1, 2]
    assert parsed.holdings_summary.participant_count == 2
    assert parsed.holdings_summary.top5_pct_of_issued == 80.0


async def test_hkex_sdw_fetch_uses_landing_page_latest_available_date(monkeypatch):
    client = HKEXSdwClient(Settings())
    landing_html = """
    <html>
      <body>
        <input name="txtShareholdingDate" id="txtShareholdingDate" data-reset="2026/08/27" />
        <script>var options = { MAX: new Date('2026/08/27') };</script>
      </body>
    </html>
    """
    post_dates: list[str] = []

    async def fake_get_session_client():
        return object()

    async def fake_request_html(
        client,
        method: str,
        url: str,
        *,
        data=None,
        headers=None,
        phase: str,
    ):
        if phase == "landing":
            return FetchedPage(
                html=landing_html,
                source_url="https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx",
                cached=False,
            )
        post_dates.append(str((data or {}).get("txtShareholdingDate")))
        return FetchedPage(
            html="<html><body><table><tr><th>ok</th></tr><tr><td>1</td></tr></table></body></html>",
            source_url="https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx",
            cached=False,
        )

    monkeypatch.setattr(client, "_get_session_client", fake_get_session_client)
    monkeypatch.setattr(client, "_request_html", fake_request_html)

    page = await client._fetch_holdings_page("01682")

    assert post_dates == ["2026/08/27"]
    assert page.html.startswith("<html>")


async def test_hkex_sdw_fetch_uses_requested_historical_date_when_provided(monkeypatch):
    client = HKEXSdwClient(Settings())
    landing_html = """
    <html>
      <body>
        <input name="txtShareholdingDate" id="txtShareholdingDate" data-reset="2026/08/27" />
        <script>var options = { MAX: new Date('2026/08/27') };</script>
      </body>
    </html>
    """
    post_dates: list[str] = []

    async def fake_get_session_client():
        return object()

    async def fake_request_html(
        client,
        method: str,
        url: str,
        *,
        data=None,
        headers=None,
        phase: str,
    ):
        if phase == "landing":
            return FetchedPage(
                html=landing_html,
                source_url="https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx",
                cached=False,
            )
        post_dates.append(str((data or {}).get("txtShareholdingDate")))
        return FetchedPage(
            html="<html><body><table><tr><th>ok</th></tr><tr><td>1</td></tr></table></body></html>",
            source_url="https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx",
            cached=False,
        )

    monkeypatch.setattr(client, "_get_session_client", fake_get_session_client)
    monkeypatch.setattr(client, "_request_html", fake_request_html)

    token = REQUESTED_CCASS_SNAPSHOT_DATE.set(date(2026, 8, 26))
    try:
        page = await client._fetch_holdings_page("01682")
    finally:
        REQUESTED_CCASS_SNAPSHOT_DATE.reset(token)

    assert post_dates == ["2026/08/26"]
    assert page.html.startswith("<html>")


async def test_service_auto_routes_webbsite_failure_to_persistent_lkg_and_persists_snapshot(
    tmp_path,
    monkeypatch,
    current_response,
):
    webbsite_response = current_response.model_copy(
        update={
            "metadata": current_response.metadata.model_copy(
                update={
                    "source_name": "Webb-site mirror",
                    "source_url": "https://webb-database.com/ccass/choldings.asp",
                }
            )
        }
    )
    calls: list[str] = []

    class FailingWebbsite:
        def __init__(self, settings):
            self.settings = settings

        async def get_holdings(self, code, limit=15):
            calls.append("webbsite")
            raise PlatformError(
                ErrorCode.SOURCE_FORBIDDEN,
                "Webb-site mirror blocked in test fixture.",
                status_code=403,
            )

    class ForbiddenHKEX:
        def __init__(self, settings):
            raise AssertionError("HKEX SDW must not be constructed for auto routing")

        async def get_holdings(self, code, limit=15):
            raise AssertionError("HKEX SDW must not be used for auto routing")

    monkeypatch.setattr("app.services.ccass.WebbsiteClient", FailingWebbsite)
    monkeypatch.setattr("app.services.ccass.HKEXSdwClient", ForbiddenHKEX)

    repository = NormalizedSnapshotRepository(tmp_path / "ccass.db")
    repository.save(
        HistoricalSnapshot.from_response(
            webbsite_response,
            source_id=WEBBSITE_SOURCE_ID,
            parser_version="fixture-parser",
        )
    )
    service = CcassService(
        settings=Settings(holdings_lkg_max_age_seconds=1_000_000),
        lkg_repository=repository,
    )

    gateway_response = await service.get_stock_gateway_response("1592", holdings_limit=2)
    response = gateway_response.normalized_response
    dashboard = build_research_dashboard_markdown(
        PreparedReport(
            code=response.metadata.code,
            markdown="base",
            chatgpt_payload="payload",
            filename="01592_ccass_report.md",
            response=response,
        )
    )

    assert calls == ["webbsite"]
    assert gateway_response.routing.selected_source_id == "persistent_lkg"
    assert gateway_response.source_trace.selected_source_name == "Persistent LKG"
    assert gateway_response.source_trace.source_name == "Webb-site mirror"
    assert response.metadata.source_name == "Webb-site mirror"
    assert response.metadata.code == "01592"
    assert response.metadata.source_url.startswith("https://webb-database.com/")
    assert repository.count_snapshots("01592") == 1
    assert repository.latest("01592", source_id=WEBBSITE_SOURCE_ID) is not None
    assert dashboard.startswith("###")
    assert "01592" in dashboard


async def test_service_auto_fails_loudly_without_local_snapshot(
    tmp_path,
    monkeypatch,
    current_response,
):
    repository = NormalizedSnapshotRepository(tmp_path / "lkg.db")
    calls: list[str] = []

    class FailingWebbsite:
        def __init__(self, settings):
            self.settings = settings

        async def get_holdings(self, code, limit=15):
            calls.append("webbsite")
            raise PlatformError(
                ErrorCode.SOURCE_FORBIDDEN,
                "Webb-site mirror blocked in test fixture.",
                status_code=403,
            )

    class ForbiddenHKEX:
        def __init__(self, settings):
            raise AssertionError("HKEX SDW must not be constructed for auto routing")

        async def get_holdings(self, code, limit=15):
            raise AssertionError("HKEX SDW must not be used for auto routing")

    monkeypatch.setattr("app.services.ccass.WebbsiteClient", FailingWebbsite)
    monkeypatch.setattr("app.services.ccass.HKEXSdwClient", ForbiddenHKEX)

    service = CcassService(
        settings=Settings(holdings_lkg_max_age_seconds=1_000_000),
        lkg_repository=repository,
    )

    with pytest.raises(PlatformError) as caught:
        await service.get_stock_gateway_response("1592", holdings_limit=2)

    assert calls == ["webbsite"]
    assert caught.value.code in {ErrorCode.SOURCE_FORBIDDEN, ErrorCode.SOURCE_UNAVAILABLE}

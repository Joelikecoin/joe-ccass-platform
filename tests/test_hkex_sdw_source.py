from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.services.ccass import CcassService
from app.sources.hkex_sdw_parser import parse_hkex_sdw_holdings
from app.sources.registry import HKEX_SDW_SOURCE_ID
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
          <input name="txtStockCode" value="01592" />
        </form>
        <table>
          <tr><td>Total in CCASS</td><td>100</td><td>80.0</td></tr>
          <tr><td>Issued securities</td><td>125</td><td>100.0</td></tr>
          <tr><td>Securities not in CCASS</td><td>25</td><td>20.0</td></tr>
        </table>
        <table>
          <tr>
            <th>Rank</th><th>CCASS ID</th><th>Participant</th><th>Holding</th>
            <th>Last change</th><th>%</th><th>Cumul.</th>
          </tr>
          <tr>
            <td>1</td><td>A00001</td><td>Broker Alpha</td><td>60</td>
            <td>2026-07-19</td><td>48.0</td><td>48.0</td>
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
    assert [row.rank for row in parsed.holdings] == [1, 2]
    assert parsed.holdings_summary.participant_count == 2
    assert parsed.holdings_summary.top5_pct_of_issued == 80.0


async def test_service_auto_routes_webbsite_failure_to_hkex_sdw_and_persists_snapshot(
    tmp_path,
    monkeypatch,
    current_response,
):
    hkex_response = current_response.model_copy(
        update={
            "metadata": current_response.metadata.model_copy(
                update={
                    "source_name": "HKEX SDW",
                    "source_url": "https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx",
                }
            )
        }
    )
    calls: list[str] = []

    class FailingWebbsite:
        def __init__(self, settings):
            calls.append("webbsite")

        async def get_holdings(self, code, limit=15):
            raise PlatformError(
                ErrorCode.SOURCE_FORBIDDEN,
                "Webb-site mirror blocked in test fixture.",
                status_code=403,
            )

    class FixtureHKEX:
        def __init__(self, settings):
            calls.append("hkex")

        async def get_holdings(self, code, limit=15):
            return hkex_response.model_copy(deep=True)

    def fail_csv(*args, **kwargs):  # pragma: no cover - defensive
        raise AssertionError("CSV fallback must not be selected when HKEX succeeds")

    monkeypatch.setattr("app.services.ccass.WebbsiteClient", FailingWebbsite)
    monkeypatch.setattr("app.services.ccass.HKEXSdwClient", FixtureHKEX)
    monkeypatch.setattr("app.services.ccass.GoogleDriveCsvSource", fail_csv)

    repository = NormalizedSnapshotRepository(tmp_path / "ccass.db")
    service = CcassService(
        settings=Settings(),
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

    assert calls == ["webbsite", "hkex"]
    assert gateway_response.routing.selected_source_id == HKEX_SDW_SOURCE_ID
    assert gateway_response.source_trace.source_name == "HKEX SDW"
    assert response.metadata.source_name == "HKEX SDW"
    assert response.metadata.code == "01592"
    assert response.metadata.source_url.startswith("https://www3.hkexnews.hk/")
    assert repository.count_snapshots("01592") == 1
    assert repository.latest("01592", source_id=HKEX_SDW_SOURCE_ID) is not None
    assert dashboard.startswith("###")
    assert "01592" in dashboard

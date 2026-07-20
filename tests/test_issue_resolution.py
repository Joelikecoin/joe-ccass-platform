import pytest

from app.config import Settings
from app.errors import ErrorCode, PlatformError
from app.sources.webbsite import WebbsiteClient


MULTI_SECURITY_HTML = """
<html><body><div class="mainbody">
<h2>TENCENT HOLDINGS LIMITED 騰訊控股有限公司</h2>
<h4>Ordinary shares: HKD</h4>
<table><tr><th>Code</th></tr><tr><td>00700</td></tr></table>
<div class="clear"></div>
<ul><li><a href="/ccass/choldings.asp?i=3601">CCASS</a></li></ul>
<div class="clear"></div>
<h4>Ordinary shares: CNY</h4>
<table><tr><th>Code</th></tr><tr><td>80700</td></tr></table>
<div class="clear"></div>
<ul><li><a href="/ccass/choldings.asp?i=34309">CCASS</a></li></ul>
</div></body></html>
"""


@pytest.mark.parametrize(("code", "expected"), [("00700", 3601), ("80700", 34309)])
async def test_resolve_issue_id_matches_exact_security_block(code, expected):
    client = WebbsiteClient(Settings(min_request_interval_seconds=0))

    async def fake_fetch(path, params):
        return MULTI_SECURITY_HTML, "https://example.test/orgdata", False

    client._fetch = fake_fetch
    issue_id, name = await client.resolve_issue_id(code)

    assert issue_id == expected
    assert name == "TENCENT HOLDINGS LIMITED 騰訊控股有限公司"


DIRECT_HOLDINGS_HTML = """
<html><body>
<h2>TENCENT HOLDINGS LIMITED: O HKD</h2>
<table><tr><td>00700</td></tr></table>
<form><input type="hidden" name="i" value="3601"></form>
</body></html>
"""


async def test_get_holdings_uses_single_verified_stock_code_request(monkeypatch):
    client = WebbsiteClient(Settings(min_request_interval_seconds=0))
    calls = []

    async def fake_fetch(path, params):
        calls.append((path, params))
        return DIRECT_HOLDINGS_HTML, "https://example.test/holdings", False

    monkeypatch.setattr(client, "_fetch", fake_fetch)
    monkeypatch.setattr(client, "parse_holdings", lambda *args, **kwargs: kwargs)

    result = await client.get_holdings("00700", limit=5)

    assert calls == [("/ccass/choldings.asp", {"sc": "700"})]
    assert result["issue_id"] == 3601
    assert result["resolved_name"] == "TENCENT HOLDINGS LIMITED: O HKD"
    assert result["limit"] == 5


@pytest.mark.parametrize(
    "html",
    [
        DIRECT_HOLDINGS_HTML.replace("00700", "80700"),
        DIRECT_HOLDINGS_HTML.replace('name="i" value="3601"', 'name="i" value=""'),
    ],
)
def test_direct_holdings_identity_rejects_unverified_page(html):
    with pytest.raises(PlatformError) as caught:
        WebbsiteClient._resolve_holdings_identity(html, "00700")

    assert caught.value.code == ErrorCode.NOT_FOUND
    assert caught.value.status_code == 404

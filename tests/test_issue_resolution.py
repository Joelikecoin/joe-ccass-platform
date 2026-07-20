import pytest

from app.config import Settings
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

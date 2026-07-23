from app.config import Settings
from app.models import CcassResponse
from app.sources.webbsite import WebbsiteClient
from app.sources.webbsite_parser import ParsedWebbsiteHoldings, parse_webbsite_holdings


async def fetch_webb_holdings(
    code: str,
    *,
    limit: int = 100,
    settings: Settings | None = None,
    client: WebbsiteClient | None = None,
) -> CcassResponse:
    """Fetch holdings through the low-frequency public mirror client."""
    source = client or WebbsiteClient(settings)
    return await source.get_holdings(code, limit=limit)


def parse_webb_holdings(html: str, *, requested_code: str) -> ParsedWebbsiteHoldings:
    """Expose the pure production parser for deterministic fixture reuse."""
    return parse_webbsite_holdings(html, requested_code=requested_code)

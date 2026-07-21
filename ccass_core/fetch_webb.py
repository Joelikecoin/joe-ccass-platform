from app.config import Settings
from app.models import CcassResponse
from app.sources.webbsite import WebbsiteClient


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


def parse_webb_holdings(*args, **kwargs) -> CcassResponse:
    """Expose the production mirror parser for collector and fixture reuse."""
    return WebbsiteClient.parse_holdings(*args, **kwargs)

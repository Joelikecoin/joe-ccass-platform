from functools import lru_cache

from app.core.normalizers import normalize_stock_code
from app.models import CcassResponse
from app.sources.webbsite import WebbsiteClient


class CcassService:
    def __init__(self, client: WebbsiteClient | None = None) -> None:
        self.client = client or WebbsiteClient()

    async def get_stock_data(self, code: str | int, holdings_limit: int = 15) -> CcassResponse:
        normalized = normalize_stock_code(code)
        return await self.client.get_holdings(normalized, limit=holdings_limit)


@lru_cache
def get_ccass_service() -> CcassService:
    return CcassService()

from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings
from app.longbridge_persistence import build_response, persist_response
from app.models import CcassResponse
from app.sources.longbridge import LongbridgeMcpClient, normalize_longbridge_symbol


class LongbridgeHoldingsService:
    def __init__(self, *, settings: Settings | None = None, client: LongbridgeMcpClient | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = client or LongbridgeMcpClient()

    async def fetch_and_persist(self, stock_code: str) -> CcassResponse:
        symbol = normalize_longbridge_symbol(stock_code)
        payload = await self.client.broker_holding_detail(symbol)
        response = build_response(payload, stock_code=stock_code, issue_id=0)
        persist_response(response, db_path=Path(self.settings.ccass_sqlite_path))
        return response


def get_longbridge_holdings_service() -> LongbridgeHoldingsService:
    return LongbridgeHoldingsService()

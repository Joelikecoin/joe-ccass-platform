from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any, Iterable


@dataclass(slots=True)
class _HistoryFrame:
    rows: list[dict[str, Any]]

    @property
    def empty(self) -> bool:
        return not self.rows

    def reset_index(self) -> "_HistoryFrame":
        return self

    def iterrows(self) -> Iterable[tuple[int, dict[str, Any]]]:
        return enumerate(self.rows)


class Ticker:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def history(
        self,
        *,
        period: str = "1y",
        interval: str = "1d",
        auto_adjust: bool = False,
        actions: bool = True,
    ) -> _HistoryFrame:
        del interval, auto_adjust, actions
        from app.services.price_history import get_price_history_service

        end_date = date.today()
        if period == "max":
            start_date = end_date - timedelta(days=3650)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "6mo":
            start_date = end_date - timedelta(days=183)
        else:
            start_date = end_date - timedelta(days=90)

        response = _run_async(
            get_price_history_service().get_price_history(
                self.symbol,
                start_date=start_date,
                end_date=end_date,
            )
        )
        if response is None or not response.prices:
            return _HistoryFrame(rows=[])

        rows: list[dict[str, Any]] = []
        for row in response.prices:
            rows.append(
                {
                    "Date": row.price_date,
                    "Open": row.open,
                    "High": row.high,
                    "Low": row.low,
                    "Close": row.close,
                    "Volume": row.volume,
                    "Dividends": 0.0,
                    "Stock Splits": 0.0,
                }
            )
        return _HistoryFrame(rows=rows)


def _run_async(awaitable: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)
    # If a loop already exists, run in a fresh nested loop on a worker thread.
    result: list[Any] = []
    error: list[BaseException] = []

    def _worker() -> None:
        try:
            result.append(asyncio.run(awaitable))
        except BaseException as exc:  # pragma: no cover - defensive bridge
            error.append(exc)

    import threading

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    thread.join()
    if error:
        raise error[0]
    return result[0] if result else None


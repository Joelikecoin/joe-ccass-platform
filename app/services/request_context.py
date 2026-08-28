from __future__ import annotations

from contextvars import ContextVar
from datetime import date


REQUESTED_CCASS_SNAPSHOT_DATE: ContextVar[date | None] = ContextVar(
    "requested_ccass_snapshot_date",
    default=None,
)

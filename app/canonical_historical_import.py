from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, TextIO


REQUIRED_COLUMNS = (
    "stock_code",
    "stock_name",
    "snapshot_date",
    "source_id",
    "source_url",
    "source_fetched_at",
    "source_data_as_of",
    "participant_id",
    "participant_name",
    "participant_category",
    "holding_shares",
    "issued_shares",
    "ccass_total_shares",
    "stake_pct_of_issued",
    "stake_pct_of_ccass",
    "rank",
    "is_partial",
    "data_quality_status",
    "warning",
    "provenance_note",
)
OPTIONAL_COLUMNS = (
    "issue_id",
    "last_change_date",
    "raw_participant_name",
    "raw_holding_value",
    "raw_source_payload_ref",
    "import_batch_id",
)
_PARTICIPANT_ID = re.compile(r"^[A-C]\d{5}$")
_STOCK_CODE = re.compile(r"^\d{5}$")


class CanonicalImportError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CanonicalHolding:
    stock_code: str
    stock_name: str
    snapshot_date: date
    source_id: str
    source_url: str
    source_fetched_at: datetime
    source_data_as_of: date
    participant_id: str
    participant_name: str
    participant_category: str
    holding_shares: int
    issued_shares: int | None
    ccass_total_shares: int | None
    stake_pct_of_issued: Decimal | None
    stake_pct_of_ccass: Decimal | None
    rank: int
    is_partial: bool
    data_quality_status: str
    warning: str
    provenance_note: str
    issue_id: int | None = None
    last_change_date: date | None = None
    raw_participant_name: str | None = None
    raw_holding_value: str | None = None
    raw_source_payload_ref: str | None = None
    import_batch_id: str | None = None

    @property
    def import_key(self) -> tuple[str, date, str]:
        return self.stock_code, self.snapshot_date, self.participant_id


@dataclass(frozen=True, slots=True)
class CanonicalImportResult:
    accepted_rows: tuple[CanonicalHolding, ...]
    rejected_rows: tuple[dict[str, object], ...]
    warnings: tuple[str, ...]
    snapshot_dates: tuple[date, ...]
    stocks: tuple[str, ...]
    sources: tuple[str, ...]
    dry_run: bool

    @property
    def usable(self) -> bool:
        return bool(self.accepted_rows) and not (
            self.rejected_rows and not self.accepted_rows
        )


class CanonicalImportWriter:
    def save(self, row: CanonicalHolding) -> None:
        raise NotImplementedError


def import_canonical_csv(
    source: str | Path | TextIO,
    *,
    dry_run: bool = True,
    writer: CanonicalImportWriter | None = None,
) -> CanonicalImportResult:
    if not dry_run and writer is None:
        raise CanonicalImportError("a writer is required when dry_run is false")
    close_source = False
    if isinstance(source, (str, Path)):
        handle = Path(source).open("r", encoding="utf-8", newline="")
        close_source = True
    else:
        handle = source
    try:
        reader = csv.DictReader(handle)
        columns = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in columns]
        if missing:
            raise CanonicalImportError(f"missing required columns: {', '.join(missing)}")
        accepted: list[CanonicalHolding] = []
        rejected: list[dict[str, object]] = []
        seen: dict[tuple[str, date, str], CanonicalHolding] = {}
        warnings: list[str] = []
        for line_number, raw in enumerate(reader, start=2):
            try:
                row = _parse_row(raw)
                prior = seen.get(row.import_key)
                if prior is not None:
                    if prior != row:
                        raise CanonicalImportError("conflicting duplicate import key")
                    warnings.append(f"line {line_number}: identical duplicate ignored")
                    continue
                seen[row.import_key] = row
                accepted.append(row)
            except CanonicalImportError as exc:
                if str(exc) == "conflicting duplicate import key":
                    raise
                rejected.append({"line": line_number, "error": str(exc)})
            except (ValueError, InvalidOperation) as exc:
                rejected.append({"line": line_number, "error": str(exc)})
        if not accepted and rejected:
            raise CanonicalImportError("canonical import contains no usable rows")
        if not dry_run and writer is not None:
            for row in accepted:
                writer.save(row)
        return CanonicalImportResult(
            accepted_rows=tuple(accepted),
            rejected_rows=tuple(rejected),
            warnings=tuple(warnings),
            snapshot_dates=tuple(sorted({row.snapshot_date for row in accepted})),
            stocks=tuple(sorted({row.stock_code for row in accepted})),
            sources=tuple(sorted({row.source_id for row in accepted})),
            dry_run=dry_run,
        )
    finally:
        if close_source:
            handle.close()


def _parse_row(raw: dict[str, str | None]) -> CanonicalHolding:
    def required(name: str) -> str:
        value = (raw.get(name) or "").strip()
        if not value:
            raise CanonicalImportError(f"{name} is required")
        return value

    stock_code = required("stock_code")
    if not _STOCK_CODE.fullmatch(stock_code):
        raise CanonicalImportError("stock_code must be exactly five digits")
    participant_id = required("participant_id").upper()
    if not _PARTICIPANT_ID.fullmatch(participant_id):
        raise CanonicalImportError("participant_id must match A-C followed by five digits")
    holding_shares = _integer(required("holding_shares"), "holding_shares")
    if holding_shares < 0:
        raise CanonicalImportError("holding_shares cannot be negative")
    issued_shares = _optional_integer(raw.get("issued_shares"), "issued_shares")
    ccass_total_shares = _optional_integer(raw.get("ccass_total_shares"), "ccass_total_shares")
    if issued_shares is not None and issued_shares < 0:
        raise CanonicalImportError("issued_shares cannot be negative")
    if ccass_total_shares is not None and ccass_total_shares < 0:
        raise CanonicalImportError("ccass_total_shares cannot be negative")
    pct_issued = _optional_decimal(raw.get("stake_pct_of_issued"), "stake_pct_of_issued")
    pct_ccass = _optional_decimal(raw.get("stake_pct_of_ccass"), "stake_pct_of_ccass")
    if pct_issued is not None and issued_shares is None:
        raise CanonicalImportError("stake_pct_of_issued requires issued_shares")
    if pct_ccass is not None and ccass_total_shares is None:
        raise CanonicalImportError("stake_pct_of_ccass requires ccass_total_shares")
    if issued_shares and pct_issued is not None and not _close(pct_issued, holding_shares * 100 / issued_shares):
        raise CanonicalImportError("stake_pct_of_issued contradicts absolute shares")
    if ccass_total_shares and pct_ccass is not None and not _close(pct_ccass, holding_shares * 100 / ccass_total_shares):
        raise CanonicalImportError("stake_pct_of_ccass contradicts absolute shares")
    partial = _boolean(required("is_partial"), "is_partial")
    return CanonicalHolding(
        stock_code=stock_code,
        stock_name=required("stock_name"),
        snapshot_date=_iso_date(required("snapshot_date"), "snapshot_date"),
        source_id=required("source_id"),
        source_url=required("source_url"),
        source_fetched_at=_iso_datetime(required("source_fetched_at"), "source_fetched_at"),
        source_data_as_of=_iso_date(required("source_data_as_of"), "source_data_as_of"),
        participant_id=participant_id,
        participant_name=required("participant_name"),
        participant_category=required("participant_category"),
        holding_shares=holding_shares,
        issued_shares=issued_shares,
        ccass_total_shares=ccass_total_shares,
        stake_pct_of_issued=pct_issued,
        stake_pct_of_ccass=pct_ccass,
        rank=_positive_integer(required("rank"), "rank"),
        is_partial=partial,
        data_quality_status=required("data_quality_status"),
        warning=(raw.get("warning") or "").strip(),
        provenance_note=required("provenance_note"),
        issue_id=_optional_integer(raw.get("issue_id"), "issue_id"),
        last_change_date=_optional_date(raw.get("last_change_date"), "last_change_date"),
        raw_participant_name=(raw.get("raw_participant_name") or "").strip() or None,
        raw_holding_value=(raw.get("raw_holding_value") or "").strip() or None,
        raw_source_payload_ref=(raw.get("raw_source_payload_ref") or "").strip() or None,
        import_batch_id=(raw.get("import_batch_id") or "").strip() or None,
    )


def _iso_date(value: str, label: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise CanonicalImportError(f"{label} must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise CanonicalImportError(f"{label} must use YYYY-MM-DD")
    return parsed


def _iso_datetime(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CanonicalImportError(f"{label} must be an ISO datetime") from exc
    if parsed.tzinfo is None:
        raise CanonicalImportError(f"{label} must include a timezone")
    return parsed


def _optional_date(value: str | None, label: str) -> date | None:
    return _iso_date(value.strip(), label) if value and value.strip() else None


def _integer(value: str, label: str) -> int:
    try:
        parsed = int(value.replace(",", ""))
    except ValueError as exc:
        raise CanonicalImportError(f"{label} must be an integer") from exc
    return parsed


def _optional_integer(value: str | None, label: str) -> int | None:
    return _integer(value.strip(), label) if value and value.strip() else None


def _positive_integer(value: str, label: str) -> int:
    parsed = _integer(value, label)
    if parsed <= 0:
        raise CanonicalImportError(f"{label} must be positive")
    return parsed


def _optional_decimal(value: str | None, label: str) -> Decimal | None:
    if not value or not value.strip():
        return None
    normalized = value.strip().removesuffix("%").strip()
    try:
        parsed = Decimal(normalized)
    except InvalidOperation as exc:
        raise CanonicalImportError(f"{label} must be numeric") from exc
    if parsed < 0:
        raise CanonicalImportError(f"{label} cannot be negative")
    return parsed


def _boolean(value: str, label: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    raise CanonicalImportError(f"{label} must be true or false")


def _close(left: Decimal, right: float) -> bool:
    return abs(float(left) - right) <= 0.01

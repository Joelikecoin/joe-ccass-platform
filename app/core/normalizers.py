import re
from datetime import date

from ccass_core.normalize import normalize_stock_code

__all__ = [
    "classify_participant",
    "normalize_stock_code",
    "parse_float",
    "parse_int",
    "parse_iso_date",
]


def parse_int(value: str) -> int:
    cleaned = re.sub(r"[^\d-]", "", value or "")
    if cleaned in {"", "-"}:
        raise ValueError(f"Not an integer: {value!r}")
    return int(cleaned)


def parse_float(value: str) -> float:
    cleaned = re.sub(r"[^\d.\-]", "", value or "")
    if cleaned in {"", "-", "."}:
        raise ValueError(f"Not a number: {value!r}")
    return float(cleaned)


def parse_iso_date(value: str) -> date | None:
    match = re.search(r"\d{4}-\d{2}-\d{2}", value or "")
    return date.fromisoformat(match.group(0)) if match else None


def classify_participant(participant_id: str, name: str) -> str:
    upper = name.upper()
    retail_tokens = ("FUTU", "BRIGHT SMART", "TIGER", "INTERACTIVE BROKERS", "WEBULL", "USMART")
    bank_tokens = ("BANK", "HSBC", "CITIBANK", "STANDARD CHARTERED")
    if any(token in upper for token in retail_tokens):
        return "retail"
    if participant_id.startswith("C") or any(token in upper for token in bank_tokens):
        return "bank_or_custodian"
    if participant_id.startswith("B"):
        return "broker"
    return "other"

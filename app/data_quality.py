from __future__ import annotations

from dataclasses import dataclass


PREFIX_SEPARATOR = ": "
MESSAGE_SEPARATOR = " | "


@dataclass(frozen=True, slots=True)
class ParsedWarning:
    prefix: str
    code: str
    message: str | None = None


def structured_warning(prefix: str, code: str, message: str) -> str:
    if not prefix.strip():
        raise ValueError("warning prefix must be non-empty")
    code_text = str(code).strip()
    if not code_text:
        raise ValueError("warning code must be non-empty")
    if not message.strip():
        raise ValueError("warning message must be non-empty")
    return f"{prefix.strip()}: {code_text}{MESSAGE_SEPARATOR}{message.strip()}"


def parse_warning(warning: str) -> ParsedWarning | None:
    if PREFIX_SEPARATOR not in warning:
        return None
    prefix, remainder = warning.split(PREFIX_SEPARATOR, 1)
    if MESSAGE_SEPARATOR in remainder:
        code, message = remainder.split(MESSAGE_SEPARATOR, 1)
        return ParsedWarning(prefix=prefix, code=code, message=message)
    return ParsedWarning(prefix=prefix, code=remainder, message=None)


def warning_message(warning: str) -> str:
    parsed = parse_warning(warning)
    if parsed is None:
        return warning
    if parsed.prefix in {
        "CHANGES_VALIDATION",
        "BIG_CHANGES_VALIDATION",
        "CONCENTRATION_VALIDATION",
    } and parsed.message is None:
        return warning
    return parsed.message or parsed.code


def warning_code(warning: str) -> str | None:
    parsed = parse_warning(warning)
    return parsed.code if parsed else None

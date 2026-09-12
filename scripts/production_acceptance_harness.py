"""Non-invasive production acceptance harness for the Longbridge chain."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

RESULT_STATES = {"PASS", "PARTIAL", "STALE", "UNAVAILABLE", "ERROR", "BLOCKED"}
DEFAULT_STOCKS = ("00005", "06182")


@dataclass
class CheckResult:
    name: str
    state: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.state not in RESULT_STATES:
            raise ValueError(f"invalid acceptance state: {self.state}")


@dataclass
class HarnessReport:
    mode: str
    started_at: str
    finished_at: str | None
    checks: list[CheckResult]
    stocks: list[str]
    write_enabled: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "stocks": self.stocks,
            "write_enabled": self.write_enabled,
            "checks": [asdict(check) for check in self.checks],
        }


class AcceptanceHarness:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        stocks: tuple[str, ...],
        timeout_seconds: float = 90.0,
        write_enabled: bool = False,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.api_key = api_key
        self.stocks = stocks
        self.timeout_seconds = timeout_seconds
        self.write_enabled = write_enabled
        self.client = client or httpx.Client(timeout=timeout_seconds, follow_redirects=False)
        self.checks: list[CheckResult] = []

    def close(self) -> None:
        self.client.close()

    def run(self) -> HarnessReport:
        started = datetime.now().astimezone().isoformat()
        self._preflight()
        for stock in self.stocks:
            self._holdings(stock)
        if self.write_enabled:
            self._persistence_opt_in()
        else:
            self.checks.append(CheckResult(
                "persistence",
                "BLOCKED",
                "Read-only default: production write/read-back proof requires explicit opt-in.",
            ))
        self._derived_checks()
        finished = datetime.now().astimezone().isoformat()
        return HarnessReport(
            mode="WRITE_ENABLED" if self.write_enabled else "DRY_RUN_READ_ONLY",
            started_at=started,
            finished_at=finished,
            checks=self.checks,
            stocks=list(self.stocks),
            write_enabled=self.write_enabled,
        )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> tuple[httpx.Response | None, float, str | None]:
        started = time.monotonic()
        try:
            response = self.client.get(urljoin(self.base_url, path.lstrip("/")), headers=self._headers(), params=params)
            return response, time.monotonic() - started, None
        except httpx.TimeoutException as exc:
            return None, time.monotonic() - started, type(exc).__name__
        except httpx.HTTPError as exc:
            return None, time.monotonic() - started, type(exc).__name__

    def _preflight(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            self.checks.append(CheckResult("base_url", "ERROR", "BASE_URL must include http(s) scheme and host."))
            return
        self.checks.append(CheckResult("base_url", "PASS", "Base URL format is valid.", {"host": parsed.netloc}))
        if not self.api_key:
            self.checks.append(CheckResult("auth", "BLOCKED", "API key is absent; authenticated checks cannot run.", {"state": "BLOCKED_AUTH"}))
        else:
            self.checks.append(CheckResult("auth", "PASS", "Authorization header will be constructed from environment input."))
        response, elapsed, error = self._get("/health")
        if error:
            self.checks.append(self._timed_result("health", elapsed, error))
        elif response is not None and response.status_code == 200:
            self.checks.append(CheckResult("health", "PASS", "Health endpoint returned HTTP 200.", {"elapsed_s": round(elapsed, 3)}))
        else:
            self.checks.append(CheckResult("health", "UNAVAILABLE", "Health endpoint did not return HTTP 200.", {"status_code": response.status_code if response else None, "elapsed_s": round(elapsed, 3)}))
        response, elapsed, error = self._get("/openapi.json")
        if error:
            self.checks.append(CheckResult("routes", "UNAVAILABLE", "OpenAPI could not be read.", {"error": error}))
        elif response is not None and response.status_code == 200:
            try:
                paths = response.json().get("paths", {})
                required = {"/api/v1/stocks/{stock_code}/holdings", "/api/v1/stocks/{stock_code}/changes", "/api/v1/stocks/{stock_code}/big-changes", "/api/v1/stocks/{stock_code}/concentration"}
                missing = sorted(required - set(paths))
                self.checks.append(CheckResult("routes", "PASS" if not missing else "PARTIAL", "OpenAPI route contract inspected.", {"missing": missing, "elapsed_s": round(elapsed, 3)}))
            except (ValueError, AttributeError):
                self.checks.append(CheckResult("routes", "ERROR", "OpenAPI response was not valid JSON."))
        else:
            self.checks.append(CheckResult("routes", "UNAVAILABLE", "OpenAPI did not return HTTP 200.", {"status_code": response.status_code if response else None}))

    def _holdings(self, stock: str) -> None:
        response, elapsed, error = self._get(f"/api/v1/stocks/{stock}/holdings")
        if error:
            self.checks.append(self._timed_result(f"holdings:{stock}", elapsed, error))
            return
        if response is None:
            self.checks.append(CheckResult(f"holdings:{stock}", "ERROR", "No response received."))
            return
        if response.status_code in {401, 403}:
            self.checks.append(CheckResult(f"holdings:{stock}", "BLOCKED", "Authentication is required.", {"state": "BLOCKED_AUTH", "status_code": response.status_code}))
            return
        if response.status_code >= 500:
            self.checks.append(CheckResult(f"holdings:{stock}", "UNAVAILABLE", "Production route returned a server failure.", {"status_code": response.status_code, "elapsed_s": round(elapsed, 3)}))
            return
        try:
            payload = response.json()
        except ValueError:
            self.checks.append(CheckResult(f"holdings:{stock}", "ERROR", "Holdings response was not JSON.", {"status_code": response.status_code}))
            return
        metadata = payload.get("metadata") or {}
        rows = payload.get("holdings") or []
        source = str(metadata.get("source_id") or metadata.get("source_name") or "").lower()
        cached = bool(metadata.get("cached"))
        stale = "STALE_LKG" in json.dumps(payload).upper() or bool(metadata.get("stale"))
        has_dates = bool(metadata.get("fetched_at")) and bool(metadata.get("holdings_date") or metadata.get("data_as_of"))
        state = "PASS" if response.status_code == 200 and source == "longbridge" and rows and has_dates and not cached and not stale else ("STALE" if stale else "PARTIAL" if response.status_code < 400 else "ERROR")
        self.checks.append(CheckResult(f"holdings:{stock}", state, "Holdings metadata and live-source contract evaluated.", {"status_code": response.status_code, "source": source, "rows": len(rows), "cached": cached, "stale": stale, "elapsed_s": round(elapsed, 3), "target_le_60s": elapsed <= 60, "hard_limit_le_90s": elapsed <= 90}))

    def _persistence_opt_in(self) -> None:
        self.checks.append(CheckResult("persistence", "BLOCKED", "Write-enabled mode is explicit but no write was executed by this harness; use the documented admin job separately.", {"write_capable": False}))

    def _derived_checks(self) -> None:
        self.checks.append(CheckResult("derived_chain", "BLOCKED", "Requires two authenticated persisted snapshot dates; harness does not invent dates or infer production evidence."))

    def _timed_result(self, name: str, elapsed: float, error: str) -> CheckResult:
        state = "ERROR" if elapsed <= 90 else "UNAVAILABLE"
        return CheckResult(name, state, "Request did not reach a terminal response.", {"error": error, "elapsed_s": round(elapsed, 3), "target_le_60s": elapsed <= 60, "hard_limit_le_90s": elapsed <= 90})


def normalize_stock(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if not digits or len(digits) > 5:
        raise ValueError(f"invalid stock code: {value!r}")
    return digits.zfill(5)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("CCASS_ACCEPTANCE_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--stock", action="append", dest="stocks", help="Stock code; repeatable. Defaults to 00005 and 06182.")
    parser.add_argument("--timeout", type=float, default=float(os.getenv("CCASS_ACCEPTANCE_TIMEOUT_SECONDS", "90")))
    parser.add_argument("--write-enabled", action="store_true", help="Opt in to write-mode reporting; no write is performed automatically.")
    args = parser.parse_args(argv)
    allow_writes = os.getenv("CCASS_ACCEPTANCE_ALLOW_WRITES") == "1"
    if args.write_enabled and not allow_writes:
        print(json.dumps({"state": "BLOCKED", "reason": "Set CCASS_ACCEPTANCE_ALLOW_WRITES=1 for write-enabled mode."}, indent=2))
        return 2
    stocks = tuple(normalize_stock(value) for value in (args.stocks or DEFAULT_STOCKS))
    harness = AcceptanceHarness(base_url=args.base_url, api_key=os.getenv("CCASS_API_KEY"), stocks=stocks, timeout_seconds=args.timeout, write_enabled=args.write_enabled)
    try:
        report = harness.run()
    finally:
        harness.close()
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    return 0 if not any(check.state == "ERROR" for check in report.checks) else 1


if __name__ == "__main__":
    sys.exit(main())

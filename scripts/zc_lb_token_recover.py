"""Recover the Longbridge MCP token from local Codex artifacts and probe it.

Scans likely files for LONGBRIDGE_ACCESS_TOKEN candidates, probes each against
the live MCP endpoint, and writes the first VALID token into .env (LF endings).
Never prints the token itself - only length and last 4 chars.
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
REPO = Path(__file__).resolve().parent.parent

CANDIDATE_FILES = [
    HOME / ".codex" / ".codex-global-state.json",
    HOME / ".codex" / ".codex-global-state.json.bak",
    *(sorted((HOME / ".codex" / "attachments").glob("**/*.txt")) if (HOME / ".codex" / "attachments").is_dir() else []),
    HOME / ".codex" / "archived_sessions" / "rollout-2026-08-02T23-14-18-019fc30a-4592-77c3-a7a9-5379a39da052.jsonl",
]

TOKEN_RE = re.compile(r"LONGBRIDGE_ACCESS_TOKEN[\s\"'=:\\n]+([A-Za-z0-9._\-]{20,})")


def collect_candidates() -> list[str]:
    seen: list[str] = []
    for path in CANDIDATE_FILES:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            print(f"skip {path.name}: {type(exc).__name__}")
            continue
        for match in TOKEN_RE.findall(text):
            if match not in seen:
                seen.append(match)
                print(f"candidate from {path.name}: len={len(match)} tail=...{match[-4:]}")
    return seen


async def probe(token: str) -> bool:
    from app.sources.longbridge import LongbridgeMcpClient

    client = LongbridgeMcpClient(access_token=token)
    try:
        result = await client._call_tool("broker_holding_detail", {"symbol": "1.HK"})
        rows = result if isinstance(result, list) else result.get("list") or []
        print(f"probe ok: rows={len(rows)}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"probe reject: {type(exc).__name__} {str(exc)[:120]}")
        return False


def write_env(token: str) -> None:
    env_path = REPO / ".env"
    text = env_path.read_text(encoding="utf-8") if env_path.is_file() else ""
    text = re.sub(r"(?m)^LONGBRIDGE_ACCESS_TOKEN=.*$\n?", "", text)
    if text and not text.endswith("\n"):
        text += "\n"
    text += f"LONGBRIDGE_ACCESS_TOKEN={token}\n"
    env_path.write_text(text, encoding="utf-8", newline="\n")
    print(".env updated (LF endings)")


def main() -> int:
    candidates = collect_candidates()
    if not candidates:
        print("NO_CANDIDATES")
        return 2
    for token in candidates:
        print(f"probing len={len(token)} tail=...{token[-4:]}")
        if asyncio.run(probe(token)):
            write_env(token)
            print("VERDICT TOKEN_RECOVERED")
            return 0
    print("VERDICT ALL_REJECTED")
    return 1


if __name__ == "__main__":
    sys.exit(main())

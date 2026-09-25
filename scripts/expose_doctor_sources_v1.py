"""Expose approved, immutable source copies for Doctor consumers."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "doctor_sources"
SOURCE_ROOT = Path(r"C:\Users\Joe Lau\Documents\Codex\2026-09-19\source-read-only-g-ai-do")
if OUT.exists():
    shutil.rmtree(OUT)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def add_sources(pattern: str, category: str, source_type: str, methodology: str | None = None) -> None:
    for src in sorted(SOURCE_ROOT.glob(pattern)):
        digest = sha256(src)
        if digest in seen:
            continue
        seen.add(digest)
        target_dir = OUT / category
        target_dir.mkdir(parents=True, exist_ok=True)
        target_name = f"{src.parent.name}__{src.name}" if src.name in {"CASES_V1.csv", "CASES.csv"} else src.name
        target = target_dir / target_name
        if not target.exists():
            shutil.copy2(src, target)
        manifest.append({
            "SOURCE_ID": f"DOCSRC-{len(manifest)+1:04d}",
            "SOURCE_TYPE": source_type,
            "TITLE": src.stem,
            "STOCK_CODE": None,
            "METHODOLOGY_ID": methodology,
            "SOURCE_PATH": str(src),
            "EXPOSED_PATH": str(target),
            "SOURCE_HASH": digest,
            "SOURCE_DATE": date.fromtimestamp(src.stat().st_mtime).isoformat(),
            "INGESTION_STATUS": "EXPOSED_READ_ONLY",
        })

manifest: list[dict] = []
seen: set[str] = set()
add_sources("outputs/phase2a/01_FRAMEWORK_EXTRACTION/IVAN_LTYPE/CASES_V1.csv", "cases", "METHODOLOGY_CASES", "IVAN_L")
add_sources("outputs/phase2b/01_FRAMEWORK_EXTRACTION/HILTON/CASES_V1.csv", "cases", "METHODOLOGY_CASES", "HILTON")
add_sources("outputs/phase2c/01_FRAMEWORK_EXTRACTION/CHOW_HIN/CASES_V1.csv", "cases", "METHODOLOGY_CASES", "CHAU_HIN")
add_sources("outputs/phase2d/01_FRAMEWORK_EXTRACTION/YEZI/CASES_V1.csv", "cases", "METHODOLOGY_CASES", "YEZI")
add_sources("outputs/phase2e/01_FRAMEWORK_EXTRACTION/BOOKS/*/CASES_V1.csv", "cases", "BOOK_CASES", "BOOKS")
add_sources("outputs/phase1b/01_FRAMEWORK_EXTRACTION/PILOT_V1/*/CASES.csv", "cases", "PILOT_CASES")
add_sources("outputs/phase2*/01_FRAMEWORK_EXTRACTION/*/*CONCEPT_MAP*.md", "methodologies", "METHODOLOGY_NOTE")
add_sources("work/book_sources/*.md", "教材", "INVESTMENT教材")
add_sources("work/yezi_sources/*.md", "transcripts", "TRANSCRIPT_LESSON", "YEZI")

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "manifest.json").write_text(json.dumps({
    "WORK_PACKAGE": "DOCTOR_SOURCE_CORPUS_EXPOSURE_V1",
    "CORPUS_STATUS": "READ_ONLY_EXPOSED",
    "SOURCE_ROOT": str(SOURCE_ROOT),
    "DEDUPLICATION": "SHA256",
    "PRODUCTION_DATA_INCLUDED": False,
    "UNAVAILABLE_PROJECT_ONLY_SOURCES": [
        "Original ChatGPT-only conversation attachments not present as durable project files",
        "Any ZC-owned source units without a reachable durable checkpoint"
    ],
    "sources": manifest,
}, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "CHECKPOINT.md").write_text(
    "# Doctor source corpus checkpoint\n\n"
    "WORK_PACKAGE=DOCTOR_SOURCE_CORPUS_EXPOSURE_V1\n"
    "CORPUS_PATH=" + str(OUT) + "\n"
    "SOURCE_COUNT=" + str(len(manifest)) + "\n"
    "READ_ONLY_COPIES=YES\n"
    "PRODUCTION_RESEARCH_STORE_MUTATED=NO\n"
    "DEDUPLICATED_BY=SHA256\n"
    "LUNA_VISIBLE_SOURCE_COUNT=" + str(len(manifest)) + "\n"
    "ZC_VISIBLE_SOURCE_COUNT=" + str(len(manifest)) + "\n",
    encoding="utf-8",
)
print(json.dumps({"corpus": str(OUT), "source_count": len(manifest)}, ensure_ascii=False))

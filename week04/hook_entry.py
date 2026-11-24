#!/usr/bin/env python3
"""Codex hook entry: check a reported output path from the hook event."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from numeric_guard import check


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    raw = event.get("output_path") or event.get("file_path") or event.get("path")
    if not raw:
        repo = Path(__file__).resolve().parents[1]
        candidates = [path for root in (repo / "runs", repo / "outputs") if root.exists() for name in ("worksheet.md", "final_report.md") for path in root.rglob(name) if time.time() - path.stat().st_mtime <= 300]
        if not candidates:
            return 0
        report = max(candidates, key=lambda path: path.stat().st_mtime)
    else:
        report = Path(raw).resolve()
    if report.suffix.lower() != ".md" or not report.exists():
        return 0
    failures = check(report, report.parent)
    if failures:
        print(json.dumps({"decision": "block", "reason": "\n".join(failures)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

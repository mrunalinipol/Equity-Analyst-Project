#!/usr/bin/env python3
"""Print the live-record reaction table without changing saved views."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from closes_reader import NOT_AVAILABLE, last_close_before, official_daily_closes, parse_filing_time  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    agreements = total = 0
    print("ticker | filing time | view time | direction | reaction | result")
    if not args.folder.exists():
        print("agreements: 0/0; after and not-computed views excluded")
        return 0
    for run in sorted(path for path in args.folder.iterdir() if path.is_dir()):
        record_path = run / "view.json"
        if not record_path.exists():
            continue
        record = json.loads(record_path.read_text(encoding="utf-8"))
        direction = record.get("direction", "not computed")
        filed = record.get("filing_time", "")
        view_time = record.get("view_time", "")
        before = last_close_before(record["ticker"], filed, ROOT / ".env") if filed else NOT_AVAILABLE
        if filed:
            filed_at = parse_filing_time(filed)
            first_reaction_day = filed_at.date() if filed_at.time() < time(16, 0) else filed_at.date() + timedelta(days=1)
            after_rows = official_daily_closes(record["ticker"], first_reaction_day, datetime.now().date(), ROOT / ".env")
        else:
            after_rows = NOT_AVAILABLE
        after = after_rows[0] if isinstance(after_rows, list) and after_rows else None
        reaction = "not available"
        result = ""
        if isinstance(before, dict) and after:
            value = after["close"] / before["close"] - 1
            reaction = "up" if value > 0 else "down" if value < 0 else "flat"
            first_after = datetime.fromisoformat(after["date"] + "T16:00:00").replace(tzinfo=filed_at.tzinfo)
            if view_time and datetime.fromisoformat(view_time) > first_after:
                result = "after"
            elif direction != "not computed":
                agreed = (direction == "more than the price" and reaction == "up") or (direction == "less than the price" and reaction == "down")
                result = "agree" if agreed else "disagree"
                total += 1
                agreements += int(agreed)
        print(f"{record['ticker']} | {filed or 'not known'} | {view_time or 'not known'} | {direction} | {reaction} | {result or 'not scored'}")
    print(f"agreements: {agreements}/{total}; after and not-computed views excluded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

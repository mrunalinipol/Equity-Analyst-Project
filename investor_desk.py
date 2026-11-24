#!/usr/bin/env python3
"""Run the team, worksheet, and numeric guard in one code-fixed order."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def latest_seeker() -> Path:
    candidates = sorted((ROOT / "runs" / "seeker").glob("seeker_*"), key=lambda path: path.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError("No seeker run exists. Run week04/seeker.py first.")
    return candidates[-1]


def pick_from_screen(seeker: Path) -> str:
    rows = json.loads((seeker / "registry.json").read_text(encoding="utf-8"))
    ranked = [row for row in rows if row.get("stage") == "in its window" and not row.get("unranked_reason") and row.get("ticker")]
    if not ranked:
        raise ValueError("The latest seeker screen has no ranked ticker.")
    return str(ranked[0]["ticker"]).upper()


def command(label: str, args: list[str], cwd: Path = ROOT) -> tuple[float, str]:
    started = time.monotonic()
    completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    elapsed = time.monotonic() - started
    if completed.returncode:
        raise RuntimeError(f"{label} failed ({completed.returncode}): {completed.stderr.strip() or completed.stdout.strip()}")
    return elapsed, completed.stdout.strip()


def newest_run(folder: Path, ticker: str, after: float) -> Path:
    candidates = [path for path in folder.glob(f"{ticker}_*") if path.is_dir() and path.stat().st_mtime >= after - 2]
    if not candidates:
        raise FileNotFoundError("The agent team did not create a run folder.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def filings_first_line(run: Path) -> str:
    metadata = json.loads((run / "run_metadata.json").read_text(encoding="utf-8"))
    items = []
    for filing in metadata.get("filings", {}).values():
        if isinstance(filing, dict):
            items.append(f"{filing.get('form')} {filing.get('accession')}")
    extra = run / "spinoff_filings.json"
    if extra.exists():
        items.extend(json.loads(extra.read_text(encoding="utf-8")))
    return "Filings read: " + (", ".join(dict.fromkeys(items)) or "not known")


def assemble(run: Path, timings: dict[str, float], preserve_view_time: bool = False) -> None:
    verified = (run / "verified_report.md").read_text(encoding="utf-8")
    worksheet = (run / "worksheet.md").read_text(encoding="utf-8")
    view_match = re.search(r"## View on this release\n(.*?)(?:\n##|\Z)", worksheet, re.DOTALL)
    view = view_match.group(1).strip() if view_match else "direction: not computed"
    timing_lines = "\n".join(f"- {name}: {seconds:.3f} seconds" for name, seconds in timings.items())
    final = f"{filings_first_line(run)}\n\n<!-- PREVERIFIED START: verification.json -->\n{verified}\n<!-- PREVERIFIED END -->\n\n# Worksheet view\n\n{view}\n\n# Part timing\n\n{timing_lines}\n"
    (run / "final_report.md").write_text(final, encoding="utf-8")
    record_path = run / "view.json"
    if not preserve_view_time or not record_path.exists():
        metadata = json.loads((run / "run_metadata.json").read_text(encoding="utf-8"))
        direction_match = re.search(r"direction:\s*(.+)", view)
        record = {
            "ticker": metadata.get("company", {}).get("ticker", ""),
            "filing_time": metadata.get("filing_time_eastern", ""),
            "view_time": datetime.now().astimezone().isoformat(),
            "direction": direction_match.group(1).strip() if direction_match else "not computed",
        }
        record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def build_existing(run: Path, registry: Path | None, preserve_view_time: bool = False) -> Path:
    timings: dict[str, float] = {}
    worksheet_args = [sys.executable, str(ROOT / "week04" / "worksheet.py"), str(run)]
    if registry:
        worksheet_args.extend(["--registry", str(registry)])
    timings["worksheet"], _ = command("worksheet", worksheet_args)
    timings["worksheet hook"], _ = command("worksheet hook", [sys.executable, str(ROOT / "week04" / "numeric_guard.py"), str(run / "worksheet.md"), "--run", str(run)])
    started = time.monotonic()
    assemble(run, timings, preserve_view_time)
    timings["assemble"] = time.monotonic() - started
    assemble(run, timings, preserve_view_time)
    (run / "desk_order.json").write_text(json.dumps({"order": ["agent team", "worksheet", "worksheet hook", "assemble", "final hook"], "seconds": timings}, indent=2) + "\n", encoding="utf-8")
    timings["final hook"], _ = command("final hook", [sys.executable, str(ROOT / "week04" / "numeric_guard.py"), str(run / "final_report.md"), "--run", str(run)])
    (run / "desk_order.json").write_text(json.dumps({"order": ["agent team", "worksheet", "worksheet hook", "assemble", "final hook"], "seconds": timings}, indent=2) + "\n", encoding="utf-8")
    return run


def run_fresh(ticker: str, peers: str, registry: Path | None, live: bool, filed: str = "") -> Path:
    output_root = ROOT / "runs" / ("live" if live else "desk")
    output_root.mkdir(parents=True, exist_ok=True)
    before = time.time()
    team_args = [sys.executable, str(ROOT / "crewai_flow.py"), ticker, "--output-root", str(output_root)]
    if peers:
        team_args.extend(["--peers", peers])
    if filed:
        team_args.extend(["--filed", filed])
    elapsed, _ = command("agent team", team_args)
    run = newest_run(output_root, ticker, before)
    built = build_existing(run, registry)
    order = json.loads((run / "desk_order.json").read_text(encoding="utf-8"))
    order["seconds"]["agent team"] = elapsed
    (run / "desk_order.json").write_text(json.dumps(order, indent=2) + "\n", encoding="utf-8")
    return built


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", help="Ticker or the word screen")
    parser.add_argument("--peers", default="")
    parser.add_argument("--seeker-run", type=Path)
    parser.add_argument("--from-run", type=Path, help="Join an existing saved team run without fetching")
    parser.add_argument("--replay", type=Path, help="Rebuild a saved joined run without fetching")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--filed", default="", help="Earnings filing time override in Eastern time")
    args = parser.parse_args()
    seeker = args.seeker_run or (latest_seeker() if args.target == "screen" else None)
    registry = seeker / "registry.json" if seeker else None
    try:
        if args.replay:
            output = build_existing(args.replay, registry, preserve_view_time=True)
        elif args.from_run:
            output = build_existing(args.from_run, registry)
        else:
            if not args.target:
                parser.error("target is required unless --from-run or --replay is used")
            ticker = pick_from_screen(seeker) if args.target == "screen" and seeker else args.target.upper()
            output = run_fresh(ticker, args.peers, registry, args.live, args.filed)
    except Exception as exc:
        print(f"Desk stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"Final report: {output / 'final_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

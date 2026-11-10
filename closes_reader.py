#!/usr/bin/env python3
"""Read official daily closes from LSEG Workspace or a local export file."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo


NOT_AVAILABLE: Literal["not available"] = "not available"
EASTERN = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parent


def _load_env(path: Path) -> dict[str, str]:
    values = dict(os.environ)
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values.setdefault(key.strip(), value)
    return values


def parse_filing_time(value: str) -> datetime:
    """Parse an SEC Accepted time or a YYYY-MM-DDTHH:MM:SS override as Eastern."""
    text = value.strip()
    if re.fullmatch(r"\d{14}", text):
        parsed = datetime.strptime(text, "%Y%m%d%H%M%S")
    else:
        normalized = text.replace(" ", "T", 1)
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError("Filing time must use YYYY-MM-DDTHH:MM:SS in Eastern time.") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=EASTERN)
    return parsed.astimezone(EASTERN)


def _normalize_day(value: str | date) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def _file_rows(path: Path, ticker: str, start: date, end: date) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            row = {str(key).strip().lower(): value for key, value in raw.items() if key is not None}
            row_ticker = str(row.get("ticker") or row.get("ric") or row.get("instrument") or "").upper()
            if row_ticker and row_ticker not in {ticker.upper(), *_ric_candidates(ticker)}:
                continue
            day_text = str(row.get("date") or row.get("datetime") or "").strip()[:10]
            close_text = str(row.get("close") or row.get("price close") or row.get("trdprc_1") or "").strip()
            if not day_text or not close_text:
                continue
            try:
                day = date.fromisoformat(day_text)
                close = float(close_text.replace(",", ""))
            except ValueError:
                continue
            if start <= day <= end:
                output.append(
                    {"ticker": ticker.upper(), "date": day.isoformat(), "close": close, "source": str(path)}
                )
    return sorted(output, key=lambda item: item["date"])


def _ric_candidates(ticker: str) -> list[str]:
    symbol = ticker.upper().strip()
    return [symbol, f"{symbol}.O", f"{symbol}.N"]


def _lseg_rows(ticker: str, start: date, end: date, app_key: str) -> list[dict[str, Any]]:
    import lseg.data as ld

    session = ld.open_session(name="desktop.workspace", app_key=app_key)
    try:
        for ric in _ric_candidates(ticker):
            try:
                frame = ld.get_history(
                    universe=ric,
                    fields=["TRDPRC_1"],
                    interval="daily",
                    start=start.isoformat(),
                    end=end.isoformat(),
                )
            except Exception:
                continue
            if frame is None or frame.empty:
                continue
            numeric_columns = [column for column in frame.columns if str(column).upper() == "TRDPRC_1"]
            if not numeric_columns:
                numeric_columns = list(frame.select_dtypes(include="number").columns)
            if not numeric_columns:
                continue
            column = numeric_columns[0]
            rows: list[dict[str, Any]] = []
            for index, raw_close in frame[column].items():
                if raw_close is None:
                    continue
                day = index.date() if hasattr(index, "date") else date.fromisoformat(str(index)[:10])
                rows.append(
                    {
                        "ticker": ticker.upper(),
                        "instrument": ric,
                        "date": day.isoformat(),
                        "close": float(raw_close),
                        "source": "LSEG Workspace daily TRDPRC_1",
                    }
                )
            if rows:
                return sorted(rows, key=lambda item: item["date"])
        return []
    finally:
        ld.close_session()


def _isolated_python(env: dict[str, str]) -> Path | None:
    configured = env.get("LSEG_PYTHON", "").strip()
    candidate = Path(configured).expanduser() if configured else ROOT / ".venv-lseg" / "bin" / "python"
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate if candidate.is_file() else None


def _isolated_rows(
    ticker: str, start: date, end: date, env_path: Path, env: dict[str, str]
) -> list[dict[str, Any]]:
    python = _isolated_python(env)
    if python is None or Path(sys.executable).resolve() == python.resolve():
        return []
    completed = subprocess.run(
        [
            str(python),
            str(Path(__file__).resolve()),
            "--provider-daily",
            ticker,
            start.isoformat(),
            end.isoformat(),
            "--env",
            str(env_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        return []
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def official_daily_closes(
    ticker: str,
    start_date: str | date,
    end_date: str | date,
    env_path: str | Path = ROOT / ".env",
) -> list[dict[str, Any]] | Literal["not available"]:
    """Return official daily closes for a ticker and inclusive date range."""
    start, end = _normalize_day(start_date), _normalize_day(end_date)
    if start > end:
        raise ValueError("The start date must not be after the end date.")
    path = Path(env_path)
    env = _load_env(path)
    export = env.get("LSEG_CLOSES_FILE", "").strip()
    if export:
        export_path = Path(export).expanduser()
        if not export_path.is_absolute():
            export_path = path.parent / export_path
        if export_path.is_file():
            rows = _file_rows(export_path, ticker, start, end)
            return rows or NOT_AVAILABLE
    app_key = env.get("LSEG_APP_KEY", "").strip()
    if not app_key:
        return NOT_AVAILABLE
    try:
        local_lseg = importlib.util.find_spec("lseg.data") is not None
    except ModuleNotFoundError:
        local_lseg = False
    if local_lseg:
        try:
            rows = _lseg_rows(ticker, start, end, app_key)
        except Exception:
            rows = []
    else:
        rows = _isolated_rows(ticker, start, end, path, env)
    return rows or NOT_AVAILABLE


def last_close_before(
    ticker: str,
    filed_at: str,
    env_path: str | Path = ROOT / ".env",
) -> dict[str, Any] | Literal["not available"]:
    """Return the last official close available before an Eastern filing time."""
    filing_time = parse_filing_time(filed_at)
    close_time = datetime.combine(filing_time.date(), time(16, 0), tzinfo=EASTERN)
    last_eligible_day = filing_time.date() if filing_time > close_time else filing_time.date() - timedelta(days=1)
    rows = official_daily_closes(
        ticker,
        last_eligible_day - timedelta(days=14),
        last_eligible_day,
        env_path,
    )
    if rows == NOT_AVAILABLE:
        return NOT_AVAILABLE
    eligible = [row for row in rows if date.fromisoformat(row["date"]) <= last_eligible_day]
    if not eligible:
        return NOT_AVAILABLE
    result = dict(max(eligible, key=lambda item: item["date"]))
    result["filed_at_eastern"] = filing_time.isoformat()
    result["close_rule"] = "A trading day's close becomes available at 4:00 PM Eastern."
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", type=Path, default=ROOT / ".env")
    parser.add_argument("--daily", nargs=3, metavar=("TICKER", "START", "END"))
    parser.add_argument("--last-before", nargs=2, metavar=("TICKER", "FILED_AT"))
    parser.add_argument("--provider-daily", nargs=3, metavar=("TICKER", "START", "END"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.provider_daily:
        ticker, start, end = args.provider_daily
        env = _load_env(args.env)
        app_key = env.get("LSEG_APP_KEY", "").strip()
        value: Any = _lseg_rows(ticker, date.fromisoformat(start), date.fromisoformat(end), app_key) if app_key else []
    elif args.daily:
        value = official_daily_closes(*args.daily, env_path=args.env)
    elif args.last_before:
        value = last_close_before(*args.last_before, env_path=args.env)
    else:
        parser.error("Use --daily or --last-before.")
    print(json.dumps(value, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

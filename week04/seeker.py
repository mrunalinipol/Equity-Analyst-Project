#!/usr/bin/env python3
"""Find, register, price, and rank U.S. spinoffs from SEC EDGAR evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from closes_reader import NOT_AVAILABLE, official_daily_closes  # noqa: E402

SEC_ARCHIVES = "https://www.sec.gov/Archives"
SPIN_FORMS = {"10-12B", "10-12G", "10-12B/A", "10-12G/A"}


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            if raw.strip() and not raw.lstrip().startswith("#") and "=" in raw:
                key, value = raw.split("=", 1)
                values[key.strip()] = value.strip().strip("\"'")
    return values


@dataclass
class Edgar:
    user_agent: str
    delay: float = 0.12

    def __post_init__(self) -> None:
        if not self.user_agent or "@" not in self.user_agent:
            raise ValueError("Set SEC_USER_AGENT in .env to a name and email address.")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"})

    def text(self, url: str) -> str:
        time.sleep(self.delay)
        response = self.session.get(url, timeout=45)
        response.raise_for_status()
        return response.text


def quarter(day: date) -> int:
    return (day.month - 1) // 3 + 1


def index_periods(start: date, end: date) -> list[tuple[int, int]]:
    periods: list[tuple[int, int]] = []
    year, qtr = start.year, quarter(start)
    while (year, qtr) <= (end.year, quarter(end)):
        periods.append((year, qtr))
        qtr += 1
        if qtr == 5:
            year, qtr = year + 1, 1
    return periods


def parse_master_index(text: str, start: date, end: date) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) != 5 or parts[2] not in SPIN_FORMS:
            continue
        filed = date.fromisoformat(parts[3])
        if start <= filed <= end:
            records.append({"cik": parts[0], "company": parts[1], "form": parts[2], "filed": parts[3], "path": parts[4]})
    return records


def discover_form10(edgar: Edgar, start: date, end: date) -> list[dict[str, str]]:
    found: dict[str, dict[str, str]] = {}
    for year, qtr in index_periods(start, end):
        url = f"{SEC_ARCHIVES}/edgar/full-index/{year}/QTR{qtr}/master.idx"
        for record in parse_master_index(edgar.text(url), start, end):
            key = f"{record['cik']}:{record['path'].split('/')[-1].replace('.txt', '').replace('-', '')[:18]}"
            found[key] = record
    return sorted(found.values(), key=lambda row: (row["filed"], row["cik"]))


def accession_from_path(path: str) -> str:
    return Path(path).stem


def filing_url(record: dict[str, str]) -> str:
    return f"{SEC_ARCHIVES}/{record['path']}"


def filing_text(html_or_submission: str) -> str:
    return BeautifulSoup(html_or_submission, "html.parser").get_text(" ", strip=True)


def first_match(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip(" .,")
    return ""


def classify_record(record: dict[str, str], raw: str) -> dict[str, Any]:
    text = filing_text(raw)
    lower = text.lower()
    accession = accession_from_path(record["path"])
    source = {"accession": accession, "form": record["form"], "filed": record["filed"], "url": filing_url(record)}
    company_lower = record.get("company", "").lower()
    fund_name = any(term in company_lower for term in (" fund", "trust", "bdc"))
    if "business development company" in lower or "perpetual-life" in lower or (fund_name and "investment company" in lower):
        return {**record, "classification": "dropped", "drop_reason": "fund", "source": source}
    distribution_proof = any(term in lower for term in ("distribution of all", "distribute all", "pro rata distribution", "distribution to holders"))
    information_statement = "information statement" in lower
    if not information_statement:
        return {**record, "classification": "dropped", "drop_reason": "Form 10 has no information statement", "source": source}
    if not distribution_proof:
        return {**record, "classification": "dropped", "drop_reason": "no parent distribution of the registrant", "source": source}
    parent = first_match(text, [
        r"(?:subsidiary of|separation from)\s+([A-Z][A-Za-z0-9&.,' -]{2,60}?(?:Inc\.|Corporation|Corp\.|Ltd\.|plc))(?=\s|\()",
        r"([A-Z][A-Za-z0-9&.,' -]{2,60}?(?:Inc\.|Corporation|Corp\.|Ltd\.|plc))\s+will distribute all",
    ])
    parent = re.sub(r"^INFORMATION STATEMENT\.\s*", "", parent, flags=re.IGNORECASE)
    ratio = first_match(text, [r"((?:one|\d+(?:\.\d+)?)\s+share[^.;]{0,100}?\s+for\s+(?:each|every)\s+(?:one|\d+(?:\.\d+)?)?\s*share)", r"distribution ratio\s*[:\-]?\s*([^.;]{1,120})"])
    record_date = first_match(text, [r"record date(?: is| of|:)\s*([A-Z][a-z]+\s+\d{1,2},\s+20\d{2})", r"on\s+([A-Z][a-z]+\s+\d{1,2},\s+20\d{2}),\s+the record date"])
    distribution_date = first_match(text, [r"distribution date(?: is| of|:)\s*([A-Z][a-z]+\s+\d{1,2},\s+20\d{2})", r"distribution (?:will|is expected to) (?:occur|be made) on\s+([A-Z][a-z]+\s+\d{1,2},\s+20\d{2})"])
    return {
        **record,
        "classification": "spinoff",
        "name": record["company"],
        "ticker": first_match(text, [r"(?:ticker symbol|symbol)\s*(?:is|will be|:)\s*[\"']?\s*([A-Z]{1,6})"]),
        "parent": parent,
        "ratio": ratio,
        "record_date": normalize_date(record_date),
        "distribution_date": normalize_date(distribution_date),
        "source": source,
        "sections": {"parent": "Information Statement cover", "ratio": "Information Statement cover", "record_date": "Information Statement cover", "distribution_date": "Information Statement cover"},
    }


def normalize_date(value: str) -> str:
    if not value:
        return ""
    for pattern in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            pass
    return ""


def load_factors(path: Path) -> tuple[int, list[dict[str, Any]]]:
    window = 0
    factors: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line == "factors:":
            continue
        if line.startswith("window_days:"):
            window = int(line.split(":", 1)[1].strip())
        elif line.startswith("- name:"):
            current = {"name": line.split(":", 1)[1].strip()}
            factors.append(current)
        elif current is not None and ":" in line:
            key, value = line.split(":", 1)
            value = value.strip().strip('"')
            current[key.strip()] = int(value) if key.strip() == "weight" else value
    if window <= 0 or not factors:
        raise ValueError("The factors file must define window_days and at least one factor.")
    return window, factors


def enrich_prices(row: dict[str, Any], run_date: date, env_path: Path) -> dict[str, Any]:
    result = dict(row)
    ticker, distribution = row.get("ticker", ""), row.get("distribution_date", "")
    result.update({"first_price": "", "first_price_date": "", "price": "", "price_date": ""})
    if not ticker or not distribution:
        return result
    start = date.fromisoformat(distribution) + timedelta(days=1)
    closes = official_daily_closes(ticker, start, run_date, env_path)
    if closes == NOT_AVAILABLE or not closes:
        return result
    env = load_env(env_path)
    configured_ticker = env.get("LSEG_CLOSES_TICKER", "").upper()
    if any(row.get("source_ticker") is None for row in closes) and configured_ticker != ticker.upper():
        # A tickerless single-name export cannot safely price a different name.
        result["price_note"] = "not available; set LSEG_CLOSES_TICKER for the configured tickerless export"
        return result
    result["first_price"], result["first_price_date"] = closes[0]["close"], closes[0]["date"]
    result["price"], result["price_date"] = closes[-1]["close"], closes[-1]["date"]
    result["first_weeks_return"] = closes[-1]["close"] / closes[0]["close"] - 1 if closes[0]["close"] else ""
    return result


def stage(row: dict[str, Any], run_date: date, window_days: int) -> str:
    distribution = row.get("distribution_date", "")
    if not distribution:
        return "registered"
    day = date.fromisoformat(distribution)
    if not row.get("first_price_date") and not row.get("distribution_complete"):
        return "listing approved" if row.get("listing_approved") else "registered"
    if run_date <= day + timedelta(days=window_days):
        return "in its window"
    return "past it"


def rank_rows(rows: list[dict[str, Any]], factors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = [dict(row) for row in rows]
    for row in ranked:
        row["factor_points"] = {}
        row["score"] = 0.0
        row["unranked_reason"] = ""
    for factor in factors:
        name, weight, direction = factor["name"], float(factor["weight"]), factor["direction"]
        if weight == 0:
            continue
        available = [(row, row.get(name)) for row in ranked if isinstance(row.get(name), (int, float))]
        if not available:
            for row in ranked:
                row["factor_points"][name] = "not available"
            continue
        ordered = sorted(available, key=lambda item: item[1], reverse=direction == "higher_is_better")
        count = len(ordered)
        for position, (row, _) in enumerate(ordered):
            points = weight if count == 1 else weight * (count - 1 - position) / (count - 1)
            row["factor_points"][name] = round(points, 4)
            row["score"] += points
        for row in ranked:
            if not isinstance(row.get(name), (int, float)):
                row["factor_points"][name] = "not available"
    for row in ranked:
        if not row.get("distribution_date"):
            row["unranked_reason"] = "distribution date is blank"
        elif not any(isinstance(row.get(factor["name"]), (int, float)) for factor in factors if float(factor["weight"]) != 0):
            row["unranked_reason"] = "all weighted factor inputs are not available"
    return sorted(ranked, key=lambda row: (bool(row["unranked_reason"]), -row["score"], row.get("name", "")))


def write_report(path: Path, run_date: date, index_date: date, rows: list[dict[str, Any]], dropped: list[dict[str, Any]], factors: list[dict[str, Any]]) -> None:
    price_dates = sorted({row.get("price_date") for row in rows if row.get("price_date")})
    lines = [f"Run date: {run_date.isoformat()} | price date: {price_dates[-1] if price_dates else 'not available'} | index date: {index_date.isoformat()}", "", "# Spinoff seeker screen", "", "## Names in their window"]
    in_window = [row for row in rows if row.get("stage") == "in its window" and not row.get("unranked_reason")]
    if not in_window:
        lines.append("None.")
    for number, row in enumerate(in_window, 1):
        points = ", ".join(f"{key} {value}" for key, value in row["factor_points"].items())
        price = f"${row['price']:.2f}" if isinstance(row.get("price"), (int, float)) else "not available"
        lines.append(f"{number}. {row.get('name') or 'not known'} | {row.get('parent') or 'not known'} | distributed {row.get('distribution_date') or 'not known'} | window ends {row.get('window_end') or 'not known'} | {price} on {row.get('price_date') or 'not available'} | score {row['score']:.4f}: {points}")
    lines.extend(["", "## Watch list"])
    watch = [row for row in rows if row.get("stage") in {"registered", "listing approved", "trading"}]
    lines.extend([f"- {row.get('name') or row.get('company')} | stage: {row['stage']} | {row['source']['url']}" for row in watch] or ["None."])
    lines.extend(["", "## Unranked"])
    unranked = [row for row in rows if row.get("unranked_reason")]
    lines.extend([f"- {row.get('name') or row.get('company')} | {row['unranked_reason']}" for row in unranked] or ["None."])
    lines.extend(["", "## Dropped"])
    lines.extend([f"- {row['company']} | {row['drop_reason']} | {row['source']['url']}" for row in dropped] or ["None."])
    lines.extend(["", "## What the data cannot show", "- A blank fact was not found and was not estimated.", "- Current index membership does not prove index membership at the distribution date.", "- The factor weights are an unvalidated hypothesis until a preregistered factor check tests them.", "", "screens, not recommendations"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(start: date, output_root: Path, candidate_file: Path | None, run_date: date, env_path: Path) -> Path:
    env = load_env(env_path)
    edgar = Edgar(env.get("SEC_USER_AGENT", ""))
    if candidate_file:
        records = json.loads(candidate_file.read_text(encoding="utf-8"))
    else:
        records = discover_form10(edgar, start, run_date)
        established = ROOT / "week04" / "verified_candidates.json"
        if established.exists():
            records.extend(json.loads(established.read_text(encoding="utf-8")))
    classified: list[dict[str, Any]] = []
    for record in records:
        raw = record.pop("saved_text", None)
        if raw is None:
            raw = edgar.text(filing_url(record))
        classified.append(classify_record(record, raw))
    # Amendments replace earlier evidence for the same registrant.
    latest_by_cik: dict[str, dict[str, Any]] = {}
    for item in classified:
        cik = str(item.get("cik", ""))
        prior = latest_by_cik.get(cik)
        if prior is None or (item.get("filed", ""), item.get("source", {}).get("accession", "")) > (prior.get("filed", ""), prior.get("source", {}).get("accession", "")):
            latest_by_cik[cik] = item
    classified = list(latest_by_cik.values())
    window_days, factors = load_factors(ROOT / "week04" / "factors.yaml")
    rows, dropped = [], []
    for item in classified:
        if item["classification"] == "dropped":
            dropped.append(item)
            continue
        row = enrich_prices(item, run_date, env_path)
        row["stage"] = stage(row, run_date, window_days)
        row["window_end"] = (date.fromisoformat(row["distribution_date"]) + timedelta(days=window_days)).isoformat() if row.get("distribution_date") else ""
        rows.append(row)
    ranked = rank_rows(rows, factors)
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    folder = output_root / f"seeker_{stamp}"
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "filings").mkdir()
    (folder / "registry.json").write_text(json.dumps(ranked, indent=2) + "\n", encoding="utf-8")
    (folder / "dropped.json").write_text(json.dumps(dropped, indent=2) + "\n", encoding="utf-8")
    (folder / "factors_used.json").write_text(json.dumps({"window_days": window_days, "factors": factors}, indent=2) + "\n", encoding="utf-8")
    write_report(folder / "report.md", run_date, run_date, ranked, dropped, factors)
    print(f"Saved seeker run: {folder}")
    return folder


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, type=date.fromisoformat)
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs" / "seeker")
    parser.add_argument("--candidate-file", type=Path, help="Test or pre-verified candidate records; default scans EDGAR indexes")
    parser.add_argument("--run-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--env", type=Path, default=ROOT / ".env")
    args = parser.parse_args()
    run(args.start, args.output_root, args.candidate_file, args.run_date, args.env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

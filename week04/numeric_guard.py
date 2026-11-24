#!/usr/bin/env python3
"""Refuse completion when a worksheet number has no saved evidence or computation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

NUMBER = re.compile(r"(?<![A-Za-z])[-+]?\$?\d[\d,]*(?:\.\d+)?%?")
COMPUTATION = re.compile(r"([-+]?\d[\d,.]*)\s*([+\-*/])\s*([-+]?\d[\d,.]*)\s*=\s*([-+]?\d[\d,.]*)")


def decimal(value: str) -> Decimal:
    return Decimal(value.replace("$", "").replace(",", "").replace("%", ""))


def close(left: Decimal, right: Decimal) -> bool:
    return abs(left - right) <= max(Decimal("0.0001"), abs(right) * Decimal("0.000001"))


def computed(line: str, token: str) -> bool:
    for match in COMPUTATION.finditer(line):
        left_text, operator, right_text, result_text = match.groups()
        left, right, result = decimal(left_text), decimal(right_text), decimal(result_text)
        expected = {"+": left + right, "-": left - right, "*": left * right, "/": left / right if right else Decimal("NaN")}[operator]
        if close(expected, result) and close(result, decimal(token)):
            return True
    return False


def all_fact_numbers(run: Path) -> set[Decimal]:
    values: set[Decimal] = set()
    for name in ("facts.json", "release_evidence.json", "ratios.json", "market_close.json", "worksheet_computations.json", "desk_order.json"):
        path = run / name
        if not path.exists():
            continue
        def walk(item: Any) -> None:
            if isinstance(item, dict):
                for value in item.values():
                    walk(value)
            elif isinstance(item, list):
                for value in item:
                    walk(value)
            elif isinstance(item, (int, float)) and not isinstance(item, bool):
                values.add(Decimal(str(item)))
        walk(json.loads(path.read_text(encoding="utf-8")))
    return values


def config_numbers(run: Path) -> set[Decimal]:
    values: set[Decimal] = set()
    config = run.parents[1] / "week04" / "worksheet_config.yaml"
    if not config.exists():
        config = Path(__file__).with_name("worksheet_config.yaml")
    for token in NUMBER.findall(config.read_text(encoding="utf-8")):
        try:
            values.add(decimal(token))
        except InvalidOperation:
            pass
    return values


def evidence_text(run: Path) -> str:
    texts: list[str] = []
    for pattern in ("*.txt", "filings/*.txt"):
        for path in run.glob(pattern):
            texts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(texts)


def identifier_only(line: str, token: str) -> bool:
    stripped = token.replace("$", "").replace(",", "").replace("%", "")
    lower = line.lower()
    if lower.startswith("filings read:"):
        return True
    if re.search(rf"(?:saved\s+)?line\s+{re.escape(stripped)}\b", line, re.IGNORECASE):
        return True
    if stripped.startswith("-") and re.search(r"20\d{2}-\d{2}-\d{2}", line):
        return True
    if stripped.startswith("-") and any(word in lower for word in ("accession", "10-k", "10-q", "8-k")):
        return True
    if re.fullmatch(r"20\d{2}(?:-\d{2}-\d{2})?", stripped):
        return True
    if len(stripped.split(".")[0]) >= 10 and any(word in lower for word in ("accession", "filings read", "saved line")):
        return True
    return False


def exact_in_text(token: str, text: str) -> bool:
    plain = token.replace("$", "").replace("%", "")
    candidates = {plain, plain.replace(",", "")}
    try:
        value = decimal(token)
        candidates.add(f"{value:f}")
        if value == value.to_integral():
            candidates.add(f"{int(value):,}")
    except InvalidOperation:
        return False
    compact = text.replace(",", "")
    return any(candidate in text or candidate.replace(",", "") in compact for candidate in candidates)


def check(report: Path, run: Path) -> list[str]:
    facts = all_fact_numbers(run)
    config = config_numbers(run)
    filings = evidence_text(run)
    failures: list[str] = []
    preverified = False
    for line_number, line in enumerate(report.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("<!-- PREVERIFIED START:"):
            preverified = True
            continue
        if line.startswith("<!-- PREVERIFIED END"):
            preverified = False
            continue
        if preverified:
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        for token in NUMBER.findall(line):
            if identifier_only(line, token):
                continue
            try:
                value = decimal(token)
            except InvalidOperation:
                continue
            supported = any(abs(value - item) <= Decimal("0.0005") for item in facts | config) or computed(line, token)
            if not supported and any(word in line.lower() for word in ("filing", "xbrl", "saved line")):
                supported = exact_in_text(token, filings)
            if not supported:
                failures.append(f"refused: line {line_number}, {token} has no filing, facts-file, reader, rate, weight, or printed-computation support | {line}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--run", type=Path, help="Saved run folder; default is the report's folder")
    args = parser.parse_args()
    failures = check(args.report, args.run or args.report.parent)
    if failures:
        print("\n".join(failures))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

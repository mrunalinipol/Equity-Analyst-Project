#!/usr/bin/env python3
"""Build an evidence-bound investor worksheet from one saved desk run."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from closes_reader import NOT_AVAILABLE, official_daily_closes  # noqa: E402


def read_json(path: Path, default: Any = None) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def load_simple_config(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip('"')
    return values


def fact_line(name: str, fact: dict[str, Any] | None) -> str:
    if not fact:
        return f"{name}: not known"
    return (
        f"{name}: {fact['value']}; reported after the spin; "
        f"{fact.get('form', 'filing')} {fact.get('accession', 'not known')}, "
        f"XBRL {fact.get('tag', 'not known')}, period {fact.get('start') or 'instant'} to {fact.get('end') or 'not known'}"
    )


def find_depreciation(run: Path, facts: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("depreciation_and_amortization", "depreciation", "depreciation_depletion_amortization"):
        if key in facts:
            return facts[key]
    text_path = run / "latest_10-K.txt"
    if not text_path.exists():
        return None
    for number, line in enumerate(text_path.read_text(encoding="utf-8").splitlines(), 1):
        matches = [
            re.search(r"depreciation and amortization(?: expense)?\s+(?:of\s+)?\$?([0-9][0-9,.]*)\s*(million|billion)?", line, re.IGNORECASE),
            re.search(r"\$?([0-9][0-9,.]*)\s*(million|billion)?\s+of depreciation and amortization", line, re.IGNORECASE),
        ]
        match = next((item for item in matches if item), None)
        if match:
            value = float(match.group(1).replace(",", ""))
            scale = {"million": 1_000_000, "billion": 1_000_000_000}.get((match.group(2) or "").lower(), 1)
            return {"value": value * scale, "form": "10-K", "accession": "saved filing", "tag": f"saved line {number}", "start": "not stated", "end": "not stated"}
    return None


def source_value(fact: dict[str, Any] | None) -> float | None:
    return float(fact["value"]) if fact and isinstance(fact.get("value"), (int, float)) else None


def compute_value(facts: dict[str, Any], config: dict[str, str], run: Path) -> dict[str, Any]:
    earnings = source_value(facts.get("net_income"))
    depreciation_fact = find_depreciation(run, facts)
    depreciation = source_value(depreciation_fact)
    capex = source_value(facts.get("capital_expenditures"))
    output: dict[str, Any] = {"earnings": earnings, "depreciation": depreciation, "capex": capex, "depreciation_fact": depreciation_fact}
    if None in (earnings, depreciation, capex):
        output.update({"owner_cash_flow": None, "low_value": None, "mid_value": None, "reason": "one or more owner-cash-flow inputs are not known"})
        return output
    owner_cash_flow = earnings + depreciation - capex
    output["owner_cash_flow"] = owner_cash_flow
    try:
        low_rate = float(config["low_capitalization_rate"])
        mid_rate = float(config["mid_capitalization_rate"])
    except (KeyError, ValueError):
        output.update({"low_value": None, "mid_value": None, "reason": "student valuation rates are blank"})
        return output
    if low_rate <= 0 or mid_rate <= 0:
        raise ValueError("Capitalization rates must be positive.")
    output.update({"low_value": owner_cash_flow / low_rate, "mid_value": owner_cash_flow / mid_rate, "low_rate": low_rate, "mid_rate": mid_rate, "reason": ""})
    return output


def liquidity(ticker: str, run: Path, config: dict[str, str]) -> dict[str, Any]:
    metadata = read_json(run / "run_metadata.json", {})
    filing_day = str(metadata.get("filing_time_eastern", ""))[:10]
    if not filing_day:
        return {"median_daily_dollar_volume": None, "purchase_size": config.get("client_purchase_size", ""), "result": "not computed"}
    closes = official_daily_closes(ticker, filing_day, date.today(), ROOT / ".env")
    # The Week 4 reader contract has closes only. The worksheet does not invent volume.
    return {"median_daily_dollar_volume": None, "purchase_size": config.get("client_purchase_size", ""), "result": "not computed; volume is not available from the configured reader", "closes_available": closes != NOT_AVAILABLE}


def persona_judgment(persona: Path, payload: dict[str, Any], output: Path) -> str:
    if not persona.exists() or "STUDENT TODO" in persona.read_text(encoding="utf-8"):
        return "Judgment not computed: the student-authored persona is missing. What would change the view: not computed."
    command = [sys.executable, str(ROOT / "week04" / "persona_call.py"), "--persona", str(persona), "--payload", str(output)]
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return completed.stdout.strip() if completed.returncode == 0 and completed.stdout.strip() else f"Judgment not computed: {completed.stderr.strip() or 'model call failed'}. What would change the view: not computed."


def registry_row(registry: Path | None, ticker: str) -> dict[str, Any] | None:
    if not registry or not registry.exists():
        return None
    rows = read_json(registry, [])
    return next((row for row in rows if str(row.get("ticker", "")).upper() == ticker), None)


def run(saved_run: Path, registry: Path | None, config_path: Path, persona: Path) -> Path:
    metadata = read_json(saved_run / "run_metadata.json", {})
    ticker = str(metadata.get("company", {}).get("ticker") or metadata.get("arguments", {}).get("ticker") or "").upper()
    if not ticker:
        raise ValueError("The saved run does not identify a ticker.")
    facts = read_json(saved_run / "facts.json", {})
    config = load_simple_config(config_path)
    row = registry_row(registry, ticker)
    value = compute_value(facts, config, saved_run)
    market_close = read_json(saved_run / "market_close.json", NOT_AVAILABLE)
    price = market_close.get("close") if isinstance(market_close, dict) else None
    liquid = liquidity(ticker, saved_run, config)
    payload = {"ticker": ticker, "spinoff_facts": row or "not applicable", "filing_facts": facts, "value": value, "price": price}
    judgment = persona_judgment(persona, payload, saved_run / "worksheet_persona_payload.json")
    filed = metadata.get("filings", {})
    filing_names = [f"{item.get('form')} {item.get('accession')}" for item in filed.values() if isinstance(item, dict)]
    lines = [
        f"Filings read: {', '.join(filing_names) or 'not known'} | worksheet date: {date.today().isoformat()}",
        "",
        f"# {metadata.get('company', {}).get('name', ticker)} ({ticker}): investor worksheet",
        "",
        "Screens to look at, not a recommendation.",
        "",
        "## Facts",
    ]
    if row:
        source = row.get("source", {})
        lines.extend([
            f"parent: {row.get('parent') or 'not known'}; {source.get('form', 'filing')} {source.get('accession', 'not known')}, {row.get('sections', {}).get('parent', 'section not known')}",
            f"distribution ratio: {row.get('ratio') or 'not known'}; {source.get('form', 'filing')} {source.get('accession', 'not known')}, {row.get('sections', {}).get('ratio', 'section not known')}",
            f"record date: {row.get('record_date') or 'not known'}; identifier; {source.get('form', 'filing')} {source.get('accession', 'not known')}",
            f"distribution date: {row.get('distribution_date') or 'not known'}; identifier; {source.get('form', 'filing')} {source.get('accession', 'not known')}",
        ])
    else:
        lines.append("spinoff facts: not applicable; ticker is not in the selected seeker registry")
    lines.extend([fact_line("after-tax earnings", facts.get("net_income")), fact_line("depreciation and amortization", value.get("depreciation_fact")), fact_line("capital spending", facts.get("capital_expenditures"))])
    lines.extend(["", "## Why it may be cheap", judgment, "", "## Value range"])
    if value["owner_cash_flow"] is None:
        lines.append(f"owner cash flow: not computed; {value['reason']}")
    else:
        lines.append(f"owner cash flow: {value['earnings']} + {value['depreciation']} - {value['capex']} = {value['owner_cash_flow']}; printed computation")
    if value["low_value"] is None:
        lines.append(f"low and mid cases: not computed; {value['reason']}")
    else:
        lines.append(f"low case: {value['owner_cash_flow']} / {value['low_rate']} = {value['low_value']}; printed computation; rate from {config_path.name}")
        lines.append(f"mid case: {value['owner_cash_flow']} / {value['mid_rate']} = {value['mid_value']}; printed computation; rate from {config_path.name}")
    if price is None or value["low_value"] is None:
        lines.append("price against low case: not computed")
    else:
        lines.append(f"price: {price} on {market_close.get('date')}; reader output")
        lines.append(f"price against low case: {price} / {value['low_value']} = {price / value['low_value']}; printed computation")
    lines.extend(["", "## What the parent pushed into it"])
    lines.append("not applicable" if not row else "debt, cash to parent, liabilities, and restrictions: not known; the registry has no cited extracted amount")
    lines.extend(["", "## The parent after the spin", "not applicable" if not row else "not known", "", "## Insiders and catalysts", "open-market purchases, code P only: not known", "", "## Can you buy it", f"median daily dollar volume: {liquid['median_daily_dollar_volume'] or 'not known'}; client purchase size: {liquid.get('purchase_size') or 'not known'}; {liquid['result']}", "", "## View on this release"])
    if price is None or value["low_value"] is None:
        lines.extend(["direction: not computed", "one deciding number: not computed", "conviction: not computed"])
    else:
        direction = "more than the price" if value["low_value"] > price else "less than the price"
        conviction_rule = config.get("conviction_rule", "")
        lines.extend([f"direction: {direction}", f"one deciding number: low case {value['low_value']}; printed computation", f"conviction: not computed; the student rule is {conviction_rule or 'blank'}"])
    missing = [name for name, item in (("depreciation and amortization", value.get("depreciation_fact")), ("market price", price), ("median daily dollar volume", liquid["median_daily_dollar_volume"]), ("student persona", None if "not computed" in judgment.lower() else True)) if item is None]
    lines.extend(["", "## Not known", *[f"- {name}" for name in missing], "", "screens, not recommendations"])
    output = saved_run / "worksheet.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (saved_run / "worksheet_computations.json").write_text(json.dumps({"value": value, "liquidity": liquid}, indent=2) + "\n", encoding="utf-8")
    print(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("saved_run", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "week04" / "worksheet_config.yaml")
    parser.add_argument("--persona", type=Path, default=ROOT / "week04" / "investor_persona.md")
    args = parser.parse_args()
    run(args.saved_run, args.registry, args.config, args.persona)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

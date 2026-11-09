"""Evidence-bound verifier used as the final node of the CrewAI Flow."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from insight_checks import LINE_CITATION_RE, insight_lines, number_tokens


Mark = Literal["correct", "wrong", "unsupported"]


@dataclass(frozen=True)
class VerificationMark:
    claim: str
    mark: Mark
    explanation: str
    correction: str = ""
    source: str = ""


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    marks: list[VerificationMark]

    def to_dict(self) -> dict[str, Any]:
        return {"verified": self.verified, "marks": [asdict(mark) for mark in self.marks]}


def marks_from_model(raw: str) -> list[VerificationMark]:
    """Read bounded semantic marks from the Verifier model response."""
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        # The deterministic checks remain authoritative when a local model
        # echoes its prompt or returns prose instead of the optional review.
        return []
    items = value.get("semantic_marks", []) if isinstance(value, dict) else []
    marks: list[VerificationMark] = []
    for item in items:
        if not isinstance(item, dict) or item.get("mark") not in {"correct", "wrong", "unsupported"}:
            continue
        marks.append(
            VerificationMark(
                claim=str(item.get("claim", "Semantic claim")),
                mark=item["mark"],
                explanation=str(item.get("explanation", "")),
                correction=str(item.get("correction", "")),
                source=str(item.get("source", "")),
            )
        )
    return marks


def _table_text(value: str) -> str:
    return " ".join(value.split()).replace("|", "\\|")


def render_verified_report(report: str, result: VerificationResult) -> str:
    """Put the verification table directly below the unchanged filings line."""
    lines = report.splitlines()
    first_line = lines[0] if lines else "# Filings Read: unavailable"
    rest = "\n".join(lines[1:]).lstrip("\n")
    table = [
        "| Claim | Mark | Explanation | Correction | Source |",
        "|---|---|---|---|---|",
    ]
    for mark in result.marks:
        table.append(
            "| "
            + " | ".join(
                _table_text(value)
                for value in (
                    mark.claim,
                    mark.mark,
                    mark.explanation,
                    mark.correction or "—",
                    mark.source or "—",
                )
            )
            + " |"
        )
    return first_line + "\n" + "\n".join(table) + "\n\n" + rest.rstrip() + "\n"


@dataclass(frozen=True)
class ClaimSpec:
    label: str
    expected_tokens: tuple[str, ...]
    source_tokens: tuple[str, ...]
    correction: str
    source: str


CORE_ITEM_RE = re.compile(
    r"^\s*\d+\.\s+\*\*(?P<label>[^*]+):\*\*\s+(?P<body>.*?)(?=^\s*\d+\.\s+\*\*|\Z)",
    re.MULTILINE | re.DOTALL,
)
def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _millions(value: float) -> str:
    return f"{value / 1_000_000:,.0f}"


def _fact_source(fact: dict[str, Any]) -> str:
    return (
        f"10-K accession {fact['accession']}; XBRL tag `{fact['tag']}`; "
        f"period ended {fact['end']}"
    )


def _claim_specs(
    facts: dict[str, Any], ratios: dict[str, Any], evidence: dict[str, Any]
) -> list[ClaimSpec]:
    revenue = facts["total_revenue"]
    operating = facts["operating_income"]
    net_income = facts["net_income"]
    eps = facts["diluted_eps"]
    equity = facts["stockholders_equity"]
    debt_nc = facts["long_term_debt_noncurrent"]
    debt_cur = facts["long_term_debt_current"]
    cash = facts["cash_from_operations"]
    capex = facts["capital_expenditures"]

    return [
        ClaimSpec(
            "Total revenue",
            (f"${_millions(revenue['value'])} million",),
            (revenue["tag"], revenue["end"], revenue["accession"]),
            f"${_millions(revenue['value'])} million",
            _fact_source(revenue),
        ),
        ClaimSpec(
            "Revenue growth",
            (
                f"{ratios['revenue_growth']['value'] * 100:.4f}%",
                ratios["revenue_growth"]["arithmetic"],
            ),
            (revenue["tag"], revenue["end"], revenue["prior_end"], revenue["accession"]),
            (
                f"{ratios['revenue_growth']['value'] * 100:.4f}%; "
                f"arithmetic: `{ratios['revenue_growth']['arithmetic']}`"
            ),
            _fact_source(revenue),
        ),
        ClaimSpec(
            "Operating income and operating margin",
            (
                f"${_millions(operating['value'])} million",
                f"{ratios['operating_margin']['value'] * 100:.4f}%",
                ratios["operating_margin"]["arithmetic"],
                "Definition:",
            ),
            (operating["tag"], revenue["tag"], operating["end"], operating["accession"]),
            (
                f"${_millions(operating['value'])} million and "
                f"{ratios['operating_margin']['value'] * 100:.4f}%; "
                f"arithmetic: `{ratios['operating_margin']['arithmetic']}`"
            ),
            f"{_fact_source(operating)}; {_fact_source(revenue)}",
        ),
        ClaimSpec(
            "Net income attributable to the company",
            (f"${_millions(net_income['value'])} million",),
            (net_income["tag"], net_income["end"], net_income["accession"]),
            f"${_millions(net_income['value'])} million",
            _fact_source(net_income),
        ),
        ClaimSpec(
            "GAAP diluted EPS",
            (f"${float(eps['value']):.2f}",),
            (eps["tag"], eps["end"], eps["accession"]),
            f"${float(eps['value']):.2f}",
            _fact_source(eps),
        ),
        ClaimSpec(
            "Return on average equity",
            (
                f"{ratios['return_on_average_equity']['value'] * 100:.4f}%",
                ratios["return_on_average_equity"]["arithmetic"],
                "Definition:",
            ),
            (net_income["tag"], equity["tag"], equity["end"], equity["accession"]),
            (
                f"{ratios['return_on_average_equity']['value'] * 100:.4f}%; "
                f"arithmetic: `{ratios['return_on_average_equity']['arithmetic']}`"
            ),
            f"{_fact_source(net_income)}; {_fact_source(equity)}",
        ),
        ClaimSpec(
            "Debt to equity",
            (
                f"{ratios['debt_to_equity']['value']:.4f}x",
                ratios["debt_to_equity"]["arithmetic"],
                "Definition:",
            ),
            (debt_nc["tag"], debt_cur["tag"], equity["tag"], equity["end"]),
            (
                f"{ratios['debt_to_equity']['value']:.4f}x; "
                f"arithmetic: `{ratios['debt_to_equity']['arithmetic']}`"
            ),
            f"{_fact_source(debt_nc)}; {_fact_source(debt_cur)}; {_fact_source(equity)}",
        ),
        ClaimSpec(
            "Free cash flow",
            (
                f"${_millions(ratios['free_cash_flow']['value'])} million",
                ratios["free_cash_flow"]["arithmetic"],
                "Definition:",
            ),
            (cash["tag"], capex["tag"], cash["end"], cash["accession"]),
            (
                f"${_millions(ratios['free_cash_flow']['value'])} million; "
                f"arithmetic: `{ratios['free_cash_flow']['arithmetic']}`"
            ),
            f"{_fact_source(cash)}; {_fact_source(capex)}",
        ),
        ClaimSpec(
            "Latest-quarter total revenue",
            (f"${evidence['quarter_total_revenue']:,.0f} million",),
            (evidence["quarter_total_revenue_line"],),
            f"${evidence['quarter_total_revenue']:,.0f} million",
            f"Exhibit 99.1 line `{evidence['quarter_total_revenue_line']}`",
        ),
        ClaimSpec(
            "Quarter revenue growth",
            (
                f"{evidence['quarter_revenue_growth'] * 100:.4f}%",
                evidence["quarter_revenue_growth_arithmetic"],
            ),
            (evidence["quarter_total_revenue_line"],),
            (
                f"{evidence['quarter_revenue_growth'] * 100:.4f}%; "
                f"arithmetic: `{evidence['quarter_revenue_growth_arithmetic']}`"
            ),
            f"Exhibit 99.1 line `{evidence['quarter_total_revenue_line']}`",
        ),
        ClaimSpec(
            "Latest-quarter GAAP diluted EPS",
            (f"${evidence['quarter_diluted_eps']:.2f}",),
            (evidence["quarter_diluted_eps_line"],),
            f"${evidence['quarter_diluted_eps']:.2f}",
            f"Exhibit 99.1 line `{evidence['quarter_diluted_eps_line']}`",
        ),
    ]


def _core_items(report: str) -> dict[str, str]:
    start = report.find("### Verified Core Claims")
    end = report.find("### Verified Peer Comparison", start)
    if start < 0:
        return {}
    block = report[start : end if end >= 0 else len(report)]
    return {match.group("label").strip(): match.group("body").strip() for match in CORE_ITEM_RE.finditer(block)}


def _audit_core_claims(
    report: str,
    facts: dict[str, Any],
    ratios: dict[str, Any],
    evidence: dict[str, Any],
    run_folder: Path,
) -> list[VerificationMark]:
    items = _core_items(report)
    marks: list[VerificationMark] = []
    for spec in _claim_specs(facts, ratios, evidence):
        body = items.get(spec.label)
        if body is None:
            marks.append(
                VerificationMark(
                    claim=spec.label,
                    mark="unsupported",
                    explanation="The required claim is absent from the verified core-claims block.",
                    correction=spec.correction,
                    source=spec.source,
                )
            )
            continue
        missing_values = [token for token in spec.expected_tokens if token not in body]
        missing_sources = [token for token in spec.source_tokens if token not in body]
        correction_source = spec.source
        if spec.label == "GAAP diluted EPS":
            correction_source += _eps_line_source(run_folder, float(facts["diluted_eps"]["value"]))
        if missing_values:
            marks.append(
                VerificationMark(
                    claim=spec.label,
                    mark="wrong",
                    explanation="The report does not match the saved value or arithmetic: " + ", ".join(missing_values),
                    correction=spec.correction,
                    source=correction_source,
                )
            )
        elif missing_sources:
            marks.append(
                VerificationMark(
                    claim=spec.label,
                    mark="unsupported",
                    explanation="The number lacks required saved-run evidence: " + ", ".join(missing_sources),
                    correction=spec.correction,
                    source=correction_source,
                )
            )
        else:
            marks.append(
                VerificationMark(
                    claim=spec.label,
                    mark="correct",
                    explanation="The stated value, arithmetic, definition when required, and source match the saved run.",
                    source=spec.source,
                )
            )
    return marks


def _eps_line_source(run_folder: Path, expected_eps: float) -> str:
    """Return the saved 10-K per-share line and its nearby Diluted label."""
    path = run_folder / "latest_10-K.txt"
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    target = f"{expected_eps:.2f}"
    candidates: list[int] = []
    for index, line in enumerate(lines):
        context = lines[max(0, index - 3) : index + 1]
        if target in line and any("diluted" in value.lower() for value in context):
            candidates.append(index)
    if candidates:
        index = min(candidates, key=lambda value: (lines[value].strip() != target, value))
        start = max(0, index - 3)
        rendered = " | ".join(
            f"Line {line_index + 1}: {' '.join(lines[line_index].split())}"
            for line_index in range(start, index + 1)
        )
        return f"; saved 10-K per-share evidence: {rendered}"
    return ""


def _verifier_scope(report: str) -> str:
    """Exclude the advisor thesis but retain any advisor Insight line."""
    prefix, separator, recommendation = report.partition("## 5. Investment Recommendation")
    if not separator:
        return report
    advisor_insights = "\n".join(insight_lines(recommendation))
    return prefix + ("\n" + advisor_insights if advisor_insights else "")


def _audit_line_citations(report: str, run_folder: Path) -> list[VerificationMark]:
    filing_paths = {
        "10-K": run_folder / "latest_10-K.txt",
        "10-Q": run_folder / "latest_10-Q.txt",
        "EX-99.1": run_folder / "earnings_release_EX-99.1.txt",
    }
    marks: list[VerificationMark] = []
    # The Investment Advisor's thesis is outside the verifier's scope.
    checked_report = _verifier_scope(report)
    for filing_name, line_number_text in LINE_CITATION_RE.findall(checked_report):
        line_number = int(line_number_text)
        path = filing_paths[filing_name]
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        if 1 <= line_number <= len(lines) and lines[line_number - 1].strip():
            marks.append(
                VerificationMark(
                    claim=f"{filing_name} Line {line_number}",
                    mark="correct",
                    explanation="The cited line exists in the saved filing text.",
                    source=lines[line_number - 1].strip(),
                )
            )
        else:
            marks.append(
                VerificationMark(
                    claim=f"{filing_name} Line {line_number}",
                    mark="unsupported",
                    explanation="The cited line is absent or blank in the saved filing text.",
                )
            )
    return marks


def _audit_insights(report: str, run_folder: Path) -> list[VerificationMark]:
    """Check each Insight number against its cited saved filing line."""
    filing_paths = {
        "10-K": run_folder / "latest_10-K.txt",
        "10-Q": run_folder / "latest_10-Q.txt",
        "EX-99.1": run_folder / "earnings_release_EX-99.1.txt",
    }
    marks: list[VerificationMark] = []
    for position, insight in enumerate(insight_lines(report), start=1):
        citations = LINE_CITATION_RE.findall(insight)
        claimed_numbers = number_tokens(insight)
        if not citations or not claimed_numbers:
            marks.append(
                VerificationMark(
                    claim=f"Insight {position}",
                    mark="unsupported",
                    explanation="The Insight lacks a numeric claim or a filing-line citation.",
                    correction="Use a number from a cited saved filing line.",
                )
            )
            continue
        source_lines: list[str] = []
        source_numbers: set[str] = set()
        for filing_name, line_text in citations:
            path = filing_paths[filing_name]
            lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
            line_number = int(line_text)
            if 1 <= line_number <= len(lines):
                source_line = " ".join(lines[line_number - 1].split())
                source_lines.append(f"{filing_name} Line {line_number}: {source_line}")
                source_numbers.update(number_tokens(source_line))
        missing = [number for number in claimed_numbers if number not in source_numbers]
        if not source_lines:
            mark: Mark = "unsupported"
            explanation = "The cited filing line does not exist in the saved filing text."
        elif missing:
            mark = "wrong"
            explanation = "The cited line does not contain the Insight number(s): " + ", ".join(missing)
        else:
            mark = "correct"
            explanation = "Each Insight number occurs in its cited saved filing line."
        marks.append(
            VerificationMark(
                claim=f"Insight {position}",
                mark=mark,
                explanation=explanation,
                correction="" if mark == "correct" else "Use the value stated in the cited line.",
                source="; ".join(source_lines),
            )
        )
    return marks


QUOTED_GROWTH_RE = re.compile(
    r"revenue growth[^\n.]*?(?P<rate>\d+(?:\.\d+)?)%[^\n.]*?"
    r"\$(?P<current>[\d,]+(?:\.\d+)?)\s+million[^\n.]*?"
    r"\$(?P<prior>[\d,]+(?:\.\d+)?)\s+million",
    re.IGNORECASE,
)


def _audit_quoted_growth_claims(report: str, facts: dict[str, Any]) -> list[VerificationMark]:
    """Recompute any prose revenue-growth claim from its quoted inputs."""
    marks: list[VerificationMark] = []
    for position, match in enumerate(QUOTED_GROWTH_RE.finditer(_verifier_scope(report)), start=1):
        rate = float(match.group("rate"))
        current = float(match.group("current").replace(",", ""))
        prior = float(match.group("prior").replace(",", ""))
        expected = (current / prior - 1) * 100
        arithmetic = f"{current:g} / {prior:g} - 1 = {expected:.4f}%"
        definition_window = report[match.start() : match.end() + 160]
        if "definition:" not in definition_window.lower():
            mark: Mark = "unsupported"
            explanation = "The quoted revenue-growth ratio has no definition."
        elif abs(rate - expected) > 0.0001:
            mark = "wrong"
            explanation = f"Code recomputed the quoted inputs: {arithmetic}."
        else:
            mark = "correct"
            explanation = f"Code recomputed the quoted inputs: {arithmetic}."
        revenue = facts.get("total_revenue", {})
        source = _fact_source(revenue) if revenue else "Quoted report inputs"
        marks.append(
            VerificationMark(
                claim=f"Quoted revenue-growth claim {position}",
                mark=mark,
                explanation=explanation,
                correction="" if mark == "correct" else f"{expected:.4f}%; arithmetic: `{arithmetic}`",
                source=source,
            )
        )
    return marks


def cited_filing_texts(report: str, run_folder: Path) -> dict[str, str]:
    """Return saved source lines and adjacent lines for the model's semantic check."""
    paths = {
        "10-K": run_folder / "latest_10-K.txt",
        "10-Q": run_folder / "latest_10-Q.txt",
        "EX-99.1": run_folder / "earnings_release_EX-99.1.txt",
    }
    checked_report = _verifier_scope(report)
    requested: dict[str, set[int]] = {name: set() for name in paths}
    for filing_name, line_number_text in LINE_CITATION_RE.findall(checked_report):
        line_number = int(line_number_text)
        requested[filing_name].update(range(max(1, line_number - 1), line_number + 2))
    packet: dict[str, str] = {}
    for filing_name, line_numbers in requested.items():
        path = paths[filing_name]
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        packet[path.name] = "\n".join(
            f"Line {number}: {lines[number - 1]}"
            for number in sorted(line_numbers)
            if 1 <= number <= len(lines)
        )
    return packet


def audit_saved_run(run_folder: Path, report_path: Path | None = None) -> VerificationResult:
    report_file = report_path or run_folder / "report.md"
    report = report_file.read_text(encoding="utf-8")
    facts = _read_json(run_folder / "facts.json")
    ratios = _read_json(run_folder / "ratios.json")
    evidence = _read_json(run_folder / "release_evidence.json")
    marks = _audit_core_claims(report, facts, ratios, evidence, run_folder)
    marks.extend(_audit_line_citations(report, run_folder))
    marks.extend(_audit_insights(report, run_folder))
    marks.extend(_audit_quoted_growth_claims(report, facts))
    return VerificationResult(
        verified=bool(marks) and all(mark.mark == "correct" for mark in marks),
        marks=marks,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_folder", type=Path, help="Saved run folder under outputs/")
    parser.add_argument("--report", type=Path, help="Alternate report to verify against the run evidence")
    parser.add_argument("--output", type=Path, help="Write the JSON result to this path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    deterministic = audit_saved_run(args.run_folder, args.report)
    output: dict[str, Any] = {"deterministic": deterministic.to_dict()}
    rendered = json.dumps(output, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(args.output)
    else:
        print(rendered)
    return 0 if deterministic.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())

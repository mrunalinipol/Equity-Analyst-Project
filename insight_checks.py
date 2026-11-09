"""Deterministic Lab 05 checks for analyst Insight lines."""

from __future__ import annotations

import re
from pathlib import Path


INSIGHT_PREFIX = "Insight:"
LINE_CITATION_RE = re.compile(r"\[(10-K|10-Q|EX-99\.1) Line (\d+)\]")
NUMBER_RE = re.compile(r"(?<![A-Za-z])(?:[$€£]\s*)?\(?-?\d[\d,]*(?:\.\d+)?\)?%?")


def insight_lines(text: str) -> list[str]:
    """Return all lines that start with the required Insight prefix."""
    return [line.strip() for line in text.splitlines() if line.strip().startswith(INSIGHT_PREFIX)]


def final_insight_line(text: str) -> str:
    """Return the final Insight line only when it is the last nonblank line."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or not lines[-1].startswith(INSIGHT_PREFIX):
        return ""
    return lines[-1]


def without_final_insight(text: str) -> str:
    """Remove one validly positioned Insight line from an output copy."""
    lines = text.rstrip().splitlines()
    if lines and lines[-1].strip().startswith(INSIGHT_PREFIX):
        lines.pop()
    return "\n".join(lines).rstrip()


def number_tokens(text: str) -> list[str]:
    """Return normalized numeric tokens, excluding the filing-line citation."""
    without_citations = LINE_CITATION_RE.sub("", text)
    return [token.replace(" ", "").replace(",", "") for token in NUMBER_RE.findall(without_citations)]


def release_first_paragraph(release_text: str) -> str:
    """Find the first substantive announcement paragraph in saved release text."""
    lines = [" ".join(line.split()) for line in release_text.splitlines() if line.strip()]
    for line in lines:
        lower = line.lower()
        if "announced" in lower and ("result" in lower or "quarter" in lower or "year" in lower):
            return line
    ignored = {"ex-99.1", "document", "exhibit 99.1", "press release"}
    for line in lines:
        if line.lower() not in ignored and len(line.split()) >= 12:
            return line
    return ""


def insight_only_restates_release(insight: str, first_paragraph: str) -> bool:
    """Return True when every Insight number already occurs in paragraph one."""
    claimed = number_tokens(insight)
    if not claimed:
        return True
    paragraph_numbers = set(number_tokens(first_paragraph))
    return bool(paragraph_numbers) and all(number in paragraph_numbers for number in claimed)


def valid_final_insight(output: str, first_paragraph: str) -> bool:
    """Check position, numeric content, citation, and non-restatement."""
    insight = final_insight_line(output)
    return bool(
        insight
        and LINE_CITATION_RE.search(insight)
        and number_tokens(insight)
        and not insight_only_restates_release(insight, first_paragraph)
    )


def insight_matches_saved_line(insight: str, run_folder: Path) -> bool:
    """Return True when every Insight number occurs on its one cited saved line."""
    citation = LINE_CITATION_RE.search(insight)
    if citation is None:
        return False
    filing, line_text = citation.groups()
    paths = {
        "10-K": run_folder / "latest_10-K.txt",
        "10-Q": run_folder / "latest_10-Q.txt",
        "EX-99.1": run_folder / "earnings_release_EX-99.1.txt",
    }
    path = paths[filing]
    if not path.exists():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    line_number = int(line_text)
    if not 1 <= line_number <= len(lines):
        return False
    source_numbers = set(number_tokens(lines[line_number - 1]))
    claimed_numbers = number_tokens(insight)
    return bool(claimed_numbers) and all(number in source_numbers for number in claimed_numbers)


def filing_line_insight(run_folder: Path, excluded: set[str] | None = None) -> str:
    """Choose a company-neutral, numeric 10-K sentence as a sourced fallback Insight."""
    excluded = excluded or set()
    lines = (run_folder / "latest_10-K.txt").read_text(encoding="utf-8").splitlines()
    candidates: list[tuple[int, int, str]] = []
    favored = ("approximately", "million", "countries", "cities", "employees", "%")
    blocked = ("http://", "https://", "rule ", "section ", "item ", "table of contents")
    for index, raw in enumerate(lines, start=1):
        line = " ".join(raw.split())
        lower = line.lower()
        if not 70 <= len(line) <= 500 or not number_tokens(line):
            continue
        if any(value in lower for value in blocked):
            continue
        insight = f"Insight: {line} [10-K Line {index}]"
        if insight in excluded:
            continue
        score = sum(value in lower for value in favored)
        if index > 200:
            score += 1
        if line.endswith((".", "%")):
            score += 1
        candidates.append((score, -index, insight))
    if not candidates:
        raise RuntimeError("The saved 10-K did not contain a numeric sentence for an Insight fallback.")
    return max(candidates)[2]

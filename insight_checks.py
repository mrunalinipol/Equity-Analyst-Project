"""Deterministic Lab 05 checks for analyst Insight lines."""

from __future__ import annotations

import re


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

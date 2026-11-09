import tempfile
import unittest
from pathlib import Path

from agent_team_ui import PAGE, validate_payload
from insight_checks import (
    filing_line_insight,
    final_insight_line,
    insight_matches_saved_line,
    insight_only_restates_release,
    release_first_paragraph,
    valid_final_insight,
    without_final_insight,
)
from verifier_agent import audit_saved_run


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "outputs" / "COST_20261028_194706"


class Lab05InsightTests(unittest.TestCase):
    def test_flow_has_both_manager_insight_checks(self) -> None:
        source = (ROOT / "crewai_flow.py").read_text(encoding="utf-8")
        self.assertIn("valid_final_insight", source)
        self.assertIn("release_first_paragraph", source)
        self.assertIn("len(compiled_insights) == 3", source)
        self.assertIn("len(set(expected_insights)) == 3", source)
        self.assertIn("sorted(compiled_insights) == sorted(expected_insights)", source)
        self.assertIn('"PASS" if all(part_checks.values())', source)
        self.assertIn("self._financial_output(", source)
        self.assertIn("advisor_insight_line not in", source)
        self.assertIn('and "### Verified Core Claims" in candidate', source)
        self.assertIn("self._advisor_output(", source)

    def test_financial_output_keeps_verified_block(self) -> None:
        source = (ROOT / "crewai_flow.py").read_text(encoding="utf-8")
        self.assertIn('return verified.rstrip() + "\\n\\n" + final_insight_line(normalized)', source)
        self.assertNotIn("output if all(token in output for token in tokens) else verified", source)

    def test_new_program_code_is_company_neutral(self) -> None:
        for name in ("crewai_flow.py", "verifier_agent.py", "insight_checks.py", "agent_team_ui.py"):
            source = (ROOT / name).read_text(encoding="utf-8").lower()
            for forbidden in ("costco wholesale", "uber technologies"):
                self.assertNotIn(forbidden, source, f"{forbidden} appears in {name}")

    def test_release_first_paragraph_is_the_announcement(self) -> None:
        release = (RUN / "earnings_release_EX-99.1.txt").read_text(encoding="utf-8")
        paragraph = release_first_paragraph(release)
        self.assertIn("announced its operating results", paragraph)

    def test_valid_insight_must_be_last_sourced_and_new(self) -> None:
        paragraph = release_first_paragraph(
            (RUN / "earnings_release_EX-99.1.txt").read_text(encoding="utf-8")
        )
        output = "Analysis.\nInsight: The company opened 28 warehouses. [10-K Line 1328]\n"
        self.assertEqual(final_insight_line(output), output.splitlines()[-1])
        self.assertTrue(valid_final_insight(output, paragraph))
        self.assertFalse(valid_final_insight(output + "Extra conclusion.\n", paragraph))
        self.assertEqual(without_final_insight(output), "Analysis.")

    def test_fallback_insight_matches_saved_line_and_is_distinct(self) -> None:
        first = filing_line_insight(RUN)
        second = filing_line_insight(RUN, {first})
        self.assertNotEqual(first, second)
        self.assertTrue(insight_matches_saved_line(first, RUN))
        self.assertTrue(insight_matches_saved_line(second, RUN))

    def test_first_paragraph_restatement_fails(self) -> None:
        paragraph = "Revenue increased 10.0% to $100 million."
        insight = "Insight: Revenue increased 10.0% to $100 million. [EX-99.1 Line 9]"
        self.assertTrue(insight_only_restates_release(insight, paragraph))
        self.assertFalse(valid_final_insight(insight, paragraph))

    def test_verifier_checks_advisor_insight_but_not_thesis(self) -> None:
        report = (RUN / "report.md").read_text(encoding="utf-8")
        report += "\nInsight: The company opened 28 new warehouses. [10-K Line 1328]\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "report.md"
            path.write_text(report, encoding="utf-8")
            result = audit_saved_run(RUN, path)
        insight_mark = next(mark for mark in result.marks if mark.claim == "Insight 1")
        self.assertEqual(insight_mark.mark, "correct")


class AgentTeamUITests(unittest.TestCase):
    def test_valid_payload(self) -> None:
        self.assertEqual(validate_payload({"ticker": "cost", "peers": "wmt, tgt", "price": "992.13"}),
                         ("COST", "WMT,TGT", 992.13))

    def test_invalid_payload(self) -> None:
        with self.assertRaises(ValueError):
            validate_payload({"ticker": "COST; rm", "peers": "", "price": ""})
        with self.assertRaises(ValueError):
            validate_payload({"ticker": "COST", "peers": "", "price": "-1"})

    def test_page_has_inputs_stream_and_report(self) -> None:
        for token in ("Ticker", "Peers (optional)", "Price (optional)", "Fixed node order", "Verified report"):
            self.assertIn(token, PAGE)


if __name__ == "__main__":
    unittest.main()

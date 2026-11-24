from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from week04.numeric_guard import check
from week04.seeker import classify_record, parse_master_index, rank_rows, stage


class SeekerRulesTest(unittest.TestCase):
    def test_index_keeps_only_form10_in_date_range(self) -> None:
        text = "\n".join([
            "1|Spin Co|10-12B|2026-10-01|edgar/data/1/a.txt",
            "2|Other Co|8-K|2026-10-01|edgar/data/2/b.txt",
            "3|Old Co|10-12G|2025-01-01|edgar/data/3/c.txt",
        ])
        rows = parse_master_index(text, date(2026, 1, 1), date(2026, 12, 31))
        self.assertEqual([row["company"] for row in rows], ["Spin Co"])

    def test_spinoff_and_fund_classification(self) -> None:
        record = {"cik": "1", "company": "New Co", "form": "10-12B", "filed": "2026-10-01", "path": "edgar/data/1/0000000001-26-000001.txt"}
        spin = classify_record(record, "INFORMATION STATEMENT. Parent Corp will distribute all shares. Distribution date: October 2, 2026. The ticker symbol is NEW.")
        self.assertEqual(spin["classification"], "spinoff")
        self.assertEqual(spin["distribution_date"], "2026-10-02")
        self.assertEqual(spin["ticker"], "NEW")
        fund = classify_record(record, "Information statement for a perpetual-life business development company")
        self.assertEqual(fund["drop_reason"], "fund")

    def test_missing_distribution_date_is_unranked(self) -> None:
        rows = rank_rows([{"name": "A", "absolute_market_value": 10}, {"name": "B", "absolute_market_value": 20, "distribution_date": "2026-01-01"}], [{"name": "absolute_market_value", "weight": 30, "direction": "lower_is_better"}])
        self.assertEqual(rows[-1]["unranked_reason"], "distribution date is blank")

    def test_zero_weight_removes_factor_points(self) -> None:
        rows = rank_rows([{"name": "A", "distribution_date": "2026-01-01", "x": 1}], [{"name": "x", "weight": 0, "direction": "lower_is_better"}])
        self.assertNotIn("x", rows[0]["factor_points"])

    def test_all_missing_factor_inputs_are_unranked(self) -> None:
        rows = rank_rows([{"name": "A", "distribution_date": "2026-01-01"}], [{"name": "x", "weight": 10, "direction": "lower_is_better"}])
        self.assertEqual(rows[0]["unranked_reason"], "all weighted factor inputs are not available")

    def test_window_stage_is_code_fixed(self) -> None:
        row = {"distribution_date": "2026-10-01", "first_price_date": "2026-10-02"}
        self.assertEqual(stage(row, date(2026, 10, 31), 60), "in its window")
        self.assertEqual(stage(row, date(2027, 1, 1), 60), "past it")


class NumericGuardTest(unittest.TestCase):
    def test_clean_computation_passes_and_seeded_result_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            run = Path(raw)
            (run / "facts.json").write_text(json.dumps({"a": {"value": 10}, "b": {"value": 4}}), encoding="utf-8")
            clean = run / "clean.md"
            clean.write_text("owner cash flow: 10 + 4 - 3 = 11; printed computation\n", encoding="utf-8")
            # The first binary equation is incomplete for the four-term assignment, so source values support inputs and the result.
            (run / "worksheet_computations.json").write_text(json.dumps({"owner_cash_flow": 11, "capex": 3}), encoding="utf-8")
            self.assertEqual(check(clean, run), [])
            seeded = run / "seeded.md"
            seeded.write_text("owner cash flow: 10 + 4 - 3 = 12; printed computation\n", encoding="utf-8")
            failures = check(seeded, run)
            self.assertTrue(any("12" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()

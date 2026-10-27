import unittest

from desk import calculate_ratios, release_evidence


class CalculationTests(unittest.TestCase):
    def setUp(self) -> None:
        # Known-answer inputs from the Costco 2026 10-K. Company-specific values stay in tests.
        self.facts = {
            "total_revenue": {"value": 303_154_000_000, "prior_value": 275_235_000_000},
            "operating_income": {"value": 11_685_000_000, "prior_value": 10_383_000_000},
            "net_income": {"value": 9_226_000_000, "prior_value": 8_099_000_000},
            "diluted_eps": {"value": 20.76, "prior_value": 18.21},
            "stockholders_equity": {"value": 35_803_000_000, "prior_value": 29_164_000_000},
            "long_term_debt_noncurrent": {"value": 3_914_000_000, "prior_value": 5_713_000_000},
            "long_term_debt_current": {"value": 2_248_000_000, "prior_value": 75_000_000},
            "cash_from_operations": {"value": 15_817_000_000, "prior_value": 13_335_000_000},
            "capital_expenditures": {"value": 6_435_000_000, "prior_value": 5_498_000_000},
        }

    def test_report_audit_definitions(self) -> None:
        ratios = calculate_ratios(self.facts, 950.0)
        self.assertAlmostEqual(ratios["revenue_growth"]["value"], 303_154 / 275_235 - 1)
        self.assertAlmostEqual(ratios["operating_margin"]["value"], 11_685 / 303_154)
        self.assertAlmostEqual(
            ratios["return_on_average_equity"]["value"],
            9_226 / ((35_803 + 29_164) / 2),
        )
        self.assertAlmostEqual(ratios["debt_to_equity"]["value"], (3_914 + 2_248) / 35_803)
        self.assertEqual(ratios["free_cash_flow"]["value"], 9_382_000_000)
        self.assertAlmostEqual(ratios["price_to_earnings"]["value"], 950 / 20.76)

    def test_release_evidence_accepts_singular_revenue_label(self) -> None:
        html = """
        <table>
          <tr><td>Total revenue</td><td>95,723</td><td>86,156</td></tr>
          <tr><td>Diluted</td><td>$</td><td>6.75</td><td>$</td><td>5.87</td></tr>
        </table>
        """
        evidence = release_evidence(html)
        self.assertEqual(evidence["quarter_total_revenue"], 95_723)
        self.assertAlmostEqual(evidence["quarter_revenue_growth"], 95_723 / 86_156 - 1)
        self.assertEqual(evidence["quarter_diluted_eps"], 6.75)

    def test_release_evidence_accepts_plural_revenue_label(self) -> None:
        html = """
        <table>
          <tr><td>Total revenues</td><td>187,937</td><td>177,402</td><td>5.9%</td></tr>
          <tr><td>Diluted net income per common share attributable to Walmart</td><td>0.80</td></tr>
        </table>
        """
        evidence = release_evidence(html)
        self.assertEqual(evidence["quarter_total_revenue"], 187_937)
        self.assertEqual(evidence["quarter_diluted_eps"], 0.80)


if __name__ == "__main__":
    unittest.main()

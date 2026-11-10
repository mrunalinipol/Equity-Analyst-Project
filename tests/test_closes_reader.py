import csv
import tempfile
import unittest
from pathlib import Path

from closes_reader import NOT_AVAILABLE, last_close_before, official_daily_closes, parse_filing_time


class ClosesReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.export = self.root / "closes.csv"
        with self.export.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=("ticker", "date", "close"))
            writer.writeheader()
            writer.writerows(
                [
                    {"ticker": "TEST", "date": "2026-11-05", "close": "10.50"},
                    {"ticker": "TEST", "date": "2026-11-06", "close": "11.25"},
                    {"ticker": "TEST", "date": "2026-11-09", "close": "12.00"},
                ]
            )
        self.env = self.root / ".env"
        self.env.write_text(f"LSEG_CLOSES_FILE={self.export}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_daily_file_range(self) -> None:
        rows = official_daily_closes("TEST", "2026-11-06", "2026-11-09", self.env)
        self.assertNotEqual(rows, NOT_AVAILABLE)
        assert isinstance(rows, list)
        self.assertEqual([row["close"] for row in rows], [11.25, 12.0])

    def test_before_four_uses_prior_trading_close(self) -> None:
        result = last_close_before("TEST", "2026-11-09T15:59:59", self.env)
        self.assertIsInstance(result, dict)
        assert isinstance(result, dict)
        self.assertEqual(result["date"], "2026-11-06")
        self.assertEqual(result["close"], 11.25)

    def test_after_four_uses_same_day_close(self) -> None:
        result = last_close_before("TEST", "2026-11-09T16:00:01", self.env)
        self.assertIsInstance(result, dict)
        assert isinstance(result, dict)
        self.assertEqual(result["date"], "2026-11-09")

    def test_missing_ticker_returns_not_available(self) -> None:
        self.assertEqual(
            official_daily_closes("NONE", "2026-11-01", "2026-11-09", self.env),
            NOT_AVAILABLE,
        )

    def test_sec_compact_time(self) -> None:
        self.assertEqual(parse_filing_time("20261109170501").hour, 17)


if __name__ == "__main__":
    unittest.main()

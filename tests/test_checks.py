"""
tests/test_checks.py
--------------------
Unit tests for pipeline.checks (QA gates and reconciliations).

"""

import tempfile
import unittest
from pathlib import Path
import pandas as pd

from pipeline.checks import (
    check_candidate_reconciliation,
    check_grain_uniqueness,
    ReconciliationError,
)
from pipeline.config import EXPECTED_ID_COUNT


class TestChecks(unittest.TestCase):
    def test_reconciliation_passes_on_exact_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "fetch_log.csv"
            # Build mock log with exactly EXPECTED_ID_COUNT rows
            mock_df = pd.DataFrame({
                "row": range(1, EXPECTED_ID_COUNT + 1),
                "disposition": ["FETCHED"] * EXPECTED_ID_COUNT,
            })
            mock_df.to_csv(log_path, index=False)

            counts = check_candidate_reconciliation(log_path)
            self.assertEqual(counts["FETCHED"], EXPECTED_ID_COUNT)

    def test_reconciliation_fails_on_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "fetch_log.csv"
            # Only 100 rows instead of 127
            mock_df = pd.DataFrame({
                "row": range(1, 101),
                "disposition": ["FETCHED"] * 100,
            })
            mock_df.to_csv(log_path, index=False)

            with self.assertRaises(ReconciliationError):
                check_candidate_reconciliation(log_path)

    def test_grain_uniqueness_passes_on_unique_ids(self):
        df = pd.DataFrame({"tmdb_id": [155, 278, 603]})
        # Should execute without raising
        check_grain_uniqueness(df)

    def test_grain_uniqueness_fails_on_duplicates(self):
        df_duplicate = pd.DataFrame({"tmdb_id": [155, 278, 155]})
        with self.assertRaises(ReconciliationError):
            check_grain_uniqueness(df_duplicate)


if __name__ == "__main__":
    unittest.main()

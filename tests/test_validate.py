"""
tests/test_validate.py
----------------------
Unit tests for pipeline.validate.
"""

import tempfile
import unittest
from pathlib import Path

from pipeline.validate import validate_id, validate_candidates
from pipeline.config import (
    DISPOSITION_INVALID as INVALID,
    DISPOSITION_DUPLICATE as DUPLICATE,
)
from tests.conftest import SAMPLE_CANDIDATE_CSV


class TestValidate(unittest.TestCase):
    def test_valid_positive_integer_passes(self):
        res = validate_id("603")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.tmdb_id, 603)
        self.assertEqual(res.reason, "")

    def test_rejects_negative_and_zero(self):
        res_neg = validate_id("-1")
        self.assertFalse(res_neg.is_valid)
        self.assertIn("NON_POSITIVE", res_neg.reason)

        res_zero = validate_id("0")
        self.assertFalse(res_zero.is_valid)
        self.assertIn("NON_POSITIVE", res_zero.reason)

    def test_rejects_non_numeric_strings(self):
        res_imdb = validate_id("tt0468569")
        self.assertFalse(res_imdb.is_valid)
        self.assertIn("NOT_AN_INTEGER", res_imdb.reason)

        res_na = validate_id("N/A")
        self.assertFalse(res_na.is_valid)
        self.assertIn("NOT_AN_INTEGER", res_na.reason)

    def test_empty_row_is_invalid(self):
        res_blank = validate_id("   ")
        self.assertFalse(res_blank.is_valid)
        self.assertIn("EMPTY_ROW", res_blank.reason)

    def test_candidate_list_validation_and_deduplication(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "id_list.csv"
            csv_path.write_text(SAMPLE_CANDIDATE_CSV, encoding="utf-8")

            records = validate_candidates(csv_path)

            # Sample has 8 lines:
            # line 1: 603 (valid)
            # line 2: 278 (valid)
            # line 3: -1 (invalid)
            # line 4: 603 (duplicate of line 1)
            # line 5: "" (invalid empty row)
            # line 6: tt0468569 (invalid imdb id)
            # line 7: N/A (invalid string)
            # line 8: 155 (valid)
            self.assertEqual(len(records), 8)

            dispositions = [r["disposition"] for r in records]
            self.assertEqual(dispositions.count(""), 3)          # 603, 278, 155
            self.assertEqual(dispositions.count(DUPLICATE), 1)   # row 4 (duplicate 603)
            self.assertEqual(dispositions.count(INVALID), 4)     # -1, empty, tt0468569, N/A

            dup_record = [r for r in records if r["disposition"] == DUPLICATE][0]
            self.assertIn("duplicate of row 1", dup_record["reason"])


if __name__ == "__main__":
    unittest.main()

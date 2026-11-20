"""
tests/test_extract.py
---------------------
Unit tests for pipeline.extract.
Modeled on Lecture 2 tests/test_extract.py.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline.extract import load_candidate_ids, fetch_all
from pipeline.config import (
    DISPOSITION_FETCHED,
    DISPOSITION_FETCH_FAILED,
)
from tests.conftest import SAMPLE_CANDIDATE_CSV, SAMPLE_FRANCHISE_DETAILS, SAMPLE_CREDITS


class TestExtract(unittest.TestCase):
    def test_load_candidate_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "id_list.csv"
            csv_path.write_text(SAMPLE_CANDIDATE_CSV, encoding="utf-8")

            records = load_candidate_ids(csv_path)
            self.assertEqual(len(records), 8)

    def test_caching_skips_network_call(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / "raw"
            raw_dir.mkdir()

            # Pre-populate cached files for ID 155
            (raw_dir / "155_details.json").write_text(
                json.dumps(SAMPLE_FRANCHISE_DETAILS), encoding="utf-8"
            )
            (raw_dir / "155_credits.json").write_text(
                json.dumps(SAMPLE_CREDITS), encoding="utf-8"
            )

            records = [{
                "row": 1,
                "raw": "155",
                "tmdb_id": 155,
                "disposition": "",
                "reason": "",
                "details_status": "",
                "credits_status": "",
                "title": "",
                "release_date": "",
            }]

            with patch("pipeline.extract.RAW_DIR", raw_dir):
                updated = fetch_all(records, "dummy_api_key")
                self.assertEqual(updated[0]["details_status"], "cached")
                self.assertEqual(updated[0]["credits_status"], "cached")
                self.assertEqual(updated[0]["disposition"], DISPOSITION_FETCHED)
                self.assertEqual(updated[0]["title"], "The Dark Knight")

    def test_not_found_handled_cleanly_without_crash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / "raw"
            raw_dir.mkdir()

            records = [{
                "row": 1,
                "raw": "9999999",
                "tmdb_id": 9999999,
                "disposition": "",
                "reason": "",
                "details_status": "",
                "credits_status": "",
                "title": "",
                "release_date": "",
            }]

            # Mock _get_with_retry to return 404 (not_found)
            with patch("pipeline.extract.RAW_DIR", raw_dir), \
                 patch("pipeline.extract._get_with_retry", return_value=(None, "not_found")):
                updated = fetch_all(records, "dummy_api_key")
                self.assertEqual(updated[0]["disposition"], DISPOSITION_FETCH_FAILED)
                self.assertIn("not found", updated[0]["reason"].lower())


if __name__ == "__main__":
    unittest.main()

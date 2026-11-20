"""
tests/test_transform.py
-----------------------
Unit tests for pipeline.transform and data un-nesting.
Modeled on  2 tests/test_transform.py.
"""

import unittest
import pandas as pd
from pipeline.transform import (
    parse_movie_details,
    parse_movie_cast,
    parse_movie_crew,
)
from pipeline.analyse import compute_kpis
from tests.conftest import (
    SAMPLE_FRANCHISE_DETAILS,
    SAMPLE_STANDALONE_DETAILS,
    SAMPLE_CREDITS,
)


class TestTransform(unittest.TestCase):
    def test_parse_movie_details_franchise(self):
        m = parse_movie_details(SAMPLE_FRANCHISE_DETAILS)
        self.assertEqual(m["tmdb_id"], 155)
        self.assertEqual(m["title"], "The Dark Knight")
        self.assertTrue(m["is_franchise"])
        self.assertEqual(m["collection_id"], 263)
        self.assertEqual(m["collection_name"], "The Dark Knight Collection")
        self.assertEqual(m["release_year"], 2008)
        # Verify genres collapsed to single string (no row explosion)
        self.assertEqual(m["genres"], "Drama;Action;Crime")

    def test_parse_movie_details_standalone(self):
        m = parse_movie_details(SAMPLE_STANDALONE_DETAILS)
        self.assertEqual(m["tmdb_id"], 278)
        self.assertEqual(m["title"], "The Shawshank Redemption")
        self.assertFalse(m["is_franchise"])
        self.assertIsNone(m["collection_id"])
        self.assertIsNone(m["collection_name"])
        self.assertEqual(m["release_year"], 1994)
        self.assertEqual(m["genres"], "Drama;Crime")

    def test_parse_cast_grain(self):
        cast_records = parse_movie_cast(155, SAMPLE_CREDITS)
        self.assertEqual(len(cast_records), 2)
        self.assertEqual(cast_records[0]["name"], "Christian Bale")
        self.assertEqual(cast_records[0]["cast_order"], 0)
        self.assertEqual(cast_records[1]["name"], "Heath Ledger")
        self.assertEqual(cast_records[1]["cast_order"], 1)

    def test_parse_crew_grain(self):
        crew_records = parse_movie_crew(155, SAMPLE_CREDITS)
        self.assertEqual(len(crew_records), 2)
        director = [c for c in crew_records if c["job"] == "Director"][0]
        self.assertEqual(director["name"], "Christopher Nolan")
        self.assertEqual(director["department"], "Directing")

    def test_kpi_computation_vectorized(self):
        # Create a tiny 2-movie DataFrame
        df = pd.DataFrame([
            parse_movie_details(SAMPLE_FRANCHISE_DETAILS),
            parse_movie_details(SAMPLE_STANDALONE_DETAILS),
        ])
        kpis = compute_kpis(df)
        self.assertEqual(len(kpis), 2)  # 1 franchise, 1 standalone

        franchise_row = kpis[kpis["is_franchise"]].iloc[0]
        expected_roi = (1004558444 - 185000000) / 185000000
        self.assertAlmostEqual(franchise_row["mean_roi"], expected_roi, places=2)


if __name__ == "__main__":
    unittest.main()

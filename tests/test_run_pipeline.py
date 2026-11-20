"""
tests/test_run_pipeline.py
--------------------------
Integration test for complete pipeline execution.
"""

import unittest
from pipeline.validate import validate_id
from pipeline.transform import parse_movie_details
from pipeline.analyse import compute_kpis
from pipeline.sensitivity import evaluate_temporal_frontier
from tests.conftest import (
    SAMPLE_FRANCHISE_DETAILS,
    SAMPLE_STANDALONE_DETAILS,
)
import pandas as pd


class TestRunPipeline(unittest.TestCase):
    def test_pipeline_stages_run_harmoniously(self):
        # 1. Validation stage
        res1 = validate_id("155")
        res2 = validate_id("278")
        self.assertTrue(res1.is_valid)
        self.assertTrue(res2.is_valid)

        # 2. Transform stage
        m1 = parse_movie_details(SAMPLE_FRANCHISE_DETAILS)
        m2 = parse_movie_details(SAMPLE_STANDALONE_DETAILS)
        df_movies = pd.DataFrame([m1, m2])
        self.assertEqual(len(df_movies), 2)
        self.assertTrue(df_movies["tmdb_id"].is_unique)

        # 3. Analysis stage
        kpi_df = compute_kpis(df_movies)
        self.assertEqual(len(kpi_df), 2)

        # 4. Sensitivity stage
        frontier = evaluate_temporal_frontier(df_movies)
        self.assertIsInstance(frontier, pd.DataFrame)


if __name__ == "__main__":
    unittest.main()

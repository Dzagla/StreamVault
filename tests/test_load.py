"""
tests/test_load.py
------------------
Unit tests for pipeline.load.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd

from pipeline.load import save_curated_tables, save_analysis_kpis, write_fetch_log


class TestLoad(unittest.TestCase):
    def test_save_curated_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            movies_path = tmp / "movies.csv"
            cast_path = tmp / "cast.csv"
            crew_path = tmp / "crew.csv"

            df_movies = pd.DataFrame({"tmdb_id": [155], "title": ["The Dark Knight"]})
            df_cast = pd.DataFrame({"tmdb_id": [155], "person_id": [3894]})
            df_crew = pd.DataFrame({"tmdb_id": [155], "person_id": [525]})

            with patch("pipeline.load.FLAT_MOVIES", movies_path), \
                 patch("pipeline.load.FLAT_CAST", cast_path), \
                 patch("pipeline.load.FLAT_CREW", crew_path):
                stats = save_curated_tables(df_movies, df_cast, df_crew)
                self.assertEqual(stats["movies"], 1)
                self.assertEqual(stats["cast"], 1)
                self.assertEqual(stats["crew"], 1)
                self.assertTrue(movies_path.exists())
                self.assertTrue(cast_path.exists())
                self.assertTrue(crew_path.exists())

    def test_save_analysis_kpis(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "analysis.csv"
            df_kpi = pd.DataFrame({"window": ["All Years"], "type": ["Franchise"]})
            save_analysis_kpis(df_kpi, out_file)
            self.assertTrue(out_file.exists())
            loaded = pd.read_csv(out_file)
            self.assertEqual(len(loaded), 1)

    def test_write_fetch_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_log = Path(tmpdir) / "fetch_log.csv"
            records = [{
                "row": 1,
                "raw": "155",
                "tmdb_id": 155,
                "disposition": "FETCHED",
                "reason": "",
                "details_status": "ok",
                "credits_status": "ok",
                "title": "The Dark Knight",
                "release_date": "2008-07-16",
            }]
            write_fetch_log(records, out_log)
            self.assertTrue(out_log.exists())
            loaded = pd.read_csv(out_log)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded.iloc[0]["tmdb_id"], 155)


if __name__ == "__main__":
    unittest.main()

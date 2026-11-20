"""
pipeline/config.py
------------------
Single source of truth for all pipeline configuration.

Every constant used by any pipeline module lives here.
To change a setting, change it here only — no other file needs editing.

Reproducibility note:
    External results depend on TMDb API state at the time of initial fetch.
    Cached raw JSON files in `data/raw/` serve as the immutable reproducibility
    anchor for all downstream transformation, quality gates, and offline runs.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR  = DATA_DIR / "raw"
OUT_DIR  = ROOT / "out"

# Input
ID_LIST = DATA_DIR / "id_list.csv"

# Generated outputs
FETCH_LOG        = DATA_DIR / "fetch_log.csv"
FLAT_MOVIES      = DATA_DIR / "movies.csv"
FLAT_CAST        = DATA_DIR / "cast.csv"
FLAT_CREW        = DATA_DIR / "crew.csv"
ANALYSIS_OUT     = OUT_DIR  / "analysis.csv"
SENSITIVITY_OUT  = OUT_DIR  / "sensitivity_report.csv"
MEMO_OUT         = OUT_DIR  / "memo.md"
PROFILING_OUT    = ROOT / "profiling"


def ensure_directories() -> None:
    """Explicitly create expected runtime directories (avoids side-effects on import)."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROFILING_OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# TMDb API
# ---------------------------------------------------------------------------
TMDB_BASE     = "https://api.themoviedb.org/3"
TMDB_LANGUAGE = "en-US"

# Rate limiting — free-tier TMDb allows ~40 req/s; stay well under it
REQUEST_GAP     = 0.25   # seconds between consecutive HTTP calls (≈ 4 req/s)
MAX_RETRIES     = 3      # attempts per endpoint before giving up
BACKOFF_BASE    = 2.0    # seconds; wait = BACKOFF_BASE ** attempt_number
REQUEST_TIMEOUT = 10     # seconds per request before raising


def get_api_key() -> str:
    """
    Read TMDB_API_KEY from ROOT/.env or process environment.
    Centralized single implementation to eliminate duplicated file parsing.
    """
    env_file = ROOT / ".env"
    if env_file.exists():
        with open(env_file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() == "TMDB_API_KEY":
                    return v.strip().strip('"').strip("'")
    return os.environ.get("TMDB_API_KEY", "")


# ---------------------------------------------------------------------------
# Source data expectations
# ---------------------------------------------------------------------------
# The brief states 127 identifiers. Any deviation is a data-quality finding
# to be recorded in the findings log — not a reason to crash.
EXPECTED_ID_COUNT = 127

# ---------------------------------------------------------------------------
# Analysis windows
# ---------------------------------------------------------------------------
CUTOFF_YEAR = 2000     # "2000-onward" window (Yaw in Finance's concern)

# ---------------------------------------------------------------------------
# Performance budget 
# ---------------------------------------------------------------------------
# The analysis stage must complete within this many seconds on the
# 127-title dataset. Adjoa will re-run on ~500 titles next year.
TIME_BUDGET_SECONDS = 60.0

# ---------------------------------------------------------------------------
# Fetch-log disposition labels
# ---------------------------------------------------------------------------
DISPOSITION_FETCHED      = "FETCHED"
DISPOSITION_INVALID      = "INVALID"
DISPOSITION_DUPLICATE    = "DUPLICATE"
DISPOSITION_FETCH_FAILED = "FETCH_FAILED"

ALL_DISPOSITIONS = {
    DISPOSITION_FETCHED,
    DISPOSITION_INVALID,
    DISPOSITION_DUPLICATE,
    DISPOSITION_FETCH_FAILED,
}

# ---------------------------------------------------------------------------
# Fetch-log CSV columns (schema contract)
# ---------------------------------------------------------------------------
FETCH_LOG_FIELDS = [
    "row",
    "raw",
    "tmdb_id",
    "disposition",
    "reason",
    "details_status",
    "credits_status",
    "title",
    "release_date",
]

# ---------------------------------------------------------------------------
# Required column contracts for curated tables (schema contracts)
# ---------------------------------------------------------------------------
MOVIES_SCHEMA = {
    "tmdb_id": "int64",
    "title": "string",
    "release_year": "int64",
    "budget": "float64",
    "revenue": "float64",
    "vote_average": "float64",
    "is_franchise": "bool",
}

CAST_SCHEMA_COLUMNS = {"tmdb_id", "person_id", "name", "cast_order"}
CREW_SCHEMA_COLUMNS = {"tmdb_id", "person_id", "name", "department", "job"}

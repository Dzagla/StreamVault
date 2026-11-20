"""
pipeline/config.py
------------------
Single source of truth for all pipeline configuration.

Every constant used by any pipeline module lives here.
To change a setting, change it here only — no other file needs editing.
"""

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
FETCH_LOG      = DATA_DIR / "fetch_log.csv"
FLAT_MOVIES    = DATA_DIR / "movies.csv"
FLAT_CAST      = DATA_DIR / "cast.csv"
FLAT_CREW      = DATA_DIR / "crew.csv"
ANALYSIS_OUT   = OUT_DIR  / "analysis.csv"
MEMO_OUT       = OUT_DIR  / "memo.md"
PROFILING_OUT  = ROOT / "profiling"

# Ensure key directories exist at import time
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# TMDb API
# ---------------------------------------------------------------------------
TMDB_BASE     = "https://api.themoviedb.org/3"
TMDB_LANGUAGE = "en-US"

# Rate limiting — free-tier TMDb allows ~40 req/s; stay well under it
REQUEST_GAP   = 0.25   # seconds between consecutive HTTP calls  (≈ 4 req/s)
MAX_RETRIES   = 3      # attempts per endpoint before giving up
BACKOFF_BASE  = 2.0    # seconds; wait = BACKOFF_BASE ** attempt_number
REQUEST_TIMEOUT = 10   # seconds per request before raising

# ---------------------------------------------------------------------------
# Source data expectations
# ---------------------------------------------------------------------------
# The brief states 127 identifiers. Any deviation is a data-quality finding
# to be recorded in the data diagnosis — not a reason to crash.
EXPECTED_ID_COUNT = 127

# ---------------------------------------------------------------------------
# Analysis windows
# ---------------------------------------------------------------------------
CUTOFF_YEAR = 2000     # "2000-onward" window  (Yaw in Finance's concern)

# ---------------------------------------------------------------------------
# Performance budget (LO4)
# ---------------------------------------------------------------------------
# The analysis stage must complete within this many seconds on the
# 127-title dataset.  Adjoa will re-run on ~500 titles next year.
TIME_BUDGET_SECONDS = 60.0

# ---------------------------------------------------------------------------
# Fetch-log disposition labels
# ---------------------------------------------------------------------------
DISPOSITION_FETCHED      = "FETCHED"
DISPOSITION_INVALID      = "INVALID"
DISPOSITION_DUPLICATE    = "DUPLICATE"
DISPOSITION_FETCH_FAILED = "FETCH_FAILED"

# ---------------------------------------------------------------------------
# Fetch-log CSV columns  (kept here so every module agrees on the schema)
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

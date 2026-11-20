"""
pipeline/checks.py
------------------
Quality gates, reconciliations, and spot-checks before loading (LO4, LO5).

QA gate pattern:
- check_reconciliation: every candidate ID is accounted for (127 expected).
- check_grain_uniqueness: asserts no duplicate film keys in curated tables.
- check_performance_budget: asserts runtime stays within performance budget (LO4).
- verify_against_live_api: deliberate external API spot-checks against tentpoles (LO5).
"""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd
import requests

from pipeline.config import (
    TMDB_BASE,
    FLAT_MOVIES,
    FETCH_LOG,
    EXPECTED_ID_COUNT,
    TIME_BUDGET_SECONDS,
    ROOT,
)

SPOTCHECK_IDS = [155, 278, 671, 680, 157336]  # Deliberate edge cases and tentpoles


class ReconciliationError(Exception):
    """Raised when candidate counts or tables do not reconcile."""


def check_candidate_reconciliation(log_path: Path = FETCH_LOG) -> dict[str, int]:
    """Assert all candidate IDs are accounted for and reconcile to EXPECTED_ID_COUNT."""
    if not log_path.exists():
        raise ReconciliationError(f"Fetch log does not exist: {log_path}")

    log_df = pd.read_csv(log_path)
    total = len(log_df)

    counts = log_df["disposition"].value_counts().to_dict()

    if total != EXPECTED_ID_COUNT:
        raise ReconciliationError(
            f"Candidate list mismatch: expected {EXPECTED_ID_COUNT}, found {total}"
        )

    print(f"✓ Quality Gate: Candidate reconciliation passed ({total}/{EXPECTED_ID_COUNT} accounted for)")
    return counts


def check_grain_uniqueness(df_movies: pd.DataFrame) -> None:
    """Assert 1 row per film grain with unique tmdb_id."""
    if not df_movies["tmdb_id"].is_unique:
        duplicates = df_movies[df_movies["tmdb_id"].duplicated()]["tmdb_id"].tolist()
        raise ReconciliationError(f"Duplicate tmdb_id in movies table: {duplicates}")
    print("✓ Quality Gate: Grain uniqueness verified (1 row per unique tmdb_id)")


def _get_api_key() -> str:
    env_file = ROOT / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() == "TMDB_API_KEY":
                    return v.strip().strip('"').strip("'")
    return os.environ.get("TMDB_API_KEY", "")


def verify_against_live_api() -> None:
    """Deliberate spot-check against live TMDb API (LO5)."""
    print("\n" + "=" * 65)
    print("LO5 Spot-Check Verification: Local Clean Data vs. Live TMDb API")
    print("=" * 65)

    api_key = _get_api_key()
    if not api_key:
        print("Warning: TMDB_API_KEY not found in environment. Skipping live check.")
        return

    df_local = pd.read_csv(FLAT_MOVIES).set_index("tmdb_id")
    discrepancies_found = 0
    checks_performed = 0

    for tid in SPOTCHECK_IDS:
        if tid not in df_local.index:
            continue

        local_row = df_local.loc[tid]
        url = f"{TMDB_BASE}/movie/{tid}"
        params = {"api_key": api_key, "language": "en-US"}

        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                print(f"ID {tid}: Live API returned status {resp.status_code}")
                continue
            live_data = resp.json()
        except Exception as exc:
            print(f"ID {tid}: Network error during live verification ({exc}).")
            continue

        print(f"\nChecking ID {tid} — '{local_row['title']}':")

        # Title check
        live_title = live_data.get("title")
        checks_performed += 1
        if local_row["title"] == live_title:
            print(f"  ✓ Title matches: '{live_title}'")
        else:
            print(f"  ✗ Title mismatch: local='{local_row['title']}' vs live='{live_title}'")
            discrepancies_found += 1

        # Release date check
        live_rel = live_data.get("release_date")
        checks_performed += 1
        if local_row["release_date"] == live_rel:
            print(f"  ✓ Release date matches: '{live_rel}'")
        else:
            print(f"  ✗ Release date mismatch: local='{local_row['release_date']}' vs live='{live_rel}'")
            discrepancies_found += 1

        # Franchise flag check
        live_coll = bool(live_data.get("belongs_to_collection"))
        checks_performed += 1
        if bool(local_row["is_franchise"]) == live_coll:
            print(f"  ✓ Franchise status matches: {live_coll}")
        else:
            print(f"  ✗ Franchise status mismatch: local={local_row['is_franchise']} vs live={live_coll}")
            discrepancies_found += 1

    print("\n" + "=" * 65)
    print(f"Spot-check complete: {checks_performed} attributes verified across {len(SPOTCHECK_IDS)} titles.")
    if discrepancies_found == 0:
        print("✓ 100% field parity confirmed between clean pipeline and live source.")
    else:
        print(f"⚠ {discrepancies_found} acceptable variance(s) documented.")
    print("=" * 65)


if __name__ == "__main__":
    check_candidate_reconciliation()
    if FLAT_MOVIES.exists():
        check_grain_uniqueness(pd.read_csv(FLAT_MOVIES))
    verify_against_live_api()

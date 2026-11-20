"""
pipeline/checks.py
------------------
Quality gates, grain verifications, reconciliations, and live API spot-checks (LO4, LO5).

QA gate pattern:
- check_candidate_reconciliation: every candidate ID is accounted for (127 expected),
  and sum of all recognized dispositions equals total count.
- check_table_grains: asserts no duplicate primary/composite keys in movies, cast, or crew.
- verify_against_live_api: deliberate external API spot-checks against tentpoles (LO5).
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import requests

from pipeline.config import (
    TMDB_BASE,
    FLAT_MOVIES,
    FLAT_CAST,
    FLAT_CREW,
    FETCH_LOG,
    EXPECTED_ID_COUNT,
    ALL_DISPOSITIONS,
    get_api_key,
)

SPOTCHECK_IDS = [155, 278, 671, 680, 157336]  # Deliberate edge cases and tentpoles


class ReconciliationError(Exception):
    """Raised when candidate counts or tabular grains fail QA gates."""


def check_candidate_reconciliation(log_path: Path = FETCH_LOG) -> dict[str, int]:
    """
    Assert all candidate IDs are accounted for, reconcile to EXPECTED_ID_COUNT,
    and verify that all recorded dispositions belong strictly to the schema contract.
    """
    if not log_path.exists():
        raise ReconciliationError(f"Fetch log does not exist: {log_path}")

    log_df = pd.read_csv(log_path)
    total = len(log_df)

    if total != EXPECTED_ID_COUNT:
        raise ReconciliationError(
            f"Candidate list mismatch: expected {EXPECTED_ID_COUNT}, found {total}"
        )

    counts = log_df["disposition"].value_counts().to_dict()

    # Verify that only valid dispositions exist
    unknown_dispositions = set(counts.keys()) - ALL_DISPOSITIONS
    if unknown_dispositions:
        raise ReconciliationError(
            f"Unknown disposition labels found in fetch log: {unknown_dispositions}"
        )

    # Verify that dispositions sum exactly to the total
    disposition_sum = sum(counts.values())
    if disposition_sum != total:
        raise ReconciliationError(
            f"Disposition sum mismatch: counts sum to {disposition_sum}, total rows is {total}"
        )

    print(f"✓ Quality Gate: Candidate reconciliation passed ({total}/{EXPECTED_ID_COUNT} accounted for)")
    return counts


def check_table_grains(
    df_movies: pd.DataFrame,
    df_cast: pd.DataFrame | None = None,
    df_crew: pd.DataFrame | None = None,
) -> None:
    """
    Verify tabular grains from ADR 001:
    - movies: unique `tmdb_id`
    - cast: unique composite key (`tmdb_id`, `person_id`, `cast_order`)
    - crew: unique composite key (`tmdb_id`, `person_id`, `department`, `job`)
    """
    # 1. Movies grain
    if not df_movies["tmdb_id"].is_unique:
        duplicates = df_movies[df_movies["tmdb_id"].duplicated()]["tmdb_id"].tolist()
        raise ReconciliationError(f"Duplicate tmdb_id in movies table: {duplicates}")
    print("✓ Quality Gate: Movies grain verified (unique tmdb_id)")

    # 2. Cast grain
    if df_cast is not None and not df_cast.empty:
        cast_key = ["tmdb_id", "person_id", "cast_order"]
        if df_cast.duplicated(subset=cast_key).any():
            dup_cast = df_cast[df_cast.duplicated(subset=cast_key)][cast_key].head(5).to_dict("records")
            raise ReconciliationError(f"Duplicate composite keys in cast table: {dup_cast}")
        print("✓ Quality Gate: Cast grain verified (unique tmdb_id + person_id + cast_order)")

    # 3. Crew grain
    if df_crew is not None and not df_crew.empty:
        crew_key = ["tmdb_id", "person_id", "department", "job"]
        if df_crew.duplicated(subset=crew_key).any():
            dup_crew = df_crew[df_crew.duplicated(subset=crew_key)][crew_key].head(5).to_dict("records")
            raise ReconciliationError(f"Duplicate composite keys in crew table: {dup_crew}")
        print("✓ Quality Gate: Crew grain verified (unique tmdb_id + person_id + department + job)")


# Backward compatibility and explicit alias
check_grain_uniqueness = check_table_grains


def verify_against_live_api() -> bool:
    """
    Deliberate spot-check against live TMDb API (LO5).
    Returns True if spot-checks completed, False if network was unreachable.
    Fails loudly on discrepancies rather than labeling them 'acceptable variances'.
    """
    print("\n" + "=" * 65)
    print("LO5 Spot-Check Verification: Local Clean Data vs. Live TMDb API")
    print("=" * 65)

    api_key = get_api_key()
    if not api_key:
        print("⚠ Live spot-check skipped: TMDB_API_KEY not configured in environment.")
        return False

    if not FLAT_MOVIES.exists():
        print(f"⚠ Live spot-check skipped: {FLAT_MOVIES} not found.")
        return False

    df_local = pd.read_csv(FLAT_MOVIES).set_index("tmdb_id")
    discrepancies_found = 0
    checks_performed = 0
    network_errors = 0

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
                network_errors += 1
                continue
            live_data = resp.json()
        except Exception as exc:
            print(f"ID {tid}: Network error during live verification ({exc}).")
            network_errors += 1
            continue

        print(f"\nChecking ID {tid} — '{local_row['title']}':")

        # Title check
        live_title = live_data.get("title")
        checks_performed += 1
        if local_row["title"] == live_title:
            print(f"  ✓ Title matches: '{live_title}'")
        else:
            print(f"  ✗ Discrepancy: local title='{local_row['title']}' vs live='{live_title}'")
            discrepancies_found += 1

        # Release date check
        live_rel = live_data.get("release_date")
        checks_performed += 1
        if local_row["release_date"] == live_rel:
            print(f"  ✓ Release date matches: '{live_rel}'")
        else:
            print(f"  ✗ Discrepancy: local release_date='{local_row['release_date']}' vs live='{live_rel}'")
            discrepancies_found += 1

        # Franchise flag check
        live_coll = bool(live_data.get("belongs_to_collection"))
        checks_performed += 1
        if bool(local_row["is_franchise"]) == live_coll:
            print(f"  ✓ Franchise status matches: {live_coll}")
        else:
            print(f"  ✗ Discrepancy: local franchise={local_row['is_franchise']} vs live={live_coll}")
            discrepancies_found += 1

    print("\n" + "=" * 65)
    if network_errors == len(SPOTCHECK_IDS):
        print("✗ Spot-check failed: Live API host was unreachable for all test titles.")
        print("=" * 65)
        return False

    print(f"Spot-check complete: {checks_performed} attributes checked across {len(SPOTCHECK_IDS)} titles.")
    if discrepancies_found == 0:
        print("✓ Field parity confirmed between clean pipeline and live source.")
    else:
        print(f"✗ Discrepancies detected: {discrepancies_found} field mismatch(es) found.")
    print("=" * 65)
    return discrepancies_found == 0


if __name__ == "__main__":
    check_candidate_reconciliation()
    if FLAT_MOVIES.exists():
        df_m = pd.read_csv(FLAT_MOVIES)
        df_c = pd.read_csv(FLAT_CAST) if FLAT_CAST.exists() else None
        df_w = pd.read_csv(FLAT_CREW) if FLAT_CREW.exists() else None
        check_table_grains(df_m, df_c, df_w)
    verify_against_live_api()

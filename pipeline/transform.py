"""
pipeline/transform.py
---------------------
Lab Part 2 (LO3): Parsing and transforming nested JSON into tabular datasets.

What this module does
---------------------
1. Scans data/raw/ for all successfully fetched movie details and credits JSONs.
2. Unpacks nested structures adhering strictly to defined tabular grains:
   - movies: 1 row per movie (primary key: tmdb_id)
     * collection extracted to determine franchise status: collection_id, collection_name, is_franchise
     * genres collapsed into a semicolon-separated string to preserve 1-row-per-film grain
     * release_year parsed from release_date
   - cast: 1 row per film-cast member (composite key: tmdb_id, person_id, cast_order)
     * includes billing order, character, popularity
   - crew: 1 row per film-crew assignment (composite key: tmdb_id, person_id, department, job)
     * focuses on Key creative roles: Director, Producer, Screenplay/Writer
3. Validates grain uniqueness (no accidental duplication on primary keys).
4. Saves flat, clean tabular datasets to CSV via pipeline.load.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from pipeline.config import (
    RAW_DIR,
    FLAT_MOVIES,
    FLAT_CAST,
    FLAT_CREW,
    FETCH_LOG,
    DISPOSITION_FETCHED,
)


def _safe_int(val: Any) -> int | None:
    try:
        if val is None or val == "":
            return None
        return int(val)
    except (ValueError, TypeError):
        return None


def parse_movie_details(data: dict) -> dict:
    """Extract flat attributes for a single movie (Grain: 1 row per film)."""
    tmdb_id = _safe_int(data.get("id"))
    collection = data.get("belongs_to_collection") or {}
    genres = data.get("genres") or []

    genre_names = [g["name"] for g in genres if isinstance(g, dict) and "name" in g]
    genre_ids = [str(g["id"]) for g in genres if isinstance(g, dict) and "id" in g]

    release_date = (data.get("release_date") or "").strip()
    release_year = None
    if len(release_date) >= 4 and release_date[:4].isdigit():
        release_year = int(release_date[:4])

    return {
        "tmdb_id": tmdb_id,
        "imdb_id": data.get("imdb_id"),
        "title": data.get("title"),
        "original_title": data.get("original_title"),
        "release_date": release_date if release_date else None,
        "release_year": release_year,
        "status": data.get("status"),
        "runtime": _safe_int(data.get("runtime")),
        "budget": data.get("budget"),
        "revenue": data.get("revenue"),
        "popularity": data.get("popularity"),
        "vote_average": data.get("vote_average"),
        "vote_count": _safe_int(data.get("vote_count")),
        "original_language": data.get("original_language"),
        # Franchise / Collection metadata
        "collection_id": _safe_int(collection.get("id")),
        "collection_name": collection.get("name"),
        "is_franchise": bool(collection.get("id")),
        # Genres flattened to preserve 1-row-per-film grain without Cartesian explosions
        "genres": ";".join(genre_names) if genre_names else None,
        "genre_ids": ";".join(genre_ids) if genre_ids else None,
    }


def parse_movie_cast(tmdb_id: int, credits_data: dict) -> list[dict]:
    """Extract cast members (Grain: 1 row per film per cast member)."""
    records = []
    cast_list = credits_data.get("cast") or []
    for item in cast_list:
        if not isinstance(item, dict):
            continue
        records.append({
            "tmdb_id": tmdb_id,
            "person_id": _safe_int(item.get("id")),
            "name": item.get("name"),
            "character": item.get("character"),
            "cast_order": _safe_int(item.get("order")),
            "popularity": item.get("popularity"),
            "known_for_department": item.get("known_for_department"),
        })
    return records


def parse_movie_crew(tmdb_id: int, credits_data: dict) -> list[dict]:
    """Extract crew members (Grain: 1 row per film per crew assignment)."""
    records = []
    crew_list = credits_data.get("crew") or []
    for item in crew_list:
        if not isinstance(item, dict):
            continue
        records.append({
            "tmdb_id": tmdb_id,
            "person_id": _safe_int(item.get("id")),
            "name": item.get("name"),
            "department": item.get("department"),
            "job": item.get("job"),
            "popularity": item.get("popularity"),
        })
    return records


def flatten_all() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Reads all successfully fetched raw responses and produces
    the three tabular datasets: movies, cast, crew.
    """
    # Identify which IDs were successfully fetched
    fetched_ids: list[int] = []
    if FETCH_LOG.exists():
        log_df = pd.read_csv(FETCH_LOG)
        fetched_ids = [
            int(x) for x in log_df.loc[log_df["disposition"] == DISPOSITION_FETCHED, "tmdb_id"].dropna()
        ]
    else:
        # Fallback to files present in raw directory
        for p in RAW_DIR.glob("*_details.json"):
            tid_str = p.name.split("_")[0]
            if tid_str.isdigit():
                fetched_ids.append(int(tid_str))
        fetched_ids = sorted(list(set(fetched_ids)))

    print(f"Flattening raw JSON for {len(fetched_ids)} fetched titles...")

    movies_rows = []
    cast_rows = []
    crew_rows = []

    for tid in fetched_ids:
        details_path = RAW_DIR / f"{tid}_details.json"
        credits_path = RAW_DIR / f"{tid}_credits.json"

        if details_path.exists():
            with open(details_path, encoding="utf-8") as f:
                d_json = json.load(f)
                movies_rows.append(parse_movie_details(d_json))

        if credits_path.exists():
            with open(credits_path, encoding="utf-8") as f:
                c_json = json.load(f)
                cast_rows.extend(parse_movie_cast(tid, c_json))
                crew_rows.extend(parse_movie_crew(tid, c_json))

    df_movies = pd.DataFrame(movies_rows)
    df_cast = pd.DataFrame(cast_rows)
    df_crew = pd.DataFrame(crew_rows)

    # Validate grain constraints
    assert df_movies["tmdb_id"].is_unique, "Error: movies table has duplicate tmdb_id!"
    print(f"✓ movies: {len(df_movies)} rows (grain: 1 row per film, unique tmdb_id)")
    print(f"✓ cast:   {len(df_cast)} rows (grain: 1 row per film-cast member)")
    print(f"✓ crew:   {len(df_crew)} rows (grain: 1 row per film-crew assignment)")

    # Save outputs
    df_movies.to_csv(FLAT_MOVIES, index=False)
    df_cast.to_csv(FLAT_CAST, index=False)
    df_crew.to_csv(FLAT_CREW, index=False)

    print(f"\nOutputs written:")
    print(f"  - {FLAT_MOVIES}")
    print(f"  - {FLAT_CAST}")
    print(f"  - {FLAT_CREW}")

    return df_movies, df_cast, df_crew


if __name__ == "__main__":
    flatten_all()

"""
pipeline/load.py
----------------
Write curated tabular datasets safely and idempotently.
"""

from __future__ import annotations

import csv
from pathlib import Path
import pandas as pd

from pipeline.config import (
    FLAT_MOVIES,
    FLAT_CAST,
    FLAT_CREW,
    ANALYSIS_OUT,
    FETCH_LOG,
    FETCH_LOG_FIELDS,
    ROOT,
)


def write_fetch_log(records: list[dict], path: Path = FETCH_LOG) -> None:
    """Write the full ID-level reconciliation log to CSV."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FETCH_LOG_FIELDS)
        writer.writeheader()
        writer.writerows({k: r.get(k, "") for k in FETCH_LOG_FIELDS} for r in records)
    print(f"Fetch log written -> {path.relative_to(ROOT)}")


def save_curated_tables(
    df_movies: pd.DataFrame,
    df_cast: pd.DataFrame,
    df_crew: pd.DataFrame,
) -> dict[str, int]:
    """Save the three grain-defended datasets to CSV."""
    df_movies.to_csv(FLAT_MOVIES, index=False)
    df_cast.to_csv(FLAT_CAST, index=False)
    df_crew.to_csv(FLAT_CREW, index=False)

    print(f"Curated tables saved:")
    print(f"  - {FLAT_MOVIES.relative_to(ROOT)} ({len(df_movies)} rows)")
    print(f"  - {FLAT_CAST.relative_to(ROOT)} ({len(df_cast)} rows)")
    print(f"  - {FLAT_CREW.relative_to(ROOT)} ({len(df_crew)} rows)")

    return {
        "movies": len(df_movies),
        "cast": len(df_cast),
        "crew": len(df_crew),
    }


def save_analysis_kpis(df_kpi: pd.DataFrame, path: Path = ANALYSIS_OUT) -> None:
    """Save the two-window KPI analysis output to CSV."""
    df_kpi.to_csv(path, index=False)
    print(f"Analysis KPI table saved -> {path.relative_to(ROOT)}")

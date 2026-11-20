"""
pipeline/load.py
----------------
Write curated tabular datasets safely, atomically, and idempotently.
Modeled on Lecture 2 pipeline/load.py.

Guarantees:
1. Schema contract enforcement: asserts expected columns exist before saving.
2. Atomic writes: data is written to a unique temporary file first, then swapped
   into place via os.replace so readers never see half-written files.
"""

from __future__ import annotations

import csv
import os
import uuid
from pathlib import Path
import pandas as pd

from pipeline.config import (
    FLAT_MOVIES,
    FLAT_CAST,
    FLAT_CREW,
    ANALYSIS_OUT,
    FETCH_LOG,
    FETCH_LOG_FIELDS,
    MOVIES_SCHEMA,
    CAST_SCHEMA_COLUMNS,
    CREW_SCHEMA_COLUMNS,
    ROOT,
)


class SchemaContractError(Exception):
    """Raised when a dataset violates its defined schema contract before saving."""


def _rel_path(p: Path) -> Path:
    try:
        return p.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return p


def _atomic_write_csv(df: pd.DataFrame, target_path: Path) -> None:
    """Write DataFrame to a temporary file first, then atomically replace target."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.parent / f".{target_path.stem}.{uuid.uuid4().hex}.tmp.csv"
    try:
        df.to_csv(tmp_path, index=False)
        os.replace(tmp_path, target_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _validate_table_contracts(
    df_movies: pd.DataFrame,
    df_cast: pd.DataFrame,
    df_crew: pd.DataFrame,
) -> None:
    """Enforce schema contracts before writing to disk."""
    # Movies contract
    missing_movies_cols = set(MOVIES_SCHEMA.keys()) - set(df_movies.columns)
    if missing_movies_cols:
        raise SchemaContractError(f"movies table missing required columns: {missing_movies_cols}")

    # Cast contract
    missing_cast_cols = CAST_SCHEMA_COLUMNS - set(df_cast.columns)
    if missing_cast_cols:
        raise SchemaContractError(f"cast table missing required columns: {missing_cast_cols}")

    # Crew contract
    missing_crew_cols = CREW_SCHEMA_COLUMNS - set(df_crew.columns)
    if missing_crew_cols:
        raise SchemaContractError(f"crew table missing required columns: {missing_crew_cols}")


def write_fetch_log(records: list[dict], path: Path = FETCH_LOG) -> None:
    """Write the full ID-level reconciliation log to CSV atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f".{path.stem}.{uuid.uuid4().hex}.tmp.csv"
    try:
        with open(tmp_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=FETCH_LOG_FIELDS)
            writer.writeheader()
            writer.writerows({k: r.get(k, "") for k in FETCH_LOG_FIELDS} for r in records)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    print(f"Fetch log written -> {_rel_path(path)}")


def save_curated_tables(
    df_movies: pd.DataFrame,
    df_cast: pd.DataFrame,
    df_crew: pd.DataFrame,
) -> dict[str, int]:
    """Validate schema and save the three grain-defended datasets to CSV atomically."""
    _validate_table_contracts(df_movies, df_cast, df_crew)

    _atomic_write_csv(df_movies, FLAT_MOVIES)
    _atomic_write_csv(df_cast, FLAT_CAST)
    _atomic_write_csv(df_crew, FLAT_CREW)

    print(f"Curated tables saved atomically:")
    print(f"  - {_rel_path(FLAT_MOVIES)} ({len(df_movies)} rows)")
    print(f"  - {_rel_path(FLAT_CAST)} ({len(df_cast)} rows)")
    print(f"  - {_rel_path(FLAT_CREW)} ({len(df_crew)} rows)")

    return {
        "movies": len(df_movies),
        "cast": len(df_cast),
        "crew": len(df_crew),
    }


def save_analysis_kpis(df_kpi: pd.DataFrame, path: Path = ANALYSIS_OUT) -> None:
    """Save the two-window KPI analysis output to CSV atomically."""
    _atomic_write_csv(df_kpi, path)
    print(f"Analysis KPI table saved -> {_rel_path(path)}")

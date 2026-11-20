"""
pipeline/validate.py
--------------------
Validate candidate identifiers and split them into valid and quarantined items.

Each rejected row receives a human-readable reason so catalog curators
can fix the right problem at source.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.config import (
    ID_LIST,
    DISPOSITION_FETCHED,
    DISPOSITION_INVALID as INVALID,
    DISPOSITION_DUPLICATE as DUPLICATE,
)


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    tmdb_id: int | None
    reason: str


def validate_id(raw: str) -> ValidationResult:
    """
    Validate a single candidate ID string.
    Valid: positive integer.
    Invalid: empty row, non-positive number, or non-numeric string (e.g. 'tt0468569', 'N/A').
    """
    raw = raw.strip()
    if not raw:
        return ValidationResult(False, None, "EMPTY_ROW (blank line in source file)")
    try:
        val = int(raw)
    except ValueError:
        return ValidationResult(False, None, f"NOT_AN_INTEGER ({raw!r})")
    if val <= 0:
        return ValidationResult(False, None, f"NON_POSITIVE ({raw!r})")
    return ValidationResult(True, val, "")


def validate_candidates(path: Path = ID_LIST) -> list[dict[str, Any]]:
    """
    Read candidate list file and validate each row.
    Detects syntactically invalid rows and duplicates.
    """
    records: list[dict[str, Any]] = []
    seen: dict[int, int] = {}  # tmdb_id -> first row number seen

    with open(path, newline="", encoding="utf-8") as fh:
        raw_lines = fh.read().splitlines()

    # Skip header row (index 0)
    data_lines = raw_lines[1:]

    for row_num, line in enumerate(data_lines, start=1):
        raw = line.strip()

        if not raw:
            records.append({
                "row": row_num,
                "raw": "",
                "tmdb_id": None,
                "disposition": INVALID,
                "reason": "EMPTY_ROW (blank line in source file)",
                "details_status": "",
                "credits_status": "",
                "title": "",
                "release_date": "",
            })
            continue

        res = validate_id(raw)
        if not res.is_valid:
            disposition = INVALID
            reason = res.reason
            tid = None
        elif res.tmdb_id in seen:
            disposition = DUPLICATE
            reason = f"duplicate of row {seen[res.tmdb_id]}"
            tid = res.tmdb_id
        else:
            seen[res.tmdb_id] = row_num
            disposition = ""  # valid candidate for extraction
            reason = ""
            tid = res.tmdb_id

        records.append({
            "row": row_num,
            "raw": raw,
            "tmdb_id": tid,
            "disposition": disposition,
            "reason": reason,
            "details_status": "",
            "credits_status": "",
            "title": "",
            "release_date": "",
        })

    return records

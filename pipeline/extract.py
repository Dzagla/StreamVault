"""
pipeline/extract.py
-------------------
Lab Part 1: Acquire raw data for all 127 TMDb candidates.

What this module does
---------------------
1. Loads the candidate ID list from data/id_list.csv via pipeline.validate.
2. Validates each ID, recording every fault before any network call.
3. Fetches GET /movie/{id} and GET /movie/{id}/credits for every
   valid, deduplicated ID, with retries and exponential back-off.
4. Saves each raw JSON response to data/raw/ so the rest of the
   pipeline never needs to touch the network again.
5. Writes data/fetch_log.csv — a full account of where every one
   of the 127 IDs went, required by the data-diagnosis deliverable.

Usage
-----
    python -m pipeline.extract          # from project root
    python -m pipeline.extract --force  # re-fetch everything
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path
from typing import Literal

import requests

from pipeline.config import (
    ROOT,
    RAW_DIR,
    ID_LIST,
    FETCH_LOG,
    FETCH_LOG_FIELDS,
    TMDB_BASE,
    TMDB_LANGUAGE,
    REQUEST_GAP,
    MAX_RETRIES,
    BACKOFF_BASE,
    REQUEST_TIMEOUT,
    DISPOSITION_FETCHED      as FETCHED,
    DISPOSITION_INVALID      as INVALID,
    DISPOSITION_DUPLICATE    as DUPLICATE,
    DISPOSITION_FETCH_FAILED as FETCH_FAILED,
    EXPECTED_ID_COUNT,
)


# ---------------------------------------------------------------------------
# 1. Load and validate IDs
# ---------------------------------------------------------------------------

def _load_api_key() -> str:
    """Read TMDB_API_KEY from .env or the process environment."""
    env_file = ROOT / ".env"
    if env_file.exists():
        with open(env_file) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() == "TMDB_API_KEY":
                    return v.strip().strip('"').strip("'")
    key = os.environ.get("TMDB_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "TMDB_API_KEY not found. Add it to .env or set the environment variable."
        )
    return key


def _validate_id(raw: str) -> tuple[int | None, str]:
    """
    Return (tmdb_int, reason) where tmdb_int is None when the ID is invalid.

    Valid: a positive integer.
    Invalid: empty string, negative number, non-numeric string (e.g. 'tt0468569',
             'N/A'), or zero.
    """
    raw = raw.strip()
    if not raw:
        return None, "EMPTY_ROW"
    try:
        value = int(raw)
    except ValueError:
        return None, f"NOT_AN_INTEGER ({raw!r})"
    if value <= 0:
        return None, f"NON_POSITIVE ({raw!r})"
    return value, ""


def load_candidate_ids(path: Path) -> list[dict]:
    """
    Read id_list.csv and return one record per row with keys:
        row          – 1-based line number (excluding header)
        raw          – original string from the file
        tmdb_id      – integer if valid, else None
        disposition  – INVALID | DUPLICATE | (empty = candidate for fetch)
        reason       – human-readable note (populated for INVALID/DUPLICATE)

    Note: csv.DictReader silently skips completely blank lines.
    We read the raw lines first so every line — including blanks — gets a
    record, which keeps the total reconcilable against the brief's stated count.
    """
    records: list[dict] = []
    seen: dict[int, int] = {}   # tmdb_id → first row number

    # Read all lines (skip header) so blank rows are not lost
    with open(path, newline="", encoding="utf-8") as fh:
        raw_lines = fh.read().splitlines()

    # raw_lines[0] is the header; data starts at index 1
    data_lines = raw_lines[1:]

    for row_num, line in enumerate(data_lines, start=1):
        raw = line.strip()

        if not raw:
            # Completely blank line — record it as INVALID/EMPTY_ROW
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

        tmdb_id, reason = _validate_id(raw)

        if tmdb_id is None:
            disposition = INVALID
        elif tmdb_id in seen:
            disposition = DUPLICATE
            reason = f"duplicate of row {seen[tmdb_id]}"
        else:
            seen[tmdb_id] = row_num
            disposition = ""   # candidate — fetch later

        records.append(
            {
                "row": row_num,
                "raw": raw,
                "tmdb_id": tmdb_id,
                "disposition": disposition,
                "reason": reason,
                "details_status": "",
                "credits_status": "",
                "title": "",
                "release_date": "",
            }
        )

    return records


# ---------------------------------------------------------------------------
# 2. Network helpers
# ---------------------------------------------------------------------------

def _get_with_retry(
    url: str,
    params: dict,
    *,
    session: requests.Session,
) -> tuple[dict | None, Literal["ok", "not_found", "failed"]]:
    """
    GET *url* with up to MAX_RETRIES attempts and exponential back-off.

    Returns (data_dict, status) where status is:
        'ok'        – 200 response, data_dict is the parsed JSON
        'not_found' – 404 response (ID doesn't exist in TMDb)
        'failed'    – all retries exhausted
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp.json(), "ok"
            if resp.status_code == 404:
                return None, "not_found"
            # Rate limit or server error — back off
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", BACKOFF_BASE ** attempt))
                print(f"    Rate limited. Waiting {retry_after}s …")
                time.sleep(retry_after)
            else:
                wait = BACKOFF_BASE ** attempt
                print(f"    HTTP {resp.status_code}. Retrying in {wait:.0f}s (attempt {attempt}/{MAX_RETRIES}) …")
                time.sleep(wait)
        except requests.exceptions.RequestException as exc:
            wait = BACKOFF_BASE ** attempt
            print(f"    Request error: {exc}. Retrying in {wait:.0f}s (attempt {attempt}/{MAX_RETRIES}) …")
            time.sleep(wait)

    return None, "failed"


# ---------------------------------------------------------------------------
# 3. Fetch loop
# ---------------------------------------------------------------------------

def fetch_all(records: list[dict], api_key: str, *, force: bool = False) -> list[dict]:
    """
    For every record with no disposition (i.e. a valid, non-duplicate ID),
    fetch both TMDb endpoints and save the raw JSON to data/raw/.

    Skips IDs whose raw files already exist unless *force* is True.
    Updates each record in place with disposition, reason, and status fields.
    Returns the same list for chaining.
    """
    candidates = [r for r in records if r["disposition"] == ""]
    total = len(candidates)
    print(f"\nFetching {total} unique valid IDs ({len(records) - total} skipped: "
          f"invalid or duplicate)\n")

    params_base = {"api_key": api_key, "language": TMDB_LANGUAGE}

    with requests.Session() as session:
        for idx, rec in enumerate(candidates, start=1):
            tid = rec["tmdb_id"]
            details_file = RAW_DIR / f"{tid}_details.json"
            credits_file = RAW_DIR / f"{tid}_credits.json"

            already_have_details = details_file.exists() and not force
            already_have_credits = credits_file.exists() and not force

            print(f"[{idx:>3}/{total}] ID {tid}", end="")

            # ---- details endpoint ----------------------------------------
            if already_have_details:
                print(f"  details=cached", end="")
                rec["details_status"] = "cached"
                with open(details_file, encoding="utf-8") as fh:
                    details_data = json.load(fh)
                rec["title"] = details_data.get("title", "")
                rec["release_date"] = details_data.get("release_date", "")
            else:
                url = f"{TMDB_BASE}/movie/{tid}"
                data, status = _get_with_retry(url, params_base, session=session)
                time.sleep(REQUEST_GAP)

                if status == "ok":
                    details_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    rec["details_status"] = "ok"
                    rec["title"] = data.get("title", "")
                    rec["release_date"] = data.get("release_date", "")
                    print(f"  details=ok", end="")
                elif status == "not_found":
                    rec["details_status"] = "not_found"
                    print(f"  details=404", end="")
                else:
                    rec["details_status"] = "failed"
                    print(f"  details=FAILED", end="")

            # ---- credits endpoint ----------------------------------------
            if already_have_credits:
                print(f"  credits=cached", end="")
                rec["credits_status"] = "cached"
            else:
                url = f"{TMDB_BASE}/movie/{tid}/credits"
                data, status = _get_with_retry(url, params_base, session=session)
                time.sleep(REQUEST_GAP)

                if status == "ok":
                    credits_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    rec["credits_status"] = "ok"
                    print(f"  credits=ok", end="")
                elif status == "not_found":
                    rec["credits_status"] = "not_found"
                    print(f"  credits=404", end="")
                else:
                    rec["credits_status"] = "failed"
                    print(f"  credits=FAILED", end="")

            # ---- resolve final disposition --------------------------------
            if rec["disposition"] == "":   # still a candidate
                details_ok = rec["details_status"] in ("ok", "cached")
                credits_ok = rec["credits_status"] in ("ok", "cached")

                if details_ok and credits_ok:
                    rec["disposition"] = FETCHED
                elif rec["details_status"] == "not_found":
                    rec["disposition"] = FETCH_FAILED
                    rec["reason"] = "ID not found in TMDb (details 404)"
                elif rec["credits_status"] == "not_found":
                    rec["disposition"] = FETCHED   # usable without credits
                    rec["reason"] = "credits 404 — no cast/crew data"
                else:
                    rec["disposition"] = FETCH_FAILED
                    rec["reason"] = (
                        f"details={rec['details_status']} "
                        f"credits={rec['credits_status']}"
                    )

            print(f"  → {rec['disposition']}")

    return records


# ---------------------------------------------------------------------------
# 4. Write fetch log
# ---------------------------------------------------------------------------

def write_fetch_log(records: list[dict], path: Path = FETCH_LOG) -> None:
    """Write the full ID-level fetch log to CSV."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FETCH_LOG_FIELDS)
        writer.writeheader()
        writer.writerows({k: r.get(k, "") for k in FETCH_LOG_FIELDS} for r in records)
    print(f"\nFetch log written → {path.relative_to(ROOT)}")


def print_summary(records: list[dict]) -> None:
    """Print a reconciliation table: dispositions must sum to len(records)."""
    from collections import Counter
    counts = Counter(r["disposition"] for r in records)
    total = len(records)

    print("\n" + "=" * 45)
    print(f"Fetch summary (expected {EXPECTED_ID_COUNT} IDs)")
    print("=" * 45)
    for label in [FETCHED, INVALID, DUPLICATE, FETCH_FAILED, ""]:
        n = counts.get(label, 0)
        display = label if label else "PENDING"
        print(f"  {display:<15} {n:>4}")
    print("  " + "-" * 20)
    print(f"  {'TOTAL':<15} {total:>4}")

    if total == EXPECTED_ID_COUNT:
        print(f"\n✓ Total reconciles to {EXPECTED_ID_COUNT}")
    else:
        gap = EXPECTED_ID_COUNT - total
        print(
            f"\n⚠ DATA QUALITY FINDING: expected {EXPECTED_ID_COUNT} IDs, "
            f"found {total} readable rows (gap = {gap})."
        )
        print(
            "  Likely cause: blank or unparseable lines in id_list.csv "
            "that csv.DictReader silently skipped."
        )
        print("  Record this in your data diagnosis — it must be explained.")


# ---------------------------------------------------------------------------
# 5. Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch raw TMDb data for all candidates.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch even if raw JSON files already exist.",
    )
    args = parser.parse_args()

    print("Loading API key …")
    api_key = _load_api_key()
    print(f"API key loaded ({api_key[:4]}{'*' * (len(api_key) - 4)})\n")

    print(f"Reading candidate list from {ID_LIST.relative_to(ROOT)} …")
    records = load_candidate_ids(ID_LIST)

    records = fetch_all(records, api_key, force=args.force)
    print_summary(records)
    write_fetch_log(records, FETCH_LOG)


if __name__ == "__main__":
    main()

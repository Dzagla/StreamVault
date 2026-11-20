"""
check_setup.py
--------------
Environment and API connectivity verification for StreamVault Licensing Analysis.

Verifies:
  1. Python, pandas, and NumPy meet minimum version requirements.
  2. DataFrame construction and dtypes print correctly (Learning Path smoke test).
  3. TMDB_API_KEY is present in .env and can reach the live TMDb API.

Usage:
    python check_setup.py
"""

from __future__ import annotations

import sys
import pandas as pd
import numpy as np
import requests

from pipeline.config import get_api_key, TMDB_BASE


def verify_versions() -> None:
    """Ensure runtime libraries meet project requirements."""
    print("=" * 60)
    print("StreamVault DE02 — Environment Verification")
    print("=" * 60)

    major, minor = sys.version_info[:2]
    assert (major, minor) >= (3, 11), f"Python 3.11+ required, found {major}.{minor}"
    print(f"✓ Python  : {sys.version.split()[0]}")

    pd_major = int(pd.__version__.split(".")[0])
    assert pd_major >= 2, f"pandas 2+ required, found {pd.__version__}"
    print(f"✓ pandas  : {pd.__version__}")

    np_major = int(np.__version__.split(".")[0])
    assert np_major >= 1, f"NumPy 1+ required, found {np.__version__}"
    print(f"✓ NumPy   : {np.__version__}")
    print(f"✓ requests: {requests.__version__}")


def smoke_test_dataframe() -> None:
    """Smoke test DataFrame construction and dtype resolution."""
    print("\n--- DataFrame Smoke Test ---")
    df = pd.DataFrame({
        "tmdb_id": [603, 680, 278],
        "title": ["The Matrix", "Pulp Fiction", "The Shawshank Redemption"],
        "year": [1999, 1994, 1994],
    })
    print(df.to_string(index=False))
    print(f"Dtypes:\n{df.dtypes}")
    print("✓ DataFrame smoke test passed.")


def check_api_connectivity() -> None:
    """Verify TMDb API key configuration and live endpoint reachability."""
    print("\n--- TMDb API Key & Connectivity ---")
    api_key = get_api_key()

    if not api_key:
        print("✗ TMDB_API_KEY not found in .env — create .env before running live fetches.")
        return

    # Fixed-width mask that avoids leaking key length or token characters
    print("✓ TMDB_API_KEY found in .env ([PROTECTED_KEY_CONFIGURED])")

    url = f"{TMDB_BASE}/movie/603"
    params = {"api_key": api_key, "language": "en-US"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print(f"✓ Live TMDb ping successful (HTTP {resp.status_code})")
        print(f"  Title: {data.get('title')} ({data.get('release_date', '')[:4]})")
        print(f"  Vote Average: {data.get('vote_average')}/10")
    except requests.exceptions.ConnectionError:
        print("✗ Network connection error — internet access required for live extraction.")
    except requests.exceptions.HTTPError as exc:
        print(f"✗ HTTP error {exc.response.status_code} — verify API key validity.")
    except Exception as exc:
        print(f"✗ Ping failed: {exc}")


def main() -> None:
    verify_versions()
    smoke_test_dataframe()
    check_api_connectivity()
    print("\n" + "=" * 60)
    print("Environment check completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()

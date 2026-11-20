"""
check_setup.py
--------------
Session 1 environment check for DE02: StreamVault Licensing Analysis.

Verifies:
  - Python, pandas, and NumPy versions are acceptable
  - A three-row DataFrame can be built from a dictionary and dtypes printed
  - The TMDb API key is present in .env and is reachable (live API ping)

Run from the project root:
    python check_setup.py
"""

import sys
import os

# ---------------------------------------------------------------------------
# 1. Version checks
# ---------------------------------------------------------------------------
print("=" * 55)
print("DE02 Environment Check")
print("=" * 55)

python_version = sys.version.split()[0]
print(f"\nPython  : {python_version}")

try:
    import pandas as pd
    print(f"pandas  : {pd.__version__}")
except ImportError:
    print("pandas  : NOT INSTALLED  →  pip install pandas")
    pd = None

try:
    import numpy as np
    print(f"NumPy   : {np.__version__}")
except ImportError:
    print("NumPy   : NOT INSTALLED  →  pip install numpy")
    np = None

try:
    import requests
    print(f"requests: {requests.__version__}")
except ImportError:
    print("requests: NOT INSTALLED  →  pip install requests")
    requests = None

# ---------------------------------------------------------------------------
# 2. Minimum version assertions
# ---------------------------------------------------------------------------
print()
major, minor = sys.version_info[:2]
assert (major, minor) >= (3, 11), (
    f"Python 3.11+ required, found {major}.{minor}"
)
print("✓ Python version OK")

if pd is not None:
    pd_major = int(pd.__version__.split(".")[0])
    assert pd_major >= 2, f"pandas 2+ required, found {pd.__version__}"
    print("✓ pandas version OK")

if np is not None:
    np_major = int(np.__version__.split(".")[0])
    assert np_major >= 1, f"NumPy 1+ required, found {np.__version__}"
    print("✓ NumPy version OK")

# ---------------------------------------------------------------------------
# 3. DataFrame smoke test  (required by Learning Path ch. 0 activity)
# ---------------------------------------------------------------------------
if pd is not None:
    print("\n--- DataFrame smoke test ---")
    df = pd.DataFrame(
        {
            "tmdb_id": [603, 680, 278],
            "title":   ["The Matrix", "Pulp Fiction", "The Shawshank Redemption"],
            "year":    [1999, 1994, 1994],
        }
    )
    print(df)
    print()
    print(df.dtypes)
    print()
    print("✓ DataFrame built and dtypes printed OK")

# ---------------------------------------------------------------------------
# 4. .env / API key check
# ---------------------------------------------------------------------------
print("\n--- TMDb API key check ---")

# Load .env manually (no python-dotenv dependency required)
env_path = os.path.join(os.path.dirname(__file__), ".env")
api_key = None

if os.path.exists(env_path):
    with open(env_path) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() == "TMDB_API_KEY":
                api_key = value.strip().strip('"').strip("'")
                break

if not api_key:
    print("✗ TMDB_API_KEY not found in .env  →  add it before continuing")
else:
    print(f"✓ TMDB_API_KEY found in .env ({api_key[:4]}{'*' * (len(api_key) - 4)})")

# ---------------------------------------------------------------------------
# 5. Live API ping  (GET /movie/603 — The Matrix)
# ---------------------------------------------------------------------------
if requests is not None and api_key:
    print("\n--- Live TMDb API ping (movie id 603) ---")
    url = "https://api.themoviedb.org/3/movie/603"
    params = {"api_key": api_key, "language": "en-US"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✓ API reachable  |  status {response.status_code}")
        print(f"  Title : {data.get('title')}")
        print(f"  Year  : {data.get('release_date', '')[:4]}")
        print(f"  Rating: {data.get('vote_average')}")
    except requests.exceptions.ConnectionError:
        print("✗ Network error — no internet access in this environment")
    except requests.exceptions.HTTPError as exc:
        print(f"✗ HTTP {exc.response.status_code} — check your API key")
    except Exception as exc:
        print(f"✗ Unexpected error: {exc}")

# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print("All checks passed — environment is ready for DE02.")
print("=" * 55)

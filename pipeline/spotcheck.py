"""
pipeline/spotcheck.py
---------------------
Backward-compatibility alias for pipeline.checks.
"""

from pipeline.checks import *
from pipeline.checks import verify_against_live_api

if __name__ == "__main__":
    verify_against_live_api()

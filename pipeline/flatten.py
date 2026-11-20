"""
pipeline/flatten.py
-------------------
Backward-compatibility alias for pipeline.transform.
"""

from pipeline.transform import *
from pipeline.transform import flatten_all

if __name__ == "__main__":
    flatten_all()

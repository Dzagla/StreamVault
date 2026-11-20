"""
pipeline/fetch.py
-----------------
Backward-compatibility alias for pipeline.extract.
"""

from pipeline.extract import *
from pipeline.extract import main

if __name__ == "__main__":
    main()

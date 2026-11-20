"""
run_tests.py
------------
Run all unit and integration tests for the StreamVault pipeline.
Uses Python's standard unittest runner (zero external dependencies required),
and is also fully compatible with pytest.

Usage:
    python run_tests.py
    python -m unittest discover tests
    pytest
"""

import sys
import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

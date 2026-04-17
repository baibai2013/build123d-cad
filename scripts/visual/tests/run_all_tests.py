#!/usr/bin/env python3
"""Discover and run all tests under scripts/visual/tests/.
发现并运行 scripts/visual/tests/ 下所有 unittest。
"""
import unittest
import sys
from pathlib import Path

THIS_DIR = Path(__file__).parent

def main() -> int:
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(THIS_DIR), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())

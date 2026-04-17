#!/usr/bin/env python3
"""Discover and run all tests under scripts/visual/tests/.
发现并运行 scripts/visual/tests/ 下所有 unittest。
"""
import unittest
import sys
from pathlib import Path

THIS_DIR = Path(__file__).parent
SKILL_ROOT = THIS_DIR.parent.parent.parent  # scripts/visual/tests -> skill root
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

def main() -> int:
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(THIS_DIR), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELECT_SCRIPT = ROOT / "scripts" / "select_parts.py"
AVAILABILITY_SCRIPT = ROOT / "scripts" / "check_availability.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_availability_report_uses_offline_catalog() -> None:
    subprocess.run([sys.executable, str(SELECT_SCRIPT), str(EXAMPLE)], check=False)
    result = subprocess.run([sys.executable, str(AVAILABILITY_SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 0
    report = json.loads((EXAMPLE / "reports" / "availability_report.json").read_text(encoding="utf-8"))
    assert report["mode"] == "offline_curated_catalog"
    assert report["parts"]
    assert all("requires live stock verification" in warning for warning in report["warnings"])

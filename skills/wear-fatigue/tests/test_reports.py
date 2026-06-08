from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEAR_SCRIPT = ROOT / "scripts" / "estimate_wear.py"
FATIGUE_SCRIPT = ROOT / "scripts" / "estimate_fatigue.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_scripts_write_markdown_reports() -> None:
    subprocess.run([sys.executable, str(WEAR_SCRIPT), str(EXAMPLE)], check=False)
    subprocess.run([sys.executable, str(FATIGUE_SCRIPT), str(EXAMPLE)], check=False)
    maintenance = (EXAMPLE / "reports" / "maintenance_interval.md").read_text(encoding="utf-8")
    summary = (EXAMPLE / "reports" / "wear_fatigue_report.md").read_text(encoding="utf-8")
    assert "Estimated maintenance interval" in maintenance
    assert "Status: FAIL" in summary

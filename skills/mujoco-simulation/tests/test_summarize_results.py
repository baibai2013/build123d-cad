from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_SCRIPT = ROOT / "scripts" / "run_scenarios.py"
SUMMARY_SCRIPT = ROOT / "scripts" / "summarize_results.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_summarize_writes_markdown() -> None:
    subprocess.run([sys.executable, str(RUN_SCRIPT), str(EXAMPLE)], check=False)
    result = subprocess.run([sys.executable, str(SUMMARY_SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    text = (EXAMPLE / "reports" / "mujoco_validation_report.md").read_text(encoding="utf-8")
    assert "MuJoCo Validation Report" in text
    assert "metadata mode" in text

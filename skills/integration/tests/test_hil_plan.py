from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "write_hil_plan.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_hil_and_data_capture_docs_written() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    hil = (EXAMPLE / "reports" / "hil_plan.md").read_text(encoding="utf-8")
    capture = (EXAMPLE / "reports" / "data_capture_checklist.md").read_text(encoding="utf-8")
    assert "current-limited bench supply" in hil
    assert "controller_latency" in capture

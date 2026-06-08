from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "propose_parameter_update.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_parameter_update_written() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    text = (EXAMPLE / "reports" / "parameter_update.yaml").read_text(encoding="utf-8")
    assert "foot_friction_scale" in text
    assert "control_latency_ms_add" in text

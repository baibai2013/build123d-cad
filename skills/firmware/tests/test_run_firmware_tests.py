from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_firmware_tests.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_firmware_test_report_written() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    report = json.loads((EXAMPLE / "reports" / "firmware_test_report.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert report["checks"]["target_defined"] is True
    assert report["checks"]["calibration_contract_ok"] is False

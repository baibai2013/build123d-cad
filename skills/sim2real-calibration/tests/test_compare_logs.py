from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "compare_logs.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_example_blocks_large_sim_real_gap() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    report = json.loads((EXAMPLE / "reports" / "sim2real_calibration.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert any("speed error" in blocker for blocker in report["blockers"])
    assert any("latency error" in blocker for blocker in report["blockers"])


def test_safe_calibration_case_passes(tmp_path: Path) -> None:
    project = tmp_path / "safe_sim2real"
    project.mkdir()
    (project / "calibration_dataset.yaml").write_text(
        """
project: safe_sim2real
tolerances:
  speed_error_pct_max: 15
  slip_error_abs_max: 0.05
  torque_error_pct_max: 20
  posture_error_deg_max: 3
  latency_error_ms_max: 10
simulation:
  average_speed_mps: 0.5
  foot_slip_ratio: 0.08
  peak_joint_torque_nm: 5.0
  max_body_roll_deg: 5
  max_body_pitch_deg: 5
  controller_latency_ms: 8
real:
  average_speed_mps: 0.46
  foot_slip_ratio: 0.1
  peak_joint_torque_nm: 5.5
  max_body_roll_deg: 6
  max_body_pitch_deg: 6
  controller_latency_ms: 12
""".lstrip(),
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, str(SCRIPT), str(project)], check=False, text=True, capture_output=True)
    assert result.returncode == 0
    report = json.loads((project / "reports" / "sim2real_calibration.json").read_text(encoding="utf-8"))
    assert report["valid"] is True

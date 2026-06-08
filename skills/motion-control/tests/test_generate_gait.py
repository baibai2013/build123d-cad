from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_gait.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_generate_gait_writes_trajectory_and_controller() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    report = json.loads((EXAMPLE / "reports" / "motion_control_report.json").read_text(encoding="utf-8"))
    trajectory = json.loads((EXAMPLE / "control" / "trajectory.json").read_text(encoding="utf-8"))
    controller = (EXAMPLE / "control" / "controller_params.yaml").read_text(encoding="utf-8")
    assert report["summary"]["gait_type"] == "trot"
    assert len(trajectory["points"]) == 8
    assert "front_left_hip_pitch" in trajectory["points"][0]["positionsByNameDeg"]
    assert "control_rate_hz" in controller


def test_safe_gait_case_passes(tmp_path: Path) -> None:
    project = tmp_path / "safe_gait"
    project.mkdir()
    (project / "motion_plan.yaml").write_text(
        """
project: safe_gait
link_lengths:
  thigh_mm: 90
  shank_mm: 95
joint_limits_deg:
  hip_pitch_min: -120
  hip_pitch_max: 120
  knee_pitch_min: -170
  knee_pitch_max: 10
ik_targets:
  - name: stance
    leg: front_left
    x_mm: 45
    z_mm: -135
    required: true
gait:
  type: walk
  cycle_time_s: 0.8
  samples_per_cycle: 5
  stride_length_mm: 35
  swing_height_mm: 20
  body_height_mm: 135
  duty_factor: 0.6
  controller:
    mode: position
    control_rate_hz: 200
    kp: 20
    kd: 0.6
""".lstrip(),
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, str(SCRIPT), str(project)], check=False, text=True, capture_output=True)
    assert result.returncode == 0
    report = json.loads((project / "reports" / "motion_control_report.json").read_text(encoding="utf-8"))
    assert report["valid"] is True

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "solve_ik.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_example_ik_blocks_unreachable_target() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    report = json.loads((EXAMPLE / "reports" / "ik_report.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert any("exceeds reach" in blocker for blocker in report["blockers"])
    assert (EXAMPLE / "control" / "ik_solution.json").exists()


def test_safe_ik_case_passes(tmp_path: Path) -> None:
    project = tmp_path / "safe_motion"
    project.mkdir()
    (project / "motion_plan.yaml").write_text(
        """
project: safe_motion
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
  type: trot
  cycle_time_s: 0.6
  samples_per_cycle: 4
  stride_length_mm: 40
  swing_height_mm: 25
  body_height_mm: 135
  duty_factor: 0.55
""".lstrip(),
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, str(SCRIPT), str(project)], check=False, text=True, capture_output=True)
    assert result.returncode == 0
    report = json.loads((project / "reports" / "ik_report.json").read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["blockers"] == []

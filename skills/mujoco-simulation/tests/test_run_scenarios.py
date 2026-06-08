from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_scenarios.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_example_blocks_failed_walk_and_slope() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    report = json.loads((EXAMPLE / "reports" / "mujoco_result.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert report["summary"]["metadata_mode"] is True
    assert any("walk_flat fell" in blocker for blocker in report["blockers"])
    assert any("torque margin" in blocker for blocker in report["blockers"])
    assert (EXAMPLE / "simulation" / "mujoco" / "results" / "walk_flat.sim_result.json").exists()
    assert (EXAMPLE / "simulation" / "mujoco" / "trajectories" / "walk_flat.trajectory.json").exists()


def test_safe_scenario_set_passes(tmp_path: Path) -> None:
    project = tmp_path / "safe_mujoco"
    project.mkdir()
    (project / "mujoco_scenarios.yaml").write_text(
        """
project: safe_mujoco
backend: metadata
model:
  mjcf: simulation/mujoco/robot.xml
limits:
  stand_stable_seconds_min: 30
  max_body_roll_deg: 8
  max_body_pitch_deg: 8
  foot_slip_ratio_max: 0.12
  joint_torque_margin_pct_min: 20
  cost_of_transport_max: 2.5
  max_contact_penetration_mm: 3
scenarios:
  - name: stand
    type: stand
    required: true
    duration_s: 30
    stable_seconds: 30
    fell: false
    max_body_roll_deg: 2
    max_body_pitch_deg: 2
    foot_slip_ratio: 0.0
    joint_torque_margin_pct: 35
    max_contact_penetration_mm: 1
    cost_of_transport: 0
  - name: walk_flat
    type: walk_flat
    required: true
    duration_s: 10
    stable_seconds: 10
    fell: false
    max_body_roll_deg: 5
    max_body_pitch_deg: 4
    foot_slip_ratio: 0.05
    joint_torque_margin_pct: 25
    max_contact_penetration_mm: 1
    cost_of_transport: 2.0
""".lstrip(),
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, str(SCRIPT), str(project)], check=False, text=True, capture_output=True)
    assert result.returncode == 0
    report = json.loads((project / "reports" / "mujoco_result.json").read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["blockers"] == []

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "estimate_wear.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_example_wear_report_blocks_known_risks() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    report = json.loads((EXAMPLE / "reports" / "wear_report.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert any("contact stress" in blocker for blocker in report["blockers"])
    assert any("bend radius" in blocker for blocker in report["blockers"])
    assert any("missing vibration lock" in blocker for blocker in report["blockers"])


def test_safe_wear_case_passes(tmp_path: Path) -> None:
    project = tmp_path / "safe_wear"
    project.mkdir()
    (project / "wear_inputs.yaml").write_text(
        """
project: safe_wear
target_maintenance_hours: 50
gears:
  - name: knee_reducer
    contact_stress_mpa: 700
    allowable_contact_stress_mpa: 1100
    pitch_line_velocity_mps: 1.5
    lubrication: grease
    estimated_life_hours: 200
bearings:
foot_pads:
  - name: foot_pad
    estimated_wear_life_hours: 120
    impact_j: 2.0
    friction_coefficient: 0.7
    replaceable: true
joint_interfaces:
harnesses:
  - name: leg_harness
    min_bend_radius_mm: 35
    required_bend_radius_mm: 25
    motion_envelope_clear: true
    pinch_risk: false
connectors:
  - name: power_connector
    mating_cycles: 100
    mating_cycles_min: 50
    vibration_lock: true
    strain_relief: true
""".lstrip(),
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, str(SCRIPT), str(project)], check=False, text=True, capture_output=True)
    assert result.returncode == 0
    report = json.loads((project / "reports" / "wear_report.json").read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["blockers"] == []

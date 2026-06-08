from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_bringup_readiness.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_example_blocks_missing_human_approval() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    report = json.loads((EXAMPLE / "reports" / "integration_checklist.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert any("human first-power approval" in blocker for blocker in report["blockers"])


def test_safe_integration_plan_passes(tmp_path: Path) -> None:
    project = tmp_path / "safe_integration"
    project.mkdir()
    (project / "integration_plan.yaml").write_text(
        """
project: safe_integration
gates:
  digital_twin_passed: true
  manufacturing_pack_complete: true
  firmware_dry_run_passed: true
  assembly_inspection_passed: true
  human_first_power_approval: true
  human_motor_motion_approval: false
safety:
  emergency_stop_verified: true
  current_limited_supply_available: true
  fire_safe_test_area: true
  battery_disconnected_for_initial_checks: true
  exposed_power_contacts_guarded: true
testbench:
  requested_stage: first_power
  motor_motion_requested: false
  hil_controller_available: true
  telemetry_logger_available: true
  spare_fuses_available: true
data_capture:
  joint_states: true
  imu: true
  bus_voltage_current: true
  controller_latency: true
  fault_states: true
""".lstrip(),
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, str(SCRIPT), str(project)], check=False, text=True, capture_output=True)
    assert result.returncode == 0
    report = json.loads((project / "reports" / "integration_checklist.json").read_text(encoding="utf-8"))
    assert report["valid"] is True

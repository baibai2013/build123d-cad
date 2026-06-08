from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_project.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_example_blocks_safety_and_calibration_issues() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    report = json.loads((EXAMPLE / "reports" / "firmware_report.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert any("undervoltage cutoff" in blocker for blocker in report["blockers"])
    assert any("encoder offset calibration" in blocker for blocker in report["blockers"])
    assert (EXAMPLE / "firmware" / "project_manifest.json").exists()
    assert (EXAMPLE / "firmware" / "can_frames.md").exists()


def test_safe_firmware_plan_passes(tmp_path: Path) -> None:
    project = tmp_path / "safe_firmware"
    project.mkdir()
    (project / "firmware_plan.yaml").write_text(
        """
project: safe_firmware
target:
  mcu: STM32G431CBT6
  toolchain: platformio
  framework: stm32_hal
  clock_mhz: 170
  joint_count: 12
control_loop:
  mode: foc_position
  frequency_hz: 500
  frequency_min_hz: 250
  telemetry_hz: 100
  watchdog_ms: 20
bus:
  type: can_fd
  bitrate_kbps: 1000
  command_id_base: 512
  telemetry_id_base: 768
  estop_id: 256
  heartbeat_ms: 20
safety:
  emergency_stop: true
  undervoltage_cutoff_v: 21
  undervoltage_min_v: 20
  overcurrent_limit_a: 35
  thermal_shutdown_c: 75
  thermal_shutdown_max_c: 80
calibration:
  joint_zero_required: true
  encoder_offset_required: true
  captured_joint_zero: true
  captured_encoder_offset: true
""".lstrip(),
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, str(SCRIPT), str(project)], check=False, text=True, capture_output=True)
    assert result.returncode == 0
    report = json.loads((project / "reports" / "firmware_report.json").read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["blockers"] == []

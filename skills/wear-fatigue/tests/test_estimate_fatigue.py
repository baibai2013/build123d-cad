from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "estimate_fatigue.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_example_fatigue_report_blocks_known_risks() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    report = json.loads((EXAMPLE / "reports" / "fatigue_report.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert any("bearing L10 life" in blocker for blocker in report["blockers"])
    assert any("limit impact" in blocker for blocker in report["blockers"])
    assert any("screw loosening" in blocker for blocker in report["blockers"])


def test_safe_fatigue_case_passes(tmp_path: Path) -> None:
    project = tmp_path / "safe_fatigue"
    project.mkdir()
    (project / "wear_inputs.yaml").write_text(
        """
project: safe_fatigue
target_maintenance_hours: 50
gears:
bearings:
  - name: knee_bearing
    l10_life_hours: 200
    radial_load_n: 80
    radial_load_limit_n: 180
    axial_load_n: 10
    axial_load_limit_n: 60
    rpm: 180
    mounting_error_deg: 0.2
    mounting_error_deg_max: 1.0
foot_pads:
joint_interfaces:
  - name: knee_limit
    limit_impact_j: 2.0
    limit_impact_j_max: 5.0
    screw_loosening_risk: low
harnesses:
connectors:
""".lstrip(),
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, str(SCRIPT), str(project)], check=False, text=True, capture_output=True)
    assert result.returncode == 0
    report = json.loads((project / "reports" / "fatigue_report.json").read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["blockers"] == []

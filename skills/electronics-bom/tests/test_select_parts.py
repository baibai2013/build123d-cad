from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "select_parts.py"
EXAMPLE = ROOT / "examples" / "quadruped_mvp"


def test_example_bom_blocks_unmet_high_current_driver() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(EXAMPLE)], check=False, text=True, capture_output=True)
    assert result.returncode == 1
    report = json.loads((EXAMPLE / "reports" / "electronics_bom.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert any("motor_driver" in blocker for blocker in report["blockers"])
    assert any(part["category"] == "mcu" for part in report["selected_parts"])
    assert (EXAMPLE / "electrical" / "library" / "selected_parts.json").exists()


def test_safe_bom_request_passes(tmp_path: Path) -> None:
    project = tmp_path / "safe_bom"
    project.mkdir()
    (project / "bom_request.yaml").write_text(
        """
project: safe_bom
constraints:
  assembly_preference: jlcpcb_basic
  package_preference: smd
requirements:
  - category: mcu
    quantity: 1
    required: true
    interface: can
    min_gpio: 24
    package: lqfp
  - category: buck_regulator
    quantity: 2
    required: true
    min_voltage_v: 24
    min_current_a: 3
""".lstrip(),
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, str(SCRIPT), str(project)], check=False, text=True, capture_output=True)
    assert result.returncode == 0
    report = json.loads((project / "reports" / "electronics_bom.json").read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["blockers"] == []

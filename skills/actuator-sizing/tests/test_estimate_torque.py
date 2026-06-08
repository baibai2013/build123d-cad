from __future__ import annotations

import importlib.util
import json
import sys


def _load_module(subskill_root, script_name):
    path = subskill_root / "scripts" / script_name
    scripts_dir = str(path.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_example_estimate_writes_blocking_report(subskill_root, example_project_copy):
    estimate = _load_module(subskill_root, "estimate_torque.py")
    payload = estimate.run(example_project_copy)
    assert payload["valid"] is False
    assert payload["minimum_margin_pct"] < 20
    assert payload["blockers"]
    report = json.loads((example_project_copy / "reports" / "torque_margin.json").read_text(encoding="utf-8"))
    assert "knee" in report["joints"]
    assert (example_project_copy / "reports" / "actuator_spec.yaml").exists()


def test_stronger_actuator_passes(subskill_root, tmp_path):
    estimate = _load_module(subskill_root, "estimate_torque.py")
    (tmp_path / "requirements.yaml").write_text(
        'version: "1.0"\nproject:\n  name: pass_bot\ntargets:\n  mass_kg: 4\n  payload_kg: 0.2\n  runtime_min: 20\n  flat_walk_speed_mps: 0.3\n  max_slope_deg: 0\n',
        encoding="utf-8",
    )
    (tmp_path / "architecture.yaml").write_text(
        'version: "1.0"\nsystem:\n  name: pass_bot\n  legs: 4\n  stance_legs: 4\ngeometry:\n  femur_length_m: 0.08\n  tibia_length_m: 0.08\n  body_half_width_m: 0.07\n',
        encoding="utf-8",
    )
    (tmp_path / "actuator_candidate.yaml").write_text(
        "actuator:\n  name: strong\n  available_torque_nm: 8\n  continuous_torque_nm: 6\n  max_speed_rad_s: 20\n  gear_ratio: 12\n",
        encoding="utf-8",
    )
    payload = estimate.run(tmp_path)
    assert payload["valid"] is True
    assert payload["blockers"] == []

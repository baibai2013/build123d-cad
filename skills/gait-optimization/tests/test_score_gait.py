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


def test_example_writes_blocking_reports(subskill_root, example_project_copy):
    scorer = _load_module(subskill_root, "score_gait.py")
    payload = scorer.run(example_project_copy)
    assert payload["valid"] is False
    assert payload["blockers"]
    assert payload["best_candidate"]["name"] == "safer_trot"
    report = json.loads((example_project_copy / "reports" / "gait_score.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert report["best_candidate"]["valid"] is True
    assert (example_project_copy / "reports" / "best_gait_params.yaml").exists()
    assert (example_project_copy / "reports" / "trajectory.json").exists()


def test_stable_gait_passes(subskill_root, tmp_path):
    scorer = _load_module(subskill_root, "score_gait.py")
    (tmp_path / "gait_validation.yaml").write_text(
        'version: "1.0"\n'
        "target:\n"
        "  stand_stable_seconds: 30\n"
        "  average_speed_mps_min: 0.5\n"
        "  max_body_roll_deg: 8\n"
        "  max_body_pitch_deg: 8\n"
        "  foot_slip_ratio_max: 0.12\n"
        "  joint_torque_margin_pct_min: 20\n"
        "  cost_of_transport_max: 2.5\n"
        "gait_params:\n"
        "  name: stable_trot\n"
        "  stride_mm: 42\n"
        "  clearance_mm: 30\n"
        "  duty_factor: 0.58\n"
        "  body_height_mm: 120\n"
        "  phase_pattern: trot\n"
        "validation:\n"
        "  single_leg_ik_pass: true\n"
        "  phase_complete: true\n"
        "  stand_stable_seconds: 34\n"
        "  flat_walk_no_fall: true\n"
        "  max_body_roll_deg: 5\n"
        "  max_body_pitch_deg: 6\n"
        "  foot_slip_ratio: 0.07\n"
        "  joint_torque_margin_pct: 28\n"
        "  average_speed_mps: 0.52\n"
        "  cost_of_transport: 2.1\n",
        encoding="utf-8",
    )
    payload = scorer.run(tmp_path)
    assert payload["valid"] is True
    assert payload["blockers"] == []
    assert payload["score"] == 100

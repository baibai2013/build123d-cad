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
    runner = _load_module(subskill_root, "run_static_case.py")
    payload = runner.run(example_project_copy)
    assert payload["valid"] is False
    assert payload["blockers"]
    report = json.loads((example_project_copy / "reports" / "fea_report.json").read_text(encoding="utf-8"))
    assert report["summary"]["case_count"] == 2
    assert report["summary"]["worst_safety_factor"] < 2
    assert (example_project_copy / "reports" / "static_case_report.json").exists()


def test_strong_case_passes(subskill_root, tmp_path):
    runner = _load_module(subskill_root, "run_static_case.py")
    (tmp_path / "fea_cases.yaml").write_text(
        'version: "1.0"\n'
        "material:\n"
        "  name: aluminum_6061_t6\n"
        "  yield_strength_mpa: 275\n"
        "global_limits:\n"
        "  safety_factor_min: 2.0\n"
        "  deflection_mm_max: 2.0\n"
        "  modal_ratio_min: 2.0\n"
        "  gait_excitation_hz: 3.0\n"
        "cases:\n"
        "  - name: upper_leg_static\n"
        "    part: upper_leg\n"
        "    load_case: static_stance\n"
        "    max_stress_mpa: 80\n"
        "    max_deflection_mm: 0.8\n"
        "    first_mode_hz: 14\n"
        "    impact_factor: 1.5\n",
        encoding="utf-8",
    )
    payload = runner.run(tmp_path)
    assert payload["valid"] is True
    assert payload["blockers"] == []
    assert payload["summary"]["worst_safety_factor"] > 2

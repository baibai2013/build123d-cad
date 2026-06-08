from __future__ import annotations

import importlib.util
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


def test_search_params_selects_best_candidate(subskill_root, example_project_copy):
    search = _load_module(subskill_root, "search_params.py")
    payload = search.run(example_project_copy)
    assert payload["best_candidate"]["name"] == "safer_trot"
    text = (example_project_copy / "reports" / "best_gait_params.yaml").read_text(encoding="utf-8")
    assert "safer_trot" in text
    assert "stride_mm: 42" in text


def test_write_report_outputs_markdown(subskill_root, example_project_copy):
    writer = _load_module(subskill_root, "write_report.py")
    payload = writer.run(example_project_copy)
    assert payload["project"] == "quadruped_mvp"
    text = (example_project_copy / "reports" / "gait_optimization_report.md").read_text(encoding="utf-8")
    assert "Gait Optimization Report" in text
    assert "Blockers" in text

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


def test_check_protection_outputs_checklist(subskill_root, example_project_copy):
    protection = _load_module(subskill_root, "check_protection.py")
    payload = protection.run(example_project_copy)
    assert payload["project"] == "quadruped_mvp"
    text = (example_project_copy / "reports" / "protection_checklist.md").read_text(encoding="utf-8")
    assert "Protection Checklist" in text
    assert "emergency_stop" in text


def test_write_report_outputs_markdown(subskill_root, example_project_copy):
    writer = _load_module(subskill_root, "write_report.py")
    payload = writer.run(example_project_copy)
    assert payload["valid"] is False
    text = (example_project_copy / "reports" / "circuit_simulation_report.md").read_text(encoding="utf-8")
    assert "Circuit Simulation Report" in text
    assert "Blockers" in text

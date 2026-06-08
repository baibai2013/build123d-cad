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


def test_write_report_outputs_markdown(subskill_root, example_project_copy):
    writer = _load_module(subskill_root, "write_report.py")
    payload = writer.run(example_project_copy)
    assert payload["project"] == "quadruped_mvp"
    text = (example_project_copy / "reports" / "pcb_mechanical_report.md").read_text(encoding="utf-8")
    assert "PCB Mechanical Reliability Report" in text
    assert "Blockers" in text

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module(subskill_root: Path, script_name: str):
    path = subskill_root / "scripts" / script_name
    scripts_dir = str(path.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_g0_passes_for_complete_requirements(subskill_root: Path, example_project: Path):
    collect = _load_module(subskill_root, "collect_artifacts.py")
    gate_mod = _load_module(subskill_root, "run_gate.py")
    collect.collect(example_project)
    payload = gate_mod.run(example_project, "G0")
    assert payload["passed"] is True
    assert payload["blocking_failures"] == []


def test_g3_fails_on_domain_blockers(subskill_root: Path, example_project: Path):
    collect = _load_module(subskill_root, "collect_artifacts.py")
    gate_mod = _load_module(subskill_root, "run_gate.py")
    collect.collect(example_project)
    payload = gate_mod.run(example_project, "G3")
    assert payload["passed"] is False
    assert "flat_walk_no_fall failed" in payload["blocking_failures"]
    written = json.loads((example_project / "reports" / "gate_report.json").read_text(encoding="utf-8"))
    assert written["gate"] == "G3"

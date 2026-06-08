from __future__ import annotations

import importlib.util
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


def test_propose_next_iteration_writes_reports(subskill_root: Path, example_project: Path):
    collect = _load_module(subskill_root, "collect_artifacts.py")
    propose = _load_module(subskill_root, "propose_next_iteration.py")
    collect.collect(example_project)
    score, actions = propose.propose(example_project)
    assert score["prototype_allowed"] is False
    assert actions
    failure_report = (example_project / "reports" / "failure_report.md").read_text(encoding="utf-8")
    next_plan = (example_project / "reports" / "next_iteration_plan.md").read_text(encoding="utf-8")
    assert "flat_walk_no_fall failed" in failure_report
    assert "Next Iteration Plan" in next_plan

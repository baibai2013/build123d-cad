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


def test_score_design_writes_blocked_score(subskill_root: Path, example_project: Path):
    collect = _load_module(subskill_root, "collect_artifacts.py")
    score_mod = _load_module(subskill_root, "score_design.py")
    collect.collect(example_project)
    payload = score_mod.score(example_project)
    assert payload["prototype_allowed"] is False
    assert payload["total_score"] < payload["threshold"]
    assert "flat_walk_no_fall failed" in payload["blockers"]
    written = json.loads((example_project / "reports" / "design_score.json").read_text(encoding="utf-8"))
    assert written["scores"]["mechanical"] == 20

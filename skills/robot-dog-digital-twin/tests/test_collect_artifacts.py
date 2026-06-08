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


def test_collect_artifacts_writes_report(subskill_root: Path, example_project: Path):
    module = _load_module(subskill_root, "collect_artifacts.py")
    payload = module.collect(example_project)
    assert payload["requirements_exists"] is True
    assert payload["verification_matrix_exists"] is True
    assert payload["missing"] == []
    assert (example_project / "reports" / "artifacts.collected.json").exists()
    assert payload["domains"]["electrical"]["pcb_fit"]["exists"] is True

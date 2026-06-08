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


def test_example_contract_validates(subskill_root, example_project_copy):
    validator = _load_module(subskill_root, "validate_contract.py")
    payload = validator.run(example_project_copy)
    assert payload["valid"] is True
    report = json.loads((example_project_copy / "reports" / "requirements_validation.json").read_text(encoding="utf-8"))
    assert report["project"] == "quadruped_mvp"


def test_missing_target_fails(tmp_path, subskill_root):
    common = _load_module(subskill_root, "contract_common.py")
    (tmp_path / "requirements.yaml").write_text(
        'version: "1.0"\nproject:\n  name: bad\nconstraints:\n  safety:\n    require_emergency_stop: true\n',
        encoding="utf-8",
    )
    (tmp_path / "verification_matrix.yaml").write_text(
        "mechanical:\n  no_assembly_interference:\n    source: mechanical\n    required: true\n",
        encoding="utf-8",
    )
    (tmp_path / "architecture.yaml").write_text(
        'version: "1.0"\nsystem:\n  name: bad\ndomains:\n  mechanical:\n    body: test\n',
        encoding="utf-8",
    )
    payload = common.validate_contract(tmp_path)
    assert payload["valid"] is False
    assert "requirements.yaml targets must be a mapping" in payload["errors"]


def test_new_contract_generates_valid_files(tmp_path, subskill_root):
    new_contract = _load_module(subskill_root, "new_contract.py")
    validator = _load_module(subskill_root, "validate_contract.py")
    written = new_contract.run(tmp_path, "fresh_bot")
    assert "requirements.yaml" in written
    payload = validator.run(tmp_path)
    assert payload["valid"] is True

"""shared/schemas/joints.schema.json 自检 + example 校验通过."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
yaml = pytest.importorskip("yaml")


def test_schema_valid(repo_root: Path) -> None:
    schema = json.loads((repo_root / "shared" / "schemas" / "joints.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)


def test_example_validates(example_joints: Path, repo_root: Path) -> None:
    schema = json.loads((repo_root / "shared" / "schemas" / "joints.schema.json").read_text())
    data = yaml.safe_load(example_joints.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(data)


def test_bad_continuous_with_limit_rejected(repo_root: Path) -> None:
    schema = json.loads((repo_root / "shared" / "schemas" / "joints.schema.json").read_text())
    data = {
        "schema_version": 1,
        "robot": "x",
        "links": [{"name": "a"}, {"name": "b"}],
        "joints": [{
            "name": "j", "type": "continuous", "parent": "a", "child": "b",
            "origin": {"xyz": [0, 0, 0], "rpy": [0, 0, 0]},
            "axis": [1, 0, 0],
            "limit": {"lower": -1, "upper": 1},  # ← continuous 不允许 limit
        }],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(data)

"""shared/schemas/world.schema.json 自检 + example 校验通过。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
yaml = pytest.importorskip("yaml")


def _schema(repo_root: Path) -> dict:
    return json.loads((repo_root / "shared" / "schemas" / "world.schema.json").read_text())


def test_schema_valid(repo_root: Path) -> None:
    jsonschema.Draft202012Validator.check_schema(_schema(repo_root))


def test_example_validates(example_world: Path, repo_root: Path) -> None:
    data = yaml.safe_load(example_world.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(_schema(repo_root)).validate(data)


def test_bad_world_name_rejected(repo_root: Path) -> None:
    data = {"schema_version": 1, "world_name": "Has Spaces", "ground": {"type": "plane"}}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(_schema(repo_root)).validate(data)


def test_unknown_top_field_rejected(repo_root: Path) -> None:
    data = {"schema_version": 1, "world_name": "w", "ground": {"type": "plane"}, "nope": 1}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(_schema(repo_root)).validate(data)


def test_bad_sensor_type_rejected(repo_root: Path) -> None:
    data = {
        "schema_version": 1, "world_name": "w",
        "ground": {"type": "plane"},
        "sensors": [{"link": "base_link", "name": "s", "type": "x_ray"}],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(_schema(repo_root)).validate(data)

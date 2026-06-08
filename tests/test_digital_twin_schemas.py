from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "shared" / "schemas"


def test_minimum_digital_twin_schemas_exist_and_parse() -> None:
    required = [
        "requirements.schema.json",
        "verification_matrix.schema.json",
        "sim_result.schema.json",
        "design_score.schema.json",
    ]
    for name in required:
        path = SCHEMA_DIR / name
        assert path.exists(), f"{name} is missing"
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["$schema"].startswith("https://json-schema.org/")
        assert payload["type"] == "object"


def test_design_score_schema_keeps_physical_gate_fields() -> None:
    payload = json.loads((SCHEMA_DIR / "design_score.schema.json").read_text(encoding="utf-8"))
    assert "passed_for_physical_prototype" in payload["required"]
    assert "total_score" in payload["required"]
    assert "blockers" in payload["required"]


def test_requirements_schema_keeps_robot_and_targets_contract() -> None:
    payload = json.loads((SCHEMA_DIR / "requirements.schema.json").read_text(encoding="utf-8"))
    assert {"version", "robot", "targets", "constraints"}.issubset(set(payload["required"]))
    assert {"name", "type", "dof"}.issubset(set(payload["properties"]["robot"]["required"]))

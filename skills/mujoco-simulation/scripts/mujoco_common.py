from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def project_path(raw: str | Path) -> Path:
    return Path(raw).expanduser().resolve()


def reports_dir(project_dir: Path) -> Path:
    return project_dir / "reports"


def mujoco_dir(project_dir: Path) -> Path:
    return project_dir / "simulation" / "mujoco"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_simple_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    list_keys = {"scenarios"}
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if stripped.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"{path}:{lineno}: list item without list parent")
            item_text = stripped[2:]
            if ":" not in item_text:
                raise ValueError(f"{path}:{lineno}: expected key: value in list item")
            key, raw_value = item_text.split(":", 1)
            item: dict[str, Any] = {}
            parent.append(item)
            if raw_value.strip() == "":
                child: dict[str, Any] = {}
                item[key.strip()] = child
                stack.append((indent, item))
                stack.append((indent + 2, child))
            else:
                item[key.strip()] = _parse_scalar(raw_value)
                stack.append((indent, item))
            continue
        if ":" not in stripped:
            raise ValueError(f"{path}:{lineno}: expected key: value")
        key, raw_value = stripped.split(":", 1)
        clean_key = key.strip()
        if raw_value.strip() == "":
            next_value: dict[str, Any] | list[Any] = [] if clean_key in list_keys else {}
            if not isinstance(parent, dict):
                raise ValueError(f"{path}:{lineno}: mapping under non-mapping parent")
            parent[clean_key] = next_value
            stack.append((indent, next_value))
        else:
            if not isinstance(parent, dict):
                raise ValueError(f"{path}:{lineno}: scalar under non-mapping parent")
            parent[clean_key] = _parse_scalar(raw_value)
    return root


def _float_at(mapping: dict[str, Any], key: str, default: float) -> float:
    value = mapping.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bool_at(mapping: dict[str, Any], key: str, default: bool) -> bool:
    value = mapping.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "yes", "1"}
    return bool(value)


def load_scenarios(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "mujoco_scenarios.yaml")


def _limits(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("limits", {}) if isinstance(data.get("limits"), dict) else {}


def _model(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("model", {}) if isinstance(data.get("model"), dict) else {}


def evaluate_project(project_dir: Path) -> dict[str, Any]:
    data = load_scenarios(project_dir)
    limits = _limits(data)
    scenarios = data.get("scenarios", []) if isinstance(data.get("scenarios"), list) else []
    backend = str(data.get("backend", "metadata"))
    project = str(data.get("project", project_dir.name))

    stand_target = _float_at(limits, "stand_stable_seconds_min", 30.0)
    roll_limit = _float_at(limits, "max_body_roll_deg", 8.0)
    pitch_limit = _float_at(limits, "max_body_pitch_deg", 8.0)
    slip_limit = _float_at(limits, "foot_slip_ratio_max", 0.12)
    torque_target = _float_at(limits, "joint_torque_margin_pct_min", 20.0)
    cot_limit = _float_at(limits, "cost_of_transport_max", 2.5)
    penetration_limit = _float_at(limits, "max_contact_penetration_mm", 3.0)
    recovery_limit = _float_at(limits, "recovery_time_s_max", 2.0)

    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []
    scenario_reports: list[dict[str, Any]] = []

    for raw in scenarios:
        scenario = raw if isinstance(raw, dict) else {}
        name = str(scenario.get("name", "unnamed_scenario"))
        scenario_type = str(scenario.get("type", "unknown"))
        required = _bool_at(scenario, "required", True)
        fell = _bool_at(scenario, "fell", False)
        stable_seconds = _float_at(scenario, "stable_seconds", 0.0)
        roll = _float_at(scenario, "max_body_roll_deg", 999.0)
        pitch = _float_at(scenario, "max_body_pitch_deg", 999.0)
        slip = _float_at(scenario, "foot_slip_ratio", 999.0)
        torque_margin = _float_at(scenario, "joint_torque_margin_pct", -100.0)
        cot = _float_at(scenario, "cost_of_transport", 999.0)
        penetration = _float_at(scenario, "max_contact_penetration_mm", 999.0)
        recovery = _float_at(scenario, "recovery_time_s", 0.0)

        scenario_blockers: list[str] = []
        scenario_warnings: list[str] = []
        if fell:
            scenario_blockers.append(f"{name} fell")
            next_actions.append(f"reduce stride aggressiveness or adjust COM for {name}")
        if scenario_type == "stand" and stable_seconds < stand_target:
            scenario_blockers.append(f"{name} stable time {stable_seconds:g}s below {stand_target:g}s")
            next_actions.append(f"lower body height or increase stance support for {name}")
        if roll > roll_limit:
            scenario_blockers.append(f"{name} body roll {roll:g}deg above {roll_limit:g}deg")
            next_actions.append(f"reduce lateral motion or widen stance for {name}")
        if pitch > pitch_limit:
            scenario_blockers.append(f"{name} body pitch {pitch:g}deg above {pitch_limit:g}deg")
            next_actions.append(f"move battery/COM or reduce acceleration for {name}")
        if slip > slip_limit:
            scenario_blockers.append(f"{name} foot slip ratio {slip:g} above {slip_limit:g}")
            next_actions.append(f"increase stance time or adjust friction/contact parameters for {name}")
        if torque_margin < torque_target:
            scenario_blockers.append(f"{name} torque margin {torque_margin:g}% below {torque_target:g}%")
            next_actions.append(f"reduce gait load or choose stronger actuator for {name}")
        if cot > cot_limit and scenario_type not in {"stand", "drop"}:
            scenario_warnings.append(f"{name} cost of transport {cot:g} above {cot_limit:g}")
            next_actions.append(f"reduce vertical motion and swing clearance for {name}")
        if penetration > penetration_limit:
            message = f"{name} contact penetration {penetration:g}mm above {penetration_limit:g}mm"
            if required:
                scenario_blockers.append(message)
            else:
                scenario_warnings.append(message)
            next_actions.append(f"adjust contact parameters or landing stiffness for {name}")
        if recovery > recovery_limit:
            scenario_blockers.append(f"{name} recovery time {recovery:g}s above {recovery_limit:g}s")
            next_actions.append(f"tune push recovery controller for {name}")

        if not required and scenario_blockers:
            warnings.extend(scenario_blockers)
            scenario_warnings.extend(scenario_blockers)
            scenario_blockers = []

        valid = not scenario_blockers
        blockers.extend(scenario_blockers)
        warnings.extend(scenario_warnings)
        scenario_reports.append(
            {
                "name": name,
                "type": scenario_type,
                "required": required,
                "valid": valid,
                "blockers": scenario_blockers,
                "warnings": scenario_warnings,
                "metrics": {
                    "duration_s": _float_at(scenario, "duration_s", 0.0),
                    "stable_seconds": stable_seconds,
                    "fell": fell,
                    "fall_time_s": _float_at(scenario, "fall_time_s", 0.0),
                    "max_body_roll_deg": roll,
                    "max_body_pitch_deg": pitch,
                    "foot_slip_ratio": slip,
                    "joint_torque_margin_pct": torque_margin,
                    "max_contact_penetration_mm": penetration,
                    "cost_of_transport": cot,
                    "recovery_time_s": recovery,
                },
            }
        )

    if not blockers and not next_actions:
        next_actions.append("no MuJoCo scenario changes required for MVP gate")

    valid_count = sum(1 for scenario in scenario_reports if scenario["valid"])
    return {
        "project": project,
        "backend": backend,
        "model": _model(data),
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "summary": {
            "scenario_count": len(scenario_reports),
            "valid_scenario_count": valid_count,
            "required_scenario_count": sum(1 for scenario in scenario_reports if scenario["required"]),
            "backend": backend,
            "metadata_mode": backend == "metadata",
        },
        "scenarios": scenario_reports,
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def scenario_result(project: str, backend: str, scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": project,
        "backend": backend,
        "scenario": scenario["name"],
        "type": scenario["type"],
        "valid": scenario["valid"],
        "blockers": scenario["blockers"],
        "warnings": scenario["warnings"],
        "metrics": scenario["metrics"],
    }


def trajectory_stub(project: str, scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": project,
        "scenario": scenario["name"],
        "format": "build123d-cad.trajectory.v1",
        "points": [
            {"timeFromStartSec": 0.0, "positionsByNameDeg": {}},
            {"timeFromStartSec": scenario["metrics"].get("duration_s", 0.0), "positionsByNameDeg": {}},
        ],
    }


def markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# MuJoCo Validation Report",
        "",
        f"Project: {payload['project']}",
        f"Backend: {payload['backend']}",
        f"Status: {'PASS' if payload['valid'] else 'FAIL'}",
        "",
        "## Scenarios",
    ]
    for scenario in payload["scenarios"]:
        lines.append(f"- {scenario['name']} ({scenario['type']}): {'PASS' if scenario['valid'] else 'FAIL'}")
    lines.extend(["", "## Blockers"])
    if payload["blockers"]:
        lines.extend(f"- {blocker}" for blocker in payload["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    if payload["summary"]["metadata_mode"]:
        lines.extend(["", "## Backend Note", "- metadata mode: these are not real MuJoCo solver results"])
    return "\n".join(lines) + "\n"

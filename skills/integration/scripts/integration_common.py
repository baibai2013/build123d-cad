from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def project_path(raw: str | Path) -> Path:
    return Path(raw).expanduser().resolve()


def reports_dir(project_dir: Path) -> Path:
    return project_dir / "reports"


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
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if ":" not in stripped:
            raise ValueError(f"{path}:{lineno}: expected key: value")
        key, raw_value = stripped.split(":", 1)
        clean_key = key.strip()
        if raw_value.strip() == "":
            if not isinstance(parent, dict):
                raise ValueError(f"{path}:{lineno}: mapping under non-mapping parent")
            child: dict[str, Any] = {}
            parent[clean_key] = child
            stack.append((indent, child))
        else:
            if not isinstance(parent, dict):
                raise ValueError(f"{path}:{lineno}: scalar under non-mapping parent")
            parent[clean_key] = _parse_scalar(raw_value)
    return root


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    return data.get(key, {}) if isinstance(data.get(key), dict) else {}


def _bool_at(mapping: dict[str, Any], key: str, default: bool) -> bool:
    value = mapping.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "yes", "1"}
    return bool(value)


def load_plan(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "integration_plan.yaml")


def evaluate_project(project_dir: Path) -> dict[str, Any]:
    data = load_plan(project_dir)
    project = str(data.get("project", project_dir.name))
    gates = _section(data, "gates")
    safety = _section(data, "safety")
    testbench = _section(data, "testbench")
    capture = _section(data, "data_capture")

    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []

    gate_checks = {
        "digital_twin_passed": "digital twin gate has not passed",
        "manufacturing_pack_complete": "manufacturing pack is incomplete",
        "firmware_dry_run_passed": "firmware dry-run gate has not passed",
        "assembly_inspection_passed": "assembly inspection has not passed",
    }
    for key, message in gate_checks.items():
        if not _bool_at(gates, key, False):
            blockers.append(message)
            next_actions.append(f"complete {key} before integration")

    safety_checks = {
        "emergency_stop_verified": "emergency stop is not physically verified",
        "current_limited_supply_available": "current-limited supply is unavailable",
        "fire_safe_test_area": "fire-safe test area is unavailable",
        "exposed_power_contacts_guarded": "exposed power contacts are not guarded",
    }
    for key, message in safety_checks.items():
        if not _bool_at(safety, key, False):
            blockers.append(message)
            next_actions.append(f"resolve safety item {key}")

    stage = str(testbench.get("requested_stage", "inspection"))
    if stage in {"first_power", "motor_motion"} and not _bool_at(gates, "human_first_power_approval", False):
        blockers.append("human first-power approval is missing")
        next_actions.append("obtain explicit human approval for first power-on")
    if _bool_at(testbench, "motor_motion_requested", False) and not _bool_at(gates, "human_motor_motion_approval", False):
        blockers.append("human motor-motion approval is missing")
        next_actions.append("obtain explicit human approval before any motor motion")
    if not _bool_at(testbench, "telemetry_logger_available", False):
        blockers.append("telemetry logger is unavailable")
        next_actions.append("set up telemetry logger before bring-up")
    if not _bool_at(testbench, "spare_fuses_available", False):
        warnings.append("spare fuses are not available")

    required_capture = ("joint_states", "imu", "bus_voltage_current", "controller_latency", "fault_states")
    for key in required_capture:
        if not _bool_at(capture, key, False):
            blockers.append(f"data capture missing {key}")
            next_actions.append(f"enable {key} logging for sim2real calibration")

    if not blockers:
        next_actions.append("integration dry-run gate is ready for the requested stage")

    return {
        "project": project,
        "valid": not blockers,
        "requested_stage": stage,
        "blockers": blockers,
        "warnings": warnings,
        "gates": gates,
        "safety": safety,
        "testbench": testbench,
        "data_capture": capture,
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def bringup_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bring-Up Readiness Report",
        "",
        f"Project: {payload['project']}",
        f"Requested stage: {payload['requested_stage']}",
        f"Status: {'PASS' if payload['valid'] else 'FAIL'}",
        "",
        "## Blockers",
    ]
    if payload["blockers"]:
        lines.extend(f"- {blocker}" for blocker in payload["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    return "\n".join(lines) + "\n"


def hil_plan_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# HIL Plan",
        "",
        f"Project: {payload['project']}",
        "",
        "## Required Setup",
        "- current-limited bench supply",
        "- emergency stop in reach",
        "- telemetry logger",
        "- firmware dry-run artifacts",
        "- robot restrained or motors disconnected for first checks",
        "",
        "## Stages",
        "- inspection",
        "- continuity check",
        "- first power with current limit",
        "- firmware heartbeat",
        "- sensor telemetry",
        "- one-joint low-current motion only after human approval",
    ]
    return "\n".join(lines) + "\n"


def data_capture_markdown(payload: dict[str, Any]) -> str:
    capture = payload["data_capture"]
    lines = ["# Data Capture Checklist", ""]
    for key in ("joint_states", "imu", "bus_voltage_current", "controller_latency", "fault_states"):
        lines.append(f"- {key}: {'yes' if _bool_at(capture, key, False) else 'no'}")
    return "\n".join(lines) + "\n"

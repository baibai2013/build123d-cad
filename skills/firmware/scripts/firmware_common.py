from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def project_path(raw: str | Path) -> Path:
    return Path(raw).expanduser().resolve()


def reports_dir(project_dir: Path) -> Path:
    return project_dir / "reports"


def firmware_dir(project_dir: Path) -> Path:
    return project_dir / "firmware"


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


def load_plan(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "firmware_plan.yaml")


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    return data.get(key, {}) if isinstance(data.get(key), dict) else {}


def evaluate_project(project_dir: Path) -> dict[str, Any]:
    data = load_plan(project_dir)
    project = str(data.get("project", project_dir.name))
    target = _section(data, "target")
    loop = _section(data, "control_loop")
    bus = _section(data, "bus")
    safety = _section(data, "safety")
    calibration = _section(data, "calibration")

    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []

    if not target.get("mcu"):
        blockers.append("target MCU is missing")
        next_actions.append("select MCU before firmware project generation")
    if not target.get("toolchain"):
        blockers.append("firmware toolchain is missing")
        next_actions.append("choose platformio/cmake/vendor toolchain")
    frequency = _float_at(loop, "frequency_hz", 0.0)
    frequency_min = _float_at(loop, "frequency_min_hz", 250.0)
    if frequency < frequency_min:
        blockers.append(f"control loop frequency {frequency:g}Hz below {frequency_min:g}Hz")
        next_actions.append("increase control loop frequency or lower firmware gate threshold")
    watchdog = _float_at(loop, "watchdog_ms", 0.0)
    if watchdog <= 0:
        blockers.append("watchdog timeout is missing")
        next_actions.append("define watchdog_ms for control loop")
    if str(bus.get("type", "")) not in {"can", "can_fd", "ethercat", "uart"}:
        blockers.append("bus type is missing or unsupported")
        next_actions.append("define CAN/CAN-FD/EtherCAT bus contract")
    if _float_at(bus, "heartbeat_ms", 0.0) <= 0:
        blockers.append("heartbeat period is missing")
        next_actions.append("define heartbeat_ms for bus watchdog")
    if not _bool_at(safety, "emergency_stop", False):
        blockers.append("emergency stop is not enabled")
        next_actions.append("add emergency-stop input and firmware kill path")
    undervoltage = _float_at(safety, "undervoltage_cutoff_v", 0.0)
    undervoltage_min = _float_at(safety, "undervoltage_min_v", 0.0)
    if undervoltage <= 0 or undervoltage < undervoltage_min:
        blockers.append(f"undervoltage cutoff {undervoltage:g}V below safe minimum {undervoltage_min:g}V")
        next_actions.append("raise undervoltage cutoff or update battery safety requirement")
    if _float_at(safety, "overcurrent_limit_a", 0.0) <= 0:
        blockers.append("overcurrent limit is missing")
        next_actions.append("define overcurrent_limit_a for motor drivers")
    thermal = _float_at(safety, "thermal_shutdown_c", 0.0)
    thermal_max = _float_at(safety, "thermal_shutdown_max_c", 85.0)
    if thermal <= 0 or thermal > thermal_max:
        blockers.append(f"thermal shutdown {thermal:g}C above max {thermal_max:g}C")
        next_actions.append("lower thermal shutdown threshold")
    if _bool_at(calibration, "joint_zero_required", True) and not _bool_at(calibration, "captured_joint_zero", False):
        blockers.append("joint zero calibration is required but not captured")
        next_actions.append("capture joint zero calibration before bring-up")
    if _bool_at(calibration, "encoder_offset_required", True) and not _bool_at(calibration, "captured_encoder_offset", False):
        blockers.append("encoder offset calibration is required but not captured")
        next_actions.append("capture encoder offsets before closed-loop motor control")

    if not blockers:
        next_actions.append("firmware dry-run contract is ready for build scaffolding")
    if target.get("toolchain") == "platformio":
        warnings.append("platformio build is not run by this MVP")

    return {
        "project": project,
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "summary": {
            "mcu": target.get("mcu", ""),
            "toolchain": target.get("toolchain", ""),
            "joint_count": int(_float_at(target, "joint_count", 0.0)),
            "control_frequency_hz": frequency,
            "bus": bus.get("type", ""),
            "emergency_stop": _bool_at(safety, "emergency_stop", False),
        },
        "target": target,
        "control_loop": loop,
        "bus": bus,
        "safety": safety,
        "calibration": calibration,
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def manifest(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": payload["project"],
        "target": payload["target"],
        "control_loop": payload["control_loop"],
        "bus": payload["bus"],
        "safety": payload["safety"],
        "dry_run_only": True,
    }


def calibration_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": payload["project"],
        "calibration": payload["calibration"],
        "ready_for_closed_loop": payload["valid"],
    }


def can_frames_markdown(payload: dict[str, Any]) -> str:
    bus = payload["bus"]
    target = payload["target"]
    lines = [
        "# CAN Frame Contract",
        "",
        f"Project: {payload['project']}",
        f"Bus: {bus.get('type', 'unknown')}",
        f"Bitrate: {bus.get('bitrate_kbps', 0)} kbps",
        f"Joint count: {target.get('joint_count', 0)}",
        "",
        "## Frames",
        f"- emergency_stop: 0x{int(bus.get('estop_id', 0)):03X}",
        f"- command_base: 0x{int(bus.get('command_id_base', 0)):03X}",
        f"- telemetry_base: 0x{int(bus.get('telemetry_id_base', 0)):03X}",
        f"- heartbeat_ms: {bus.get('heartbeat_ms', 0)}",
    ]
    return "\n".join(lines) + "\n"


def test_report(payload: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "target_defined": bool(payload["target"].get("mcu")),
        "control_loop_ok": payload["summary"]["control_frequency_hz"] >= _float_at(payload["control_loop"], "frequency_min_hz", 250.0),
        "bus_contract_ok": bool(payload["bus"].get("type")) and _float_at(payload["bus"], "heartbeat_ms", 0.0) > 0,
        "safety_contract_ok": not any("emergency stop" in blocker or "undervoltage" in blocker or "overcurrent" in blocker or "thermal" in blocker for blocker in payload["blockers"]),
        "calibration_contract_ok": not any("calibration" in blocker for blocker in payload["blockers"]),
    }
    return {
        "project": payload["project"],
        "valid": all(checks.values()),
        "checks": checks,
        "blockers": payload["blockers"],
        "warnings": payload["warnings"],
    }

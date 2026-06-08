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


def _float_at(mapping: dict[str, Any], key: str, default: float) -> float:
    value = mapping.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_dataset(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "calibration_dataset.yaml")


def pct_error(sim: float, real: float) -> float:
    if abs(sim) < 1e-9:
        return 0.0 if abs(real) < 1e-9 else 999.0
    return (real - sim) / abs(sim) * 100.0


def evaluate_project(project_dir: Path) -> dict[str, Any]:
    data = load_dataset(project_dir)
    project = str(data.get("project", project_dir.name))
    tolerances = _section(data, "tolerances")
    sim = _section(data, "simulation")
    real = _section(data, "real")
    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []

    speed_sim = _float_at(sim, "average_speed_mps", 0.0)
    speed_real = _float_at(real, "average_speed_mps", 0.0)
    speed_error = pct_error(speed_sim, speed_real)
    speed_limit = _float_at(tolerances, "speed_error_pct_max", 15.0)
    if abs(speed_error) > speed_limit:
        blockers.append(f"speed error {speed_error:.1f}% exceeds {speed_limit:g}%")
        next_actions.append("increase drivetrain loss or retune gait speed model")

    slip_sim = _float_at(sim, "foot_slip_ratio", 0.0)
    slip_real = _float_at(real, "foot_slip_ratio", 0.0)
    slip_error = slip_real - slip_sim
    slip_limit = _float_at(tolerances, "slip_error_abs_max", 0.05)
    if abs(slip_error) > slip_limit:
        blockers.append(f"slip error {slip_error:.3f} exceeds {slip_limit:g}")
        next_actions.append("adjust friction/contact parameters and foot material model")

    torque_sim = _float_at(sim, "peak_joint_torque_nm", 0.0)
    torque_real = _float_at(real, "peak_joint_torque_nm", 0.0)
    torque_error = pct_error(torque_sim, torque_real)
    torque_limit = _float_at(tolerances, "torque_error_pct_max", 20.0)
    if abs(torque_error) > torque_limit:
        blockers.append(f"torque error {torque_error:.1f}% exceeds {torque_limit:g}%")
        next_actions.append("increase actuator load scale or inertia estimate")

    roll_error = _float_at(real, "max_body_roll_deg", 0.0) - _float_at(sim, "max_body_roll_deg", 0.0)
    pitch_error = _float_at(real, "max_body_pitch_deg", 0.0) - _float_at(sim, "max_body_pitch_deg", 0.0)
    posture_limit = _float_at(tolerances, "posture_error_deg_max", 3.0)
    if abs(roll_error) > posture_limit or abs(pitch_error) > posture_limit:
        blockers.append(f"posture error roll={roll_error:.1f}deg pitch={pitch_error:.1f}deg exceeds {posture_limit:g}deg")
        next_actions.append("review COM, inertia, and contact damping")

    latency_error = _float_at(real, "controller_latency_ms", 0.0) - _float_at(sim, "controller_latency_ms", 0.0)
    latency_limit = _float_at(tolerances, "latency_error_ms_max", 10.0)
    if abs(latency_error) > latency_limit:
        blockers.append(f"latency error {latency_error:.1f}ms exceeds {latency_limit:g}ms")
        next_actions.append("add control latency parameter and rerun gait simulation")

    if not blockers:
        next_actions.append("sim-real metrics are within MVP tolerances")
    if not real:
        blockers.append("real metrics are missing")
        next_actions.append("collect physical prototype log before calibration")

    metrics = {
        "speed_error_pct": round(speed_error, 3),
        "slip_error_abs": round(slip_error, 3),
        "torque_error_pct": round(torque_error, 3),
        "roll_error_deg": round(roll_error, 3),
        "pitch_error_deg": round(pitch_error, 3),
        "latency_error_ms": round(latency_error, 3),
    }
    return {
        "project": project,
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "summary": metrics,
        "simulation": sim,
        "real": real,
        "tolerances": tolerances,
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def parameter_update(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    drivetrain_loss = min(0.3, max(0.0, -summary["speed_error_pct"] / 100.0 * 0.5))
    friction_scale = max(0.5, min(1.5, 1.0 - summary["slip_error_abs"]))
    torque_scale = max(0.8, min(1.5, 1.0 + summary["torque_error_pct"] / 100.0 * 0.5))
    latency_ms = max(0.0, summary["latency_error_ms"])
    lines = [
        f"project: {payload['project']}",
        "parameter_update:",
        f"  drivetrain_loss_add: {drivetrain_loss:.3f}",
        f"  foot_friction_scale: {friction_scale:.3f}",
        f"  actuator_load_scale: {torque_scale:.3f}",
        f"  control_latency_ms_add: {latency_ms:.3f}",
        "notes:",
        "  - conservative MVP suggestions; rerun simulation and physical test after applying",
    ]
    return "\n".join(lines) + "\n"


def markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Sim2Real Calibration Report",
        "",
        f"Project: {payload['project']}",
        f"Status: {'PASS' if payload['valid'] else 'FAIL'}",
        "",
        "## Error Summary",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: {value:g}")
    lines.extend(["", "## Blockers"])
    if payload["blockers"]:
        lines.extend(f"- {blocker}" for blocker in payload["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    return "\n".join(lines) + "\n"

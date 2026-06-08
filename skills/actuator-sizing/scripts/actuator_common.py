from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


GRAVITY = 9.81
MIN_MARGIN_PCT = 20.0


DEFAULT_ACTUATOR = {
    "name": "mvp_integrated_actuator",
    "available_torque_nm": 5.0,
    "continuous_torque_nm": 3.5,
    "max_speed_rad_s": 18.0,
    "gear_ratio": 9.0,
}


def project_path(raw: str | Path) -> Path:
    return Path(raw).expanduser().resolve()


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
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            raise ValueError(f"{path}:{lineno}: expected key: value")
        key, raw_value = stripped.split(":", 1)
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if raw_value.strip() == "":
            child: dict[str, Any] = {}
            parent[key.strip()] = child
            stack.append((indent, child))
        else:
            parent[key.strip()] = _parse_scalar(raw_value)
    return root


def reports_dir(project_dir: Path) -> Path:
    return project_dir / "reports"


def load_requirements(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "requirements.yaml")


def load_architecture(project_dir: Path) -> dict[str, Any]:
    path = project_dir / "architecture.yaml"
    return load_simple_yaml(path) if path.exists() else {}


def load_actuator_candidate(project_dir: Path) -> dict[str, Any]:
    path = project_dir / "actuator_candidate.yaml"
    if not path.exists():
        return dict(DEFAULT_ACTUATOR)
    data = load_simple_yaml(path)
    candidate = dict(DEFAULT_ACTUATOR)
    candidate.update(data.get("actuator", data))
    return candidate


def _float_at(mapping: dict[str, Any], key: str, default: float) -> float:
    value = mapping.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def estimate_payload(project_dir: Path) -> dict[str, Any]:
    requirements = load_requirements(project_dir)
    architecture = load_architecture(project_dir)
    candidate = load_actuator_candidate(project_dir)

    targets = requirements.get("targets", {}) if isinstance(requirements.get("targets"), dict) else {}
    system = architecture.get("system", {}) if isinstance(architecture.get("system"), dict) else {}
    geometry = architecture.get("geometry", {}) if isinstance(architecture.get("geometry"), dict) else {}

    mass_kg = _float_at(targets, "mass_kg", 5.0)
    payload_kg = _float_at(targets, "payload_kg", 0.5)
    speed_mps = _float_at(targets, "flat_walk_speed_mps", 0.5)
    slope_deg = _float_at(targets, "max_slope_deg", 0.0)
    legs = int(_float_at(system, "legs", 4))
    stance_legs = max(2, int(_float_at(system, "stance_legs", 3)))

    femur_m = _float_at(geometry, "femur_length_m", 0.09)
    tibia_m = _float_at(geometry, "tibia_length_m", 0.10)
    body_half_width_m = _float_at(geometry, "body_half_width_m", 0.09)

    total_mass = mass_kg + payload_kg
    load_per_leg = total_mass * GRAVITY / stance_legs
    dynamic_factor = 1.4 + min(0.6, max(0.0, speed_mps))
    slope_factor = 1.0 + math.sin(math.radians(max(0.0, slope_deg)))

    required = {
        "hip": load_per_leg * body_half_width_m * slope_factor,
        "knee": load_per_leg * femur_m * dynamic_factor * slope_factor,
        "ankle": load_per_leg * tibia_m * 0.6 * dynamic_factor,
    }

    available = float(candidate["available_torque_nm"])
    continuous = float(candidate["continuous_torque_nm"])
    max_speed = float(candidate["max_speed_rad_s"])
    required_speed = max(1.0, speed_mps / max(0.05, femur_m + tibia_m) * 2.0)

    joints: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    margins: list[float] = []

    for name, required_torque in required.items():
        available_margin = (available - required_torque) / available * 100.0
        thermal_margin = (continuous - required_torque * 0.65) / continuous * 100.0
        speed_margin = (max_speed - required_speed) / max_speed * 100.0
        joint_margin = min(available_margin, thermal_margin, speed_margin)
        margins.append(joint_margin)
        joints[name] = {
            "required_torque_nm": round(required_torque, 3),
            "available_torque_nm": round(available, 3),
            "continuous_torque_nm": round(continuous, 3),
            "required_speed_rad_s": round(required_speed, 3),
            "max_speed_rad_s": round(max_speed, 3),
            "torque_margin_pct": round(available_margin, 2),
            "thermal_margin_pct": round(thermal_margin, 2),
            "speed_margin_pct": round(speed_margin, 2),
            "margin_pct": round(joint_margin, 2),
        }
        if joint_margin < MIN_MARGIN_PCT:
            blockers.append(f"{name} actuator margin below {int(MIN_MARGIN_PCT)}%")

    minimum_margin = min(margins) if margins else 0.0
    return {
        "project": project_dir.name,
        "valid": not blockers,
        "minimum_margin_pct": round(minimum_margin, 2),
        "blockers": blockers,
        "inputs": {
            "mass_kg": mass_kg,
            "payload_kg": payload_kg,
            "flat_walk_speed_mps": speed_mps,
            "max_slope_deg": slope_deg,
            "legs": legs,
            "stance_legs": stance_legs,
            "femur_length_m": femur_m,
            "tibia_length_m": tibia_m,
            "body_half_width_m": body_half_width_m,
        },
        "actuator": candidate,
        "joints": joints,
    }


def actuator_spec_yaml(payload: dict[str, Any]) -> str:
    actuator = payload["actuator"]
    lines = [
        'version: "1.0"',
        "actuator:",
        f"  name: {actuator['name']}",
        f"  available_torque_nm: {actuator['available_torque_nm']}",
        f"  continuous_torque_nm: {actuator['continuous_torque_nm']}",
        f"  max_speed_rad_s: {actuator['max_speed_rad_s']}",
        f"  gear_ratio: {actuator['gear_ratio']}",
        "summary:",
        f"  valid: {str(payload['valid']).lower()}",
        f"  minimum_margin_pct: {payload['minimum_margin_pct']}",
    ]
    return "\n".join(lines) + "\n"


def markdown_report(payload: dict[str, Any]) -> str:
    status = "PASS" if payload["valid"] else "FAIL"
    lines = [
        "# Actuator Sizing Report",
        "",
        f"Project: {payload['project']}",
        f"Status: {status}",
        f"Minimum margin: {payload['minimum_margin_pct']}%",
        "",
        "## Blockers",
    ]
    blockers = payload.get("blockers", [])
    if blockers:
        lines.extend(f"- {blocker}" for blocker in blockers)
    else:
        lines.append("- none")
    lines.extend(["", "## Joint Margins"])
    for name, report in payload["joints"].items():
        lines.append(f"- {name}: {report['margin_pct']}%")
    return "\n".join(lines) + "\n"

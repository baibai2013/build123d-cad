from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


LEG_NAMES = ("front_left", "front_right", "rear_left", "rear_right")


def project_path(raw: str | Path) -> Path:
    return Path(raw).expanduser().resolve()


def reports_dir(project_dir: Path) -> Path:
    return project_dir / "reports"


def control_dir(project_dir: Path) -> Path:
    return project_dir / "control"


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
    list_keys = {"ik_targets"}
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


def load_motion_plan(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "motion_plan.yaml")


def _limits(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("joint_limits_deg", {}) if isinstance(data.get("joint_limits_deg"), dict) else {}


def _links(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("link_lengths", {}) if isinstance(data.get("link_lengths"), dict) else {}


def _gait(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("gait", {}) if isinstance(data.get("gait"), dict) else {}


def solve_plan(project_dir: Path) -> dict[str, Any]:
    data = load_motion_plan(project_dir)
    project = str(data.get("project", project_dir.name))
    links = _links(data)
    limits = _limits(data)
    l1 = _float_at(links, "thigh_mm", 90.0)
    l2 = _float_at(links, "shank_mm", 95.0)
    hip_min = _float_at(limits, "hip_pitch_min", -80.0)
    hip_max = _float_at(limits, "hip_pitch_max", 80.0)
    knee_min = _float_at(limits, "knee_pitch_min", -150.0)
    knee_max = _float_at(limits, "knee_pitch_max", 5.0)
    targets = data.get("ik_targets", []) if isinstance(data.get("ik_targets"), list) else []

    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []
    solutions: list[dict[str, Any]] = []

    for raw in targets:
        target = raw if isinstance(raw, dict) else {}
        name = str(target.get("name", "unnamed_target"))
        leg = str(target.get("leg", "front_left"))
        x = _float_at(target, "x_mm", 0.0)
        z = _float_at(target, "z_mm", 0.0)
        required = _bool_at(target, "required", True)
        distance = math.hypot(x, z)
        target_blockers: list[str] = []
        if distance > l1 + l2:
            target_blockers.append(f"{name} target distance {distance:.1f}mm exceeds reach {(l1 + l2):.1f}mm")
            next_actions.append(f"reduce stride or increase leg length for {name}")
        if distance < abs(l1 - l2):
            target_blockers.append(f"{name} target distance {distance:.1f}mm below folded reach {abs(l1 - l2):.1f}mm")
            next_actions.append(f"move foot target away from hip for {name}")

        hip_deg = 0.0
        knee_deg = 0.0
        if not target_blockers:
            cos_knee = (distance * distance - l1 * l1 - l2 * l2) / (2.0 * l1 * l2)
            cos_knee = max(-1.0, min(1.0, cos_knee))
            knee_rad = -math.acos(cos_knee)
            hip_rad = math.atan2(z, x) - math.atan2(l2 * math.sin(knee_rad), l1 + l2 * math.cos(knee_rad))
            hip_deg = math.degrees(hip_rad)
            knee_deg = math.degrees(knee_rad)
            if hip_deg < hip_min or hip_deg > hip_max:
                target_blockers.append(f"{name} hip pitch {hip_deg:.1f}deg outside [{hip_min:g}, {hip_max:g}]")
                next_actions.append(f"move {name} foot target inside hip pitch range")
            if knee_deg < knee_min or knee_deg > knee_max:
                target_blockers.append(f"{name} knee pitch {knee_deg:.1f}deg outside [{knee_min:g}, {knee_max:g}]")
                next_actions.append(f"move {name} foot target inside knee pitch range")

        if target_blockers and not required:
            warnings.extend(target_blockers)
            target_blockers = []

        blockers.extend(target_blockers)
        solutions.append(
            {
                "name": name,
                "leg": leg,
                "valid": not target_blockers,
                "required": required,
                "target": {"x_mm": x, "z_mm": z, "distance_mm": round(distance, 3)},
                "joints_deg": {"hip_pitch": round(hip_deg, 3), "knee_pitch": round(knee_deg, 3)},
                "blockers": target_blockers,
            }
        )

    if not blockers and not next_actions:
        next_actions.append("no IK changes required for MVP gate")

    return {
        "project": project,
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "summary": {
            "target_count": len(solutions),
            "valid_target_count": sum(1 for item in solutions if item["valid"]),
            "thigh_mm": l1,
            "shank_mm": l2,
        },
        "solutions": solutions,
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def ik_solution(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": payload["project"],
        "valid": payload["valid"],
        "solutions": payload["solutions"],
    }


def phase_offsets(gait_type: str) -> dict[str, float]:
    if gait_type == "walk":
        return {"front_left": 0.0, "rear_right": 0.25, "front_right": 0.5, "rear_left": 0.75}
    if gait_type == "bound":
        return {"front_left": 0.0, "front_right": 0.0, "rear_left": 0.5, "rear_right": 0.5}
    return {"front_left": 0.0, "rear_right": 0.0, "front_right": 0.5, "rear_left": 0.5}


def generate_trajectory(project_dir: Path, ik_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_motion_plan(project_dir)
    project = str(data.get("project", project_dir.name))
    gait = _gait(data)
    gait_type = str(gait.get("type", "trot"))
    cycle_time = _float_at(gait, "cycle_time_s", 0.6)
    samples = max(2, int(_float_at(gait, "samples_per_cycle", 8)))
    stride = _float_at(gait, "stride_length_mm", 60.0)
    swing = _float_at(gait, "swing_height_mm", 35.0)
    duty = _float_at(gait, "duty_factor", 0.55)
    body_height = _float_at(gait, "body_height_mm", 135.0)
    controller = gait.get("controller", {}) if isinstance(gait.get("controller"), dict) else {}
    ik_payload = ik_payload or solve_plan(project_dir)

    blockers = list(ik_payload["blockers"])
    warnings: list[str] = []
    next_actions = list(ik_payload["next_actions"])
    if duty < 0.45:
        warnings.append("duty factor below 0.45 may be aggressive for MVP trot")
        next_actions.append("increase duty factor before dynamics validation")
    if stride > body_height * 0.6:
        warnings.append("stride length is large relative to body height")
        next_actions.append("reduce stride length or validate in MuJoCo before firmware handoff")

    offsets = phase_offsets(gait_type)
    points: list[dict[str, Any]] = []
    for i in range(samples):
        t = cycle_time * i / (samples - 1)
        positions: dict[str, float] = {}
        for leg in LEG_NAMES:
            phase = (i / samples + offsets[leg]) % 1.0
            swing_phase = max(0.0, min(1.0, (phase - duty) / max(0.001, 1.0 - duty)))
            hip = (phase - 0.5) * stride * 0.25
            knee = -55.0 + math.sin(math.pi * swing_phase) * swing * 0.25
            positions[f"{leg}_hip_pitch"] = round(hip, 3)
            positions[f"{leg}_knee_pitch"] = round(knee, 3)
        points.append({"timeFromStartSec": round(t, 4), "positionsByNameDeg": positions})

    return {
        "project": project,
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "summary": {
            "gait_type": gait_type,
            "cycle_time_s": cycle_time,
            "samples_per_cycle": samples,
            "stride_length_mm": stride,
            "swing_height_mm": swing,
            "duty_factor": duty,
            "trajectory_points": len(points),
        },
        "trajectory": {"format": "build123d-cad.trajectory.v1", "points": points},
        "controller": {
            "mode": str(controller.get("mode", "position")),
            "control_rate_hz": _float_at(controller, "control_rate_hz", 200.0),
            "kp": _float_at(controller, "kp", 28.0),
            "kd": _float_at(controller, "kd", 0.8),
        },
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def controller_yaml(payload: dict[str, Any]) -> str:
    controller = payload["controller"]
    summary = payload["summary"]
    return "\n".join(
        [
            f"project: {payload['project']}",
            f"mode: {controller['mode']}",
            f"control_rate_hz: {controller['control_rate_hz']:g}",
            f"kp: {controller['kp']:g}",
            f"kd: {controller['kd']:g}",
            f"gait_type: {summary['gait_type']}",
            f"cycle_time_s: {summary['cycle_time_s']:g}",
            f"duty_factor: {summary['duty_factor']:g}",
        ]
    ) + "\n"


def markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Motion Control Report",
        "",
        f"Project: {payload['project']}",
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

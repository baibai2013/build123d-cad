from __future__ import annotations

import json
from pathlib import Path
from typing import Any


WEIGHTS = {
    "ik": 10,
    "phase": 10,
    "stand": 15,
    "flat_walk": 20,
    "posture": 15,
    "slip": 10,
    "torque": 10,
    "speed_energy": 10,
}


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
        if raw_value.strip() == "":
            next_value: dict[str, Any] | list[Any] = {}
            if key.strip() == "candidates":
                next_value = []
            if not isinstance(parent, dict):
                raise ValueError(f"{path}:{lineno}: mapping under non-mapping parent")
            parent[key.strip()] = next_value
            stack.append((indent, next_value))
        else:
            if not isinstance(parent, dict):
                raise ValueError(f"{path}:{lineno}: scalar under non-mapping parent")
            parent[key.strip()] = _parse_scalar(raw_value)
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


def load_gait(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "gait_validation.yaml")


def _target(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("target", {}) if isinstance(data.get("target"), dict) else {}


def _score_validation(validation: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    stand_target = _float_at(target, "stand_stable_seconds", 30.0)
    speed_target = _float_at(target, "average_speed_mps_min", 0.5)
    roll_limit = _float_at(target, "max_body_roll_deg", 8.0)
    pitch_limit = _float_at(target, "max_body_pitch_deg", 8.0)
    slip_limit = _float_at(target, "foot_slip_ratio_max", 0.12)
    torque_target = _float_at(target, "joint_torque_margin_pct_min", 20.0)
    cot_limit = _float_at(target, "cost_of_transport_max", 2.5)

    single_leg_ik_pass = _bool_at(validation, "single_leg_ik_pass", False)
    phase_complete = _bool_at(validation, "phase_complete", False)
    stand_seconds = _float_at(validation, "stand_stable_seconds", 0.0)
    flat_walk_no_fall = _bool_at(validation, "flat_walk_no_fall", False)
    roll = _float_at(validation, "max_body_roll_deg", 999.0)
    pitch = _float_at(validation, "max_body_pitch_deg", 999.0)
    slip = _float_at(validation, "foot_slip_ratio", 999.0)
    torque_margin = _float_at(validation, "joint_torque_margin_pct", -100.0)
    speed = _float_at(validation, "average_speed_mps", 0.0)
    cot = _float_at(validation, "cost_of_transport", 999.0)

    levels = {
        "L0_single_leg_ik": single_leg_ik_pass,
        "L1_phase_complete": phase_complete,
        "L2_stand_stable": stand_seconds >= stand_target,
        "L3_flat_walk_no_fall": flat_walk_no_fall,
        "L4_posture_within_limits": roll <= roll_limit and pitch <= pitch_limit,
        "L5_foot_slip_ok": slip <= slip_limit,
        "L6_torque_margin_ok": torque_margin >= torque_target,
        "L7_speed_energy_ok": speed >= speed_target and cot <= cot_limit,
    }

    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []

    if not single_leg_ik_pass:
        blockers.append("single leg IK failed")
        next_actions.append("fix leg IK limits before gait iteration")
    if not phase_complete:
        blockers.append("four-leg phase pattern incomplete")
        next_actions.append("define a complete four-leg phase table")
    if stand_seconds < stand_target:
        blockers.append(f"stand stable time {stand_seconds:g}s below target {stand_target:g}s")
        next_actions.append("lower body height or increase stance duty factor")
    if not flat_walk_no_fall:
        blockers.append("flat walk fell")
        next_actions.append("reduce stride length and increase duty factor")
    if roll > roll_limit:
        blockers.append(f"body roll {roll:g}deg above limit {roll_limit:g}deg")
        next_actions.append("reduce lateral body motion and stance width error")
    if pitch > pitch_limit:
        blockers.append(f"body pitch {pitch:g}deg above limit {pitch_limit:g}deg")
        next_actions.append("move COM or reduce acceleration/stride aggressiveness")
    if slip > slip_limit:
        blockers.append(f"foot slip ratio {slip:g} above limit {slip_limit:g}")
        next_actions.append("reduce stride length or increase stance time")
    if torque_margin < torque_target:
        blockers.append(f"joint torque margin {torque_margin:g}% below target {torque_target:g}%")
        next_actions.append("reduce gait aggressiveness or increase actuator torque")
    if speed < speed_target:
        warnings.append(f"average speed {speed:g}m/s below target {speed_target:g}m/s")
        next_actions.append("increase speed only after stability blockers are cleared")
    if cot > cot_limit:
        warnings.append(f"cost of transport {cot:g} above limit {cot_limit:g}")
        next_actions.append("reduce vertical motion and avoid excessive swing clearance")

    score = 0
    score += WEIGHTS["ik"] if single_leg_ik_pass else 0
    score += WEIGHTS["phase"] if phase_complete else 0
    score += WEIGHTS["stand"] if stand_seconds >= stand_target else max(0, int(WEIGHTS["stand"] * stand_seconds / stand_target))
    score += WEIGHTS["flat_walk"] if flat_walk_no_fall else 0
    score += WEIGHTS["posture"] if roll <= roll_limit and pitch <= pitch_limit else 0
    score += WEIGHTS["slip"] if slip <= slip_limit else 0
    score += WEIGHTS["torque"] if torque_margin >= torque_target else max(0, int(WEIGHTS["torque"] * max(0, torque_margin) / torque_target))
    score += WEIGHTS["speed_energy"] if speed >= speed_target and cot <= cot_limit else 0

    return {
        "valid": not blockers,
        "score": int(score),
        "blockers": blockers,
        "warnings": warnings,
        "levels": levels,
        "metrics": {
            "stand_stable_seconds": stand_seconds,
            "flat_walk_no_fall": flat_walk_no_fall,
            "fall_time_s": _float_at(validation, "fall_time_s", 0.0),
            "max_body_roll_deg": roll,
            "max_body_pitch_deg": pitch,
            "foot_slip_ratio": slip,
            "joint_torque_margin_pct": torque_margin,
            "average_speed_mps": speed,
            "cost_of_transport": cot,
        },
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def _candidate_report(candidate: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    validation = candidate.get("validation", {}) if isinstance(candidate.get("validation"), dict) else {}
    params = candidate.get("params", {}) if isinstance(candidate.get("params"), dict) else {}
    report = _score_validation(validation, target)
    return {
        "name": candidate.get("name", "candidate"),
        "valid": report["valid"],
        "score": report["score"],
        "params": params,
        "blockers": report["blockers"],
        "warnings": report["warnings"],
        "metrics": report["metrics"],
    }


def evaluate_project(project_dir: Path) -> dict[str, Any]:
    data = load_gait(project_dir)
    target = _target(data)
    current_params = data.get("gait_params", {}) if isinstance(data.get("gait_params"), dict) else {}
    validation = data.get("validation", {}) if isinstance(data.get("validation"), dict) else {}
    current = _score_validation(validation, target)
    candidates_raw = data.get("candidates", []) if isinstance(data.get("candidates"), list) else []
    candidates = [_candidate_report(item if isinstance(item, dict) else {}, target) for item in candidates_raw]
    all_options = [
        {
            "name": current_params.get("name", "current"),
            "valid": current["valid"],
            "score": current["score"],
            "params": current_params,
            "blockers": current["blockers"],
            "warnings": current["warnings"],
            "metrics": current["metrics"],
        },
        *candidates,
    ]
    best = sorted(all_options, key=lambda item: (item["valid"], item["score"]), reverse=True)[0]
    failed_candidates = [item for item in all_options if not item["valid"]]
    return {
        "project": project_dir.name,
        "valid": current["valid"],
        "score": current["score"],
        "blockers": current["blockers"],
        "warnings": current["warnings"],
        "levels": current["levels"],
        "metrics": current["metrics"],
        "current_params": current_params,
        "best_candidate": best,
        "candidate_count": len(candidates),
        "failed_candidates": failed_candidates,
        "next_actions": current["next_actions"] or ["no gait changes required for MVP gate"],
    }


def gait_score_report(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": payload["project"],
        "valid": payload["valid"],
        "score": payload["score"],
        "blockers": payload["blockers"],
        "warnings": payload["warnings"],
        "levels": payload["levels"],
        "metrics": payload["metrics"],
        "current_params": payload["current_params"],
        "best_candidate": payload["best_candidate"],
        "next_actions": payload["next_actions"],
    }


def best_gait_params_yaml(payload: dict[str, Any]) -> str:
    best = payload["best_candidate"]
    params = best.get("params", {})
    lines = [
        'version: "1.0"',
        f"name: {best.get('name', 'best_candidate')}",
        f"score: {best.get('score', 0)}",
        f"valid: {str(best.get('valid', False)).lower()}",
        "params:",
    ]
    for key, value in params.items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines) + "\n"


def trajectory_summary(payload: dict[str, Any]) -> dict[str, Any]:
    params = payload["best_candidate"].get("params", {})
    return {
        "project": payload["project"],
        "source": "gait_optimization_mvp",
        "candidate": payload["best_candidate"].get("name", "best_candidate"),
        "phase_pattern": params.get("phase_pattern", "trot"),
        "stride_mm": params.get("stride_mm"),
        "clearance_mm": params.get("clearance_mm"),
        "duty_factor": params.get("duty_factor"),
        "body_height_mm": params.get("body_height_mm"),
    }


def markdown_report(payload: dict[str, Any]) -> str:
    status = "PASS" if payload["valid"] else "FAIL"
    best = payload["best_candidate"]
    lines = [
        "# Gait Optimization Report",
        "",
        f"Project: {payload['project']}",
        f"Status: {status}",
        f"Current score: {payload['score']}",
        f"Best candidate: {best.get('name', 'best_candidate')} ({best.get('score', 0)})",
        "",
        "## Blockers",
    ]
    if payload["blockers"]:
        lines.extend(f"- {blocker}" for blocker in payload["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings"])
    if payload["warnings"]:
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    else:
        lines.append("- none")
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    return "\n".join(lines) + "\n"

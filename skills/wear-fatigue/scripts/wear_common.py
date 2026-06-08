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
    list_keys = {"gears", "bearings", "foot_pads", "joint_interfaces", "harnesses", "connectors"}
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


def _str_at(mapping: dict[str, Any], key: str, default: str) -> str:
    value = mapping.get(key, default)
    return str(value)


def load_wear_inputs(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "wear_inputs.yaml")


def _component_entry(component_type: str, component: dict[str, Any], valid: bool, blockers: list[str], warnings: list[str], metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": component_type,
        "name": _str_at(component, "name", "unnamed"),
        "valid": valid,
        "blockers": blockers,
        "warnings": warnings,
        "metrics": metrics,
    }


def evaluate_project(project_dir: Path) -> dict[str, Any]:
    data = load_wear_inputs(project_dir)
    target_hours = _float_at(data, "target_maintenance_hours", 50.0)
    project = _str_at(data, "project", project_dir.name)

    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []
    components: list[dict[str, Any]] = []

    for gear in data.get("gears", []) if isinstance(data.get("gears"), list) else []:
        component_blockers: list[str] = []
        component_warnings: list[str] = []
        name = _str_at(gear, "name", "unnamed_gear")
        stress = _float_at(gear, "contact_stress_mpa", 0.0)
        allowable = _float_at(gear, "allowable_contact_stress_mpa", 0.0)
        life = _float_at(gear, "estimated_life_hours", target_hours)
        stress_margin = ((allowable - stress) / allowable * 100.0) if allowable > 0 else 0.0
        if allowable > 0 and stress > allowable:
            component_blockers.append(f"{name} contact stress {stress:g}MPa above allowable {allowable:g}MPa")
            next_actions.append(f"increase reducer size, improve material, or reduce knee torque for {name}")
        elif stress_margin < 15.0:
            component_warnings.append(f"{name} gear contact stress margin is below 15%")
        if life < target_hours:
            component_blockers.append(f"{name} estimated gear life {life:g}h below target {target_hours:g}h")
            next_actions.append(f"reduce load or choose longer-life reducer for {name}")
        components.append(
            _component_entry(
                "gear",
                gear,
                not component_blockers,
                component_blockers,
                component_warnings,
                {
                    "contact_stress_mpa": stress,
                    "allowable_contact_stress_mpa": allowable,
                    "stress_margin_pct": round(stress_margin, 3),
                    "estimated_life_hours": life,
                    "pitch_line_velocity_mps": _float_at(gear, "pitch_line_velocity_mps", 0.0),
                    "lubrication": _str_at(gear, "lubrication", "unknown"),
                },
            )
        )
        blockers.extend(component_blockers)
        warnings.extend(component_warnings)

    for bearing in data.get("bearings", []) if isinstance(data.get("bearings"), list) else []:
        component_blockers = []
        component_warnings = []
        name = _str_at(bearing, "name", "unnamed_bearing")
        l10 = _float_at(bearing, "l10_life_hours", 0.0)
        radial = _float_at(bearing, "radial_load_n", 0.0)
        radial_limit = _float_at(bearing, "radial_load_limit_n", 0.0)
        axial = _float_at(bearing, "axial_load_n", 0.0)
        axial_limit = _float_at(bearing, "axial_load_limit_n", 0.0)
        mounting_error = _float_at(bearing, "mounting_error_deg", 0.0)
        mounting_limit = _float_at(bearing, "mounting_error_deg_max", 1.0)
        if l10 < target_hours:
            component_blockers.append(f"{name} bearing L10 life {l10:g}h below target {target_hours:g}h")
            next_actions.append(f"select larger bearing or reduce radial load for {name}")
        elif l10 < target_hours * 1.5:
            component_warnings.append(f"{name} bearing L10 life has low margin")
        if radial_limit > 0 and radial > radial_limit:
            component_blockers.append(f"{name} radial load {radial:g}N above limit {radial_limit:g}N")
            next_actions.append(f"add support or move load path closer to {name}")
        if axial_limit > 0 and axial > axial_limit:
            component_blockers.append(f"{name} axial load {axial:g}N above limit {axial_limit:g}N")
            next_actions.append(f"add thrust support for {name}")
        if mounting_error > mounting_limit:
            component_blockers.append(f"{name} mounting error {mounting_error:g}deg above {mounting_limit:g}deg")
            next_actions.append(f"tighten bearing seat alignment for {name}")
        components.append(
            _component_entry(
                "bearing",
                bearing,
                not component_blockers,
                component_blockers,
                component_warnings,
                {
                    "l10_life_hours": l10,
                    "radial_load_n": radial,
                    "radial_load_limit_n": radial_limit,
                    "axial_load_n": axial,
                    "axial_load_limit_n": axial_limit,
                    "rpm": _float_at(bearing, "rpm", 0.0),
                    "mounting_error_deg": mounting_error,
                    "mounting_error_deg_max": mounting_limit,
                },
            )
        )
        blockers.extend(component_blockers)
        warnings.extend(component_warnings)

    for foot in data.get("foot_pads", []) if isinstance(data.get("foot_pads"), list) else []:
        component_blockers = []
        component_warnings = []
        name = _str_at(foot, "name", "unnamed_foot_pad")
        life = _float_at(foot, "estimated_wear_life_hours", 0.0)
        replaceable = _bool_at(foot, "replaceable", False)
        friction = _float_at(foot, "friction_coefficient", 0.0)
        if life < target_hours:
            component_blockers.append(f"{name} foot pad wear life {life:g}h below target {target_hours:g}h")
            next_actions.append(f"change foot pad material or make {name} easy to replace")
        if not replaceable:
            component_blockers.append(f"{name} is not replaceable")
            next_actions.append(f"make {name} a replaceable wear item")
        if friction < 0.5:
            component_warnings.append(f"{name} friction coefficient may be low")
        components.append(
            _component_entry(
                "foot_pad",
                foot,
                not component_blockers,
                component_blockers,
                component_warnings,
                {
                    "estimated_wear_life_hours": life,
                    "impact_j": _float_at(foot, "impact_j", 0.0),
                    "friction_coefficient": friction,
                    "replaceable": replaceable,
                },
            )
        )
        blockers.extend(component_blockers)
        warnings.extend(component_warnings)

    for joint in data.get("joint_interfaces", []) if isinstance(data.get("joint_interfaces"), list) else []:
        component_blockers = []
        component_warnings = []
        name = _str_at(joint, "name", "unnamed_joint_interface")
        impact = _float_at(joint, "limit_impact_j", 0.0)
        impact_limit = _float_at(joint, "limit_impact_j_max", 0.0)
        loosening = _str_at(joint, "screw_loosening_risk", "unknown").lower()
        if impact_limit > 0 and impact > impact_limit:
            component_blockers.append(f"{name} limit impact {impact:g}J above {impact_limit:g}J")
            next_actions.append(f"add damping or soften joint limit stop for {name}")
        if loosening == "high":
            component_blockers.append(f"{name} screw loosening risk is high")
            next_actions.append(f"add threadlocker, locking nut, or preload control for {name}")
        elif loosening in {"medium", "moderate"}:
            component_warnings.append(f"{name} screw loosening risk should be reviewed")
        components.append(
            _component_entry(
                "joint_interface",
                joint,
                not component_blockers,
                component_blockers,
                component_warnings,
                {
                    "limit_impact_j": impact,
                    "limit_impact_j_max": impact_limit,
                    "screw_loosening_risk": loosening,
                },
            )
        )
        blockers.extend(component_blockers)
        warnings.extend(component_warnings)

    for harness in data.get("harnesses", []) if isinstance(data.get("harnesses"), list) else []:
        component_blockers = []
        component_warnings = []
        name = _str_at(harness, "name", "unnamed_harness")
        bend = _float_at(harness, "min_bend_radius_mm", 0.0)
        required = _float_at(harness, "required_bend_radius_mm", 0.0)
        envelope_clear = _bool_at(harness, "motion_envelope_clear", False)
        pinch = _bool_at(harness, "pinch_risk", True)
        if required > 0 and bend < required:
            component_blockers.append(f"{name} bend radius {bend:g}mm below required {required:g}mm")
            next_actions.append(f"reroute {name} or increase service loop radius")
        if not envelope_clear:
            component_blockers.append(f"{name} motion envelope is not clear")
            next_actions.append(f"move {name} outside leg sweep envelope")
        if pinch:
            component_blockers.append(f"{name} has pinch risk")
            next_actions.append(f"add clip, sleeve, or hard routing feature for {name}")
        components.append(
            _component_entry(
                "harness",
                harness,
                not component_blockers,
                component_blockers,
                component_warnings,
                {
                    "min_bend_radius_mm": bend,
                    "required_bend_radius_mm": required,
                    "motion_envelope_clear": envelope_clear,
                    "pinch_risk": pinch,
                },
            )
        )
        blockers.extend(component_blockers)
        warnings.extend(component_warnings)

    for connector in data.get("connectors", []) if isinstance(data.get("connectors"), list) else []:
        component_blockers = []
        component_warnings = []
        name = _str_at(connector, "name", "unnamed_connector")
        cycles = _float_at(connector, "mating_cycles", 0.0)
        cycles_min = _float_at(connector, "mating_cycles_min", 50.0)
        vibration_lock = _bool_at(connector, "vibration_lock", False)
        strain_relief = _bool_at(connector, "strain_relief", False)
        if cycles < cycles_min:
            component_blockers.append(f"{name} mating cycles {cycles:g} below target {cycles_min:g}")
            next_actions.append(f"choose connector with higher mating cycle rating for {name}")
        if not vibration_lock:
            component_blockers.append(f"{name} missing vibration lock")
            next_actions.append(f"add latch, retention clip, or locking connector for {name}")
        if not strain_relief:
            component_blockers.append(f"{name} missing strain relief")
            next_actions.append(f"add strain relief near {name}")
        components.append(
            _component_entry(
                "connector",
                connector,
                not component_blockers,
                component_blockers,
                component_warnings,
                {
                    "mating_cycles": cycles,
                    "mating_cycles_min": cycles_min,
                    "vibration_lock": vibration_lock,
                    "strain_relief": strain_relief,
                },
            )
        )
        blockers.extend(component_blockers)
        warnings.extend(component_warnings)

    service_lives = [
        float(component["metrics"][key])
        for component in components
        for key in ("estimated_life_hours", "l10_life_hours", "estimated_wear_life_hours")
        if key in component["metrics"]
    ]
    maintenance_interval = min(service_lives) if service_lives else target_hours
    valid_components = sum(1 for component in components if component["valid"])
    if not blockers and not next_actions:
        next_actions.append("no wear/fatigue changes required for MVP gate")

    return {
        "project": project,
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "summary": {
            "target_maintenance_hours": target_hours,
            "component_count": len(components),
            "valid_component_count": valid_components,
            "estimated_maintenance_interval_hours": round(maintenance_interval, 3),
            "blocker_count": len(blockers),
        },
        "components": components,
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def wear_report(payload: dict[str, Any]) -> dict[str, Any]:
    component_types = {"gear", "foot_pad", "harness", "connector"}
    return {
        "project": payload["project"],
        "valid": not any(component["blockers"] for component in payload["components"] if component["type"] in component_types),
        "summary": payload["summary"],
        "components": [component for component in payload["components"] if component["type"] in component_types],
        "blockers": [blocker for component in payload["components"] if component["type"] in component_types for blocker in component["blockers"]],
        "warnings": [warning for component in payload["components"] if component["type"] in component_types for warning in component["warnings"]],
        "next_actions": payload["next_actions"],
    }


def fatigue_report(payload: dict[str, Any]) -> dict[str, Any]:
    component_types = {"bearing", "joint_interface"}
    return {
        "project": payload["project"],
        "valid": not any(component["blockers"] for component in payload["components"] if component["type"] in component_types),
        "summary": payload["summary"],
        "components": [component for component in payload["components"] if component["type"] in component_types],
        "blockers": [blocker for component in payload["components"] if component["type"] in component_types for blocker in component["blockers"]],
        "warnings": [warning for component in payload["components"] if component["type"] in component_types for warning in component["warnings"]],
        "next_actions": payload["next_actions"],
    }


def maintenance_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Wear/Fatigue Maintenance Interval",
        "",
        f"Project: {payload['project']}",
        f"Status: {'PASS' if payload['valid'] else 'FAIL'}",
        f"Estimated maintenance interval: {payload['summary']['estimated_maintenance_interval_hours']:g} hours",
        f"Target maintenance interval: {payload['summary']['target_maintenance_hours']:g} hours",
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


def summary_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Wear/Fatigue Report",
        "",
        f"Project: {payload['project']}",
        f"Status: {'PASS' if payload['valid'] else 'FAIL'}",
        "",
        "## Components",
    ]
    for component in payload["components"]:
        lines.append(f"- {component['type']}: {component['name']} - {'PASS' if component['valid'] else 'FAIL'}")
    lines.extend(["", "## Blockers"])
    if payload["blockers"]:
        lines.extend(f"- {blocker}" for blocker in payload["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    return "\n".join(lines) + "\n"

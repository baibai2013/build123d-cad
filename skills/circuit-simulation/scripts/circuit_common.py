from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MIN_CURRENT_MARGIN_PCT = 20.0
MIN_BULK_CAP_UF = 1000.0


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
            if key.strip() in {"power_rails", "motor_drivers", "components"}:
                next_value = []
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


def load_circuit(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "circuit_requirements.yaml")


def _current_margin(limit: float, load: float) -> float:
    if limit <= 0:
        return -100.0
    return (limit - load) / limit * 100.0


def check_project(project_dir: Path) -> dict[str, Any]:
    data = load_circuit(project_dir)
    checks = data.get("checks", {}) if isinstance(data.get("checks"), dict) else {}
    battery = data.get("battery", {}) if isinstance(data.get("battery"), dict) else {}
    safety = data.get("safety", {}) if isinstance(data.get("safety"), dict) else {}
    rails = data.get("power_rails", []) if isinstance(data.get("power_rails"), list) else []
    drivers = data.get("motor_drivers", []) if isinstance(data.get("motor_drivers"), list) else []
    thermal_section = data.get("thermal", {}) if isinstance(data.get("thermal"), dict) else {}
    thermal_components = (
        thermal_section.get("components", []) if isinstance(thermal_section.get("components"), list) else []
    )

    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []

    erc_pass = _bool_at(checks, "erc_pass", True)
    drc_pass = _bool_at(checks, "drc_pass", True)
    if not erc_pass:
        blockers.append("ERC failed")
        next_actions.append("fix ERC errors before prototype gate")
    if not drc_pass:
        blockers.append("DRC failed")
        next_actions.append("fix DRC errors before prototype gate")

    voltage_nominal = _float_at(battery, "voltage_nominal_v", 24.0)
    battery_max_current = _float_at(battery, "max_current_a", 0.0)
    fuse_current = _float_at(battery, "fuse_current_a", 0.0)
    if fuse_current <= 0:
        blockers.append("battery fuse missing")
        next_actions.append("add appropriately rated battery fuse")
    elif battery_max_current and fuse_current > battery_max_current:
        blockers.append("battery fuse current exceeds battery max current")
        next_actions.append("reduce fuse rating or increase validated battery current capability")

    rail_reports: list[dict[str, Any]] = []
    total_rail_power_w = 0.0
    for raw in rails:
        rail = raw if isinstance(raw, dict) else {}
        name = str(rail.get("name", "unnamed_rail"))
        voltage = _float_at(rail, "voltage_v", 0.0)
        regulator_current = _float_at(rail, "regulator_current_a", 0.0)
        load_current = _float_at(rail, "load_current_a", 0.0)
        efficiency = _float_at(rail, "efficiency_pct", 85.0)
        margin = _current_margin(regulator_current, load_current)
        output_power = voltage * load_current
        input_power = output_power / max(0.01, efficiency / 100.0)
        total_rail_power_w += input_power
        rail_blockers: list[str] = []
        rail_warnings: list[str] = []
        if margin < MIN_CURRENT_MARGIN_PCT:
            rail_blockers.append(f"{name} current margin below 20%")
        if efficiency < 70:
            rail_warnings.append(f"{name} regulator efficiency below 70%")
        blockers.extend(rail_blockers)
        warnings.extend(rail_warnings)
        if rail_blockers:
            next_actions.append(f"increase {name} regulator rating or reduce load current")
        rail_reports.append(
            {
                "name": name,
                "voltage_v": voltage,
                "regulator_current_a": regulator_current,
                "load_current_a": load_current,
                "current_margin_pct": round(margin, 2),
                "efficiency_pct": efficiency,
                "estimated_input_power_w": round(input_power, 3),
                "valid": not rail_blockers,
                "blockers": rail_blockers,
                "warnings": rail_warnings,
            }
        )

    driver_reports: list[dict[str, Any]] = []
    total_motor_continuous_current = 0.0
    total_motor_peak_current = 0.0
    for raw in drivers:
        driver = raw if isinstance(raw, dict) else {}
        name = str(driver.get("name", "unnamed_driver"))
        count = int(_float_at(driver, "count", 1))
        peak = _float_at(driver, "peak_current_a_each", 0.0)
        continuous = _float_at(driver, "continuous_current_a_each", 0.0)
        peak_limit = _float_at(driver, "driver_peak_limit_a_each", 0.0)
        continuous_limit = _float_at(driver, "driver_continuous_limit_a_each", 0.0)
        peak_margin = _current_margin(peak_limit, peak)
        continuous_margin = _current_margin(continuous_limit, continuous)
        driver_blockers: list[str] = []
        if peak_margin < MIN_CURRENT_MARGIN_PCT:
            driver_blockers.append(f"{name} peak current margin below 20%")
        if continuous_margin < MIN_CURRENT_MARGIN_PCT:
            driver_blockers.append(f"{name} continuous current margin below 20%")
        blockers.extend(driver_blockers)
        if driver_blockers:
            next_actions.append(f"increase {name} driver current rating or reduce actuator current demand")
        total_motor_continuous_current += continuous * count
        total_motor_peak_current += peak * count
        driver_reports.append(
            {
                "name": name,
                "count": count,
                "peak_current_a_each": peak,
                "continuous_current_a_each": continuous,
                "driver_peak_limit_a_each": peak_limit,
                "driver_continuous_limit_a_each": continuous_limit,
                "peak_margin_pct": round(peak_margin, 2),
                "continuous_margin_pct": round(continuous_margin, 2),
                "valid": not driver_blockers,
                "blockers": driver_blockers,
            }
        )

    rail_current_from_battery = total_rail_power_w / max(1.0, voltage_nominal)
    estimated_continuous_battery_current = rail_current_from_battery + total_motor_continuous_current
    estimated_peak_battery_current = rail_current_from_battery + total_motor_peak_current
    battery_margin = _current_margin(battery_max_current, estimated_peak_battery_current)
    if battery_margin < MIN_CURRENT_MARGIN_PCT:
        blockers.append("battery peak current margin below 20%")
        next_actions.append("increase battery current rating or reduce simultaneous motor peak current")

    emergency_stop = _bool_at(safety, "emergency_stop", False)
    reverse_polarity = _bool_at(safety, "reverse_polarity_protection", False)
    undervoltage = _float_at(safety, "undervoltage_cutoff_v", 0.0)
    tvs = _bool_at(safety, "tvs_diode", False)
    bulk_cap = _float_at(safety, "bulk_capacitance_uf", 0.0)
    if not emergency_stop:
        blockers.append("emergency stop missing")
        next_actions.append("add emergency stop input or power cutoff path")
    if not reverse_polarity:
        warnings.append("reverse polarity protection missing")
    if undervoltage < voltage_nominal * 0.70:
        blockers.append("undervoltage cutoff below 70% of nominal battery voltage")
        next_actions.append("raise undervoltage cutoff to protect battery and controls")
    if not tvs:
        blockers.append("motor power TVS diode missing")
        next_actions.append("add TVS or transient suppression on motor power rail")
    if bulk_cap < MIN_BULK_CAP_UF:
        warnings.append("bulk capacitance below 1000 uF for motor-heavy design")

    ambient = _float_at(thermal_section, "ambient_c", 35.0)
    thermal_reports: list[dict[str, Any]] = []
    for raw in thermal_components:
        component = raw if isinstance(raw, dict) else {}
        name = str(component.get("name", "unnamed_component"))
        dissipation = _float_at(component, "dissipation_w", 0.0)
        resistance = _float_at(component, "thermal_resistance_c_w", 0.0)
        max_temp = _float_at(component, "max_temp_c", 85.0)
        estimated = ambient + dissipation * resistance
        thermal_blockers: list[str] = []
        thermal_warnings: list[str] = []
        if estimated > max_temp:
            thermal_blockers.append(f"{name} estimated temperature above limit")
        elif estimated > max_temp - 10:
            thermal_warnings.append(f"{name} estimated temperature within 10C of limit")
        blockers.extend(thermal_blockers)
        warnings.extend(thermal_warnings)
        if thermal_blockers:
            next_actions.append(f"reduce {name} dissipation or improve cooling")
        thermal_reports.append(
            {
                "name": name,
                "dissipation_w": dissipation,
                "thermal_resistance_c_w": resistance,
                "ambient_c": ambient,
                "estimated_temp_c": round(estimated, 2),
                "max_temp_c": max_temp,
                "valid": not thermal_blockers,
                "blockers": thermal_blockers,
                "warnings": thermal_warnings,
            }
        )

    if not blockers and not next_actions:
        next_actions.append("no circuit changes required for MVP gate")

    scores = {
        "erc_drc": 20 if erc_pass and drc_pass else 0,
        "power_budget": 25 if battery_margin >= MIN_CURRENT_MARGIN_PCT else 8,
        "rails": max(0, 20 - sum(len(item["blockers"]) for item in rail_reports) * 8),
        "protection": max(0, 20 - sum(1 for item in ["emergency_stop", "undervoltage", "tvs"] if item)),
        "thermal": max(0, 15 - sum(len(item["blockers"]) for item in thermal_reports) * 7),
    }
    protection_score = 20
    for condition in (emergency_stop, undervoltage >= voltage_nominal * 0.70, tvs, fuse_current > 0):
        if not condition:
            protection_score -= 5
    scores["protection"] = max(0, protection_score)

    return {
        "project": project_dir.name,
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "scores": scores,
        "total_score": sum(scores.values()),
        "checks": {"erc_pass": erc_pass, "drc_pass": drc_pass},
        "battery": {
            "voltage_nominal_v": voltage_nominal,
            "max_current_a": battery_max_current,
            "fuse_current_a": fuse_current,
            "estimated_continuous_current_a": round(estimated_continuous_battery_current, 3),
            "estimated_peak_current_a": round(estimated_peak_battery_current, 3),
            "peak_current_margin_pct": round(battery_margin, 2),
        },
        "power_rails": rail_reports,
        "motor_drivers": driver_reports,
        "thermal": {
            "ambient_c": ambient,
            "components": thermal_reports,
        },
        "protection": {
            "emergency_stop": emergency_stop,
            "reverse_polarity_protection": reverse_polarity,
            "undervoltage_cutoff_v": undervoltage,
            "tvs_diode": tvs,
            "bulk_capacitance_uf": bulk_cap,
        },
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def circuit_check_report(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": payload["project"],
        "valid": payload["valid"],
        "blockers": payload["blockers"],
        "warnings": payload["warnings"],
        "scores": payload["scores"],
        "checks": payload["checks"],
        "battery": payload["battery"],
        "protection": payload["protection"],
        "next_actions": payload["next_actions"],
    }


def power_budget_report(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": payload["project"],
        "valid": payload["valid"],
        "battery": payload["battery"],
        "power_rails": payload["power_rails"],
        "motor_drivers": payload["motor_drivers"],
        "blockers": [
            blocker
            for blocker in payload["blockers"]
            if "current" in blocker.lower() or "battery" in blocker.lower() or "rail" in blocker.lower()
        ],
    }


def thermal_report(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": payload["project"],
        "valid": all(component["valid"] for component in payload["thermal"]["components"]),
        "ambient_c": payload["thermal"]["ambient_c"],
        "components": payload["thermal"]["components"],
    }


def protection_checklist(payload: dict[str, Any]) -> str:
    protection = payload["protection"]
    lines = ["# Protection Checklist", ""]
    for key, value in protection.items():
        status = "PASS" if value else "FAIL"
        if isinstance(value, (int, float)) and key != "bulk_capacitance_uf":
            status = "PASS" if value > 0 else "FAIL"
        lines.append(f"- {key}: {status} ({value})")
    return "\n".join(lines) + "\n"


def markdown_report(payload: dict[str, Any]) -> str:
    status = "PASS" if payload["valid"] else "FAIL"
    lines = [
        "# Circuit Simulation Report",
        "",
        f"Project: {payload['project']}",
        f"Status: {status}",
        f"Total score: {payload['total_score']}",
        f"Battery peak current margin: {payload['battery']['peak_current_margin_pct']}%",
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

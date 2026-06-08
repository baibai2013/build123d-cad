from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


GRAVITY = 9.81
PCB_MODULUS_PA = 20_000_000_000.0
MIN_CLEARANCE_MM = 2.0
MIN_BOARD_THICKNESS_MM = 1.6
MIN_HOLE_EDGE_DISTANCE_MM = 3.0
MAX_UNSUPPORTED_SPAN_MM = 70.0
MAX_BOARD_FLEX_MM = 1.5


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
            # The MVP parser treats keys named "connectors" as lists.
            if key.strip() == "connectors":
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


def load_pcb_mechanical(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "pcb_mechanical.yaml")


def _required_holes(area_mm2: float) -> int:
    if area_mm2 > 9000:
        return 6
    if area_mm2 > 5000:
        return 4
    return 3


def _connector_support_limit(kind: str) -> float:
    return 25.0 if kind == "power" else 40.0


def estimate_board_flex_mm(board: dict[str, Any], mounting: dict[str, Any], loads: dict[str, Any]) -> float:
    width_m = _float_at(board, "width_mm", 60.0) / 1000.0
    thickness_m = _float_at(board, "thickness_mm", 1.6) / 1000.0
    mass_kg = _float_at(board, "mass_g", 30.0) / 1000.0
    vibration_g = max(1.0, _float_at(loads, "vibration_g", 3.0))
    span_m = _float_at(mounting, "max_unsupported_span_mm", 60.0) / 1000.0
    inertia = width_m * thickness_m**3 / 12.0
    load_n = mass_kg * GRAVITY * vibration_g
    if inertia <= 0:
        return math.inf
    return load_n * span_m**3 / (48.0 * PCB_MODULUS_PA * inertia) * 1000.0


def check_project(project_dir: Path) -> dict[str, Any]:
    data = load_pcb_mechanical(project_dir)
    board = data.get("board", {}) if isinstance(data.get("board"), dict) else {}
    mounting = data.get("mounting", {}) if isinstance(data.get("mounting"), dict) else {}
    loads = data.get("loads", {}) if isinstance(data.get("loads"), dict) else {}
    connectors = data.get("connectors", []) if isinstance(data.get("connectors"), list) else []

    width = _float_at(board, "width_mm", 60.0)
    length = _float_at(board, "length_mm", 80.0)
    thickness = _float_at(board, "thickness_mm", 1.6)
    area = width * length
    required_holes = _required_holes(area)
    hole_count = int(_float_at(mounting, "hole_count", 0))
    standoff_count = int(_float_at(mounting, "standoff_count", 0))
    hole_edge_distance = _float_at(mounting, "hole_edge_distance_mm", 0.0)
    unsupported_span = _float_at(mounting, "max_unsupported_span_mm", max(width, length))
    enclosure_clearance = _float_at(board, "enclosure_clearance_mm", 0.0)
    edge_clearance = _float_at(board, "edge_clearance_mm", 0.0)
    flex_mm = estimate_board_flex_mm(board, mounting, loads)

    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []

    if enclosure_clearance < MIN_CLEARANCE_MM:
        blockers.append("board enclosure clearance below 2 mm")
        next_actions.append("increase enclosure clearance or reduce connector height")
    if edge_clearance < MIN_CLEARANCE_MM:
        blockers.append("board edge clearance below 2 mm")
        next_actions.append("increase board-to-wall edge clearance")
    if thickness < MIN_BOARD_THICKNESS_MM:
        blockers.append("pcb thickness below 1.6 mm for robot-dog vibration")
        next_actions.append("use 1.6 mm or thicker PCB laminate")
    if hole_count < required_holes:
        blockers.append(f"mounting hole count {hole_count} below required {required_holes}")
        next_actions.append("add mounting holes near board corners and high-load connectors")
    if standoff_count < required_holes:
        blockers.append(f"standoff count {standoff_count} below required {required_holes}")
        next_actions.append("add standoffs to reduce unsupported board span")
    if hole_edge_distance < MIN_HOLE_EDGE_DISTANCE_MM:
        blockers.append("mounting hole edge distance below 3 mm")
        next_actions.append("move mounting holes farther from board edge")
    if unsupported_span > MAX_UNSUPPORTED_SPAN_MM:
        blockers.append("max unsupported PCB span above 70 mm")
        next_actions.append("add center standoff or shorten unsupported span")
    if flex_mm > MAX_BOARD_FLEX_MM:
        blockers.append("estimated board flex above 1.5 mm")
        next_actions.append("add standoff support or increase PCB thickness")

    connector_reports: list[dict[str, Any]] = []
    for raw in connectors:
        connector = raw if isinstance(raw, dict) else {}
        name = str(connector.get("name", "unnamed_connector"))
        kind = str(connector.get("kind", "signal"))
        clearance = _float_at(connector, "clearance_mm", 0.0)
        nearest_standoff = _float_at(connector, "nearest_standoff_mm", 999.0)
        support_limit = _connector_support_limit(kind)
        bend_radius = _float_at(connector, "cable_bend_radius_mm", 0.0)
        min_bend = _float_at(connector, "cable_min_bend_radius_mm", 0.0)
        strain_relief = _bool_at(connector, "strain_relief", False)
        connector_blockers: list[str] = []
        if clearance < MIN_CLEARANCE_MM:
            connector_blockers.append(f"{name} connector clearance below 2 mm")
        if nearest_standoff > support_limit:
            connector_blockers.append(f"{name} {kind} connector lacks nearby support")
        if min_bend and bend_radius < min_bend:
            connector_blockers.append(f"{name} cable bend radius below minimum")
        if kind == "power" and not strain_relief:
            connector_blockers.append(f"{name} power connector lacks strain relief")
        blockers.extend(connector_blockers)
        if connector_blockers:
            next_actions.append(f"revise {name} connector support, clearance, or cable routing")
        connector_reports.append(
            {
                "name": name,
                "kind": kind,
                "clearance_mm": round(clearance, 2),
                "nearest_standoff_mm": round(nearest_standoff, 2),
                "support_limit_mm": support_limit,
                "cable_bend_radius_mm": round(bend_radius, 2),
                "cable_min_bend_radius_mm": round(min_bend, 2),
                "strain_relief": strain_relief,
                "valid": not connector_blockers,
                "blockers": connector_blockers,
            }
        )

    if not blockers and not warnings:
        next_actions.append("no PCB mechanical changes required for MVP gate")

    scores = {
        "fit": 0 if enclosure_clearance < MIN_CLEARANCE_MM or edge_clearance < MIN_CLEARANCE_MM else 25,
        "mounting": max(0, 25 - max(0, required_holes - min(hole_count, standoff_count)) * 8),
        "stiffness": 25 if flex_mm <= MAX_BOARD_FLEX_MM and thickness >= MIN_BOARD_THICKNESS_MM else 8,
        "connectors": max(0, 25 - sum(len(item["blockers"]) for item in connector_reports) * 5),
    }

    return {
        "project": project_dir.name,
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "scores": scores,
        "total_score": sum(scores.values()),
        "board": {
            "name": board.get("name", "pcb"),
            "width_mm": width,
            "length_mm": length,
            "thickness_mm": thickness,
            "mass_g": _float_at(board, "mass_g", 30.0),
            "area_mm2": round(area, 2),
            "enclosure_clearance_mm": enclosure_clearance,
            "edge_clearance_mm": edge_clearance,
        },
        "mounting": {
            "hole_count": hole_count,
            "standoff_count": standoff_count,
            "required_support_count": required_holes,
            "hole_edge_distance_mm": hole_edge_distance,
            "max_unsupported_span_mm": unsupported_span,
        },
        "flex": {
            "estimated_board_flex_mm": round(flex_mm, 3),
            "limit_mm": MAX_BOARD_FLEX_MM,
            "model": "mvp_beam_approximation",
        },
        "connectors": connector_reports,
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def compact_fit_report(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": payload["project"],
        "valid": payload["valid"],
        "blockers": payload["blockers"],
        "scores": payload["scores"],
        "board": payload["board"],
        "mounting": payload["mounting"],
        "flex": payload["flex"],
        "next_actions": payload["next_actions"],
    }


def connector_clearance_report(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": payload["project"],
        "valid": all(connector["valid"] for connector in payload["connectors"]),
        "connectors": payload["connectors"],
    }


def markdown_report(payload: dict[str, Any]) -> str:
    status = "PASS" if payload["valid"] else "FAIL"
    lines = [
        "# PCB Mechanical Reliability Report",
        "",
        f"Project: {payload['project']}",
        f"Status: {status}",
        f"Total score: {payload['total_score']}",
        f"Estimated board flex: {payload['flex']['estimated_board_flex_mm']} mm",
        "",
        "## Blockers",
    ]
    if payload["blockers"]:
        lines.extend(f"- {blocker}" for blocker in payload["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Connector Checks"])
    for connector in payload["connectors"]:
        result = "PASS" if connector["valid"] else "FAIL"
        lines.append(f"- {connector['name']}: {result}")
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    return "\n".join(lines) + "\n"

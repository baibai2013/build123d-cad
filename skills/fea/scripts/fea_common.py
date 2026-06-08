from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_YIELD_MPA = {
    "petg": 45.0,
    "pla": 55.0,
    "nylon": 70.0,
    "aluminum_6061_t6": 275.0,
    "aluminum_7075_t6": 500.0,
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
            if key.strip() == "cases":
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


def load_fea_cases(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "fea_cases.yaml")


def evaluate_project(project_dir: Path) -> dict[str, Any]:
    data = load_fea_cases(project_dir)
    material = data.get("material", {}) if isinstance(data.get("material"), dict) else {}
    limits = data.get("global_limits", {}) if isinstance(data.get("global_limits"), dict) else {}
    cases = data.get("cases", []) if isinstance(data.get("cases"), list) else []

    material_name = str(material.get("name", "petg"))
    yield_strength = _float_at(material, "yield_strength_mpa", DEFAULT_YIELD_MPA.get(material_name.lower(), 45.0))
    sf_min = _float_at(limits, "safety_factor_min", 2.0)
    deflection_limit = _float_at(limits, "deflection_mm_max", 2.0)
    modal_ratio_min = _float_at(limits, "modal_ratio_min", 2.0)
    gait_hz = _float_at(limits, "gait_excitation_hz", 3.0)

    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []
    case_reports: list[dict[str, Any]] = []

    for raw in cases:
        case = raw if isinstance(raw, dict) else {}
        name = str(case.get("name", "unnamed_case"))
        part = str(case.get("part", "unknown_part"))
        max_stress = _float_at(case, "max_stress_mpa", 0.0)
        max_deflection = _float_at(case, "max_deflection_mm", 0.0)
        first_mode = _float_at(case, "first_mode_hz", 0.0)
        local_deflection_limit = _float_at(case, "deflection_mm_limit", deflection_limit)
        safety_factor = yield_strength / max_stress if max_stress > 0 else 999.0
        modal_ratio = first_mode / gait_hz if gait_hz > 0 else 999.0
        case_blockers: list[str] = []
        case_warnings: list[str] = []
        if safety_factor < sf_min:
            case_blockers.append(f"{name} safety factor {safety_factor:.2f} below {sf_min:g}")
            next_actions.append(f"increase section thickness or change material for {part}")
        elif safety_factor < sf_min * 1.25:
            case_warnings.append(f"{name} safety factor has low margin")
        if max_deflection > local_deflection_limit:
            case_blockers.append(f"{name} deflection {max_deflection:g}mm above {local_deflection_limit:g}mm")
            next_actions.append(f"add rib/support or shorten span for {part}")
        if modal_ratio < modal_ratio_min:
            case_blockers.append(f"{name} first modal ratio {modal_ratio:.2f} below {modal_ratio_min:g}")
            next_actions.append(f"stiffen {part} or move gait excitation away from first mode")
        blockers.extend(case_blockers)
        warnings.extend(case_warnings)
        case_reports.append(
            {
                "name": name,
                "part": part,
                "load_case": case.get("load_case", "unknown"),
                "max_stress_mpa": round(max_stress, 3),
                "yield_strength_mpa": round(yield_strength, 3),
                "safety_factor": round(safety_factor, 3),
                "safety_factor_min": sf_min,
                "max_deflection_mm": round(max_deflection, 3),
                "deflection_limit_mm": local_deflection_limit,
                "first_mode_hz": round(first_mode, 3),
                "gait_excitation_hz": gait_hz,
                "modal_ratio": round(modal_ratio, 3),
                "impact_factor": _float_at(case, "impact_factor", 1.0),
                "valid": not case_blockers,
                "blockers": case_blockers,
                "warnings": case_warnings,
            }
        )

    if not blockers and not next_actions:
        next_actions.append("no structural FEA changes required for MVP gate")

    valid_cases = sum(1 for item in case_reports if item["valid"])
    worst_safety = min((item["safety_factor"] for item in case_reports), default=999.0)
    max_deflection_seen = max((item["max_deflection_mm"] for item in case_reports), default=0.0)
    min_modal_ratio = min((item["modal_ratio"] for item in case_reports), default=999.0)

    return {
        "project": project_dir.name,
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "summary": {
            "material": material_name,
            "yield_strength_mpa": yield_strength,
            "case_count": len(case_reports),
            "valid_case_count": valid_cases,
            "worst_safety_factor": worst_safety,
            "max_deflection_mm": max_deflection_seen,
            "min_modal_ratio": min_modal_ratio,
        },
        "cases": case_reports,
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def static_case_report(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": payload["project"],
        "valid": payload["valid"],
        "summary": payload["summary"],
        "cases": payload["cases"],
    }


def checklist(payload: dict[str, Any]) -> str:
    lines = [
        "# FEA Checklist",
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

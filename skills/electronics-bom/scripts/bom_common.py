from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CATALOG: list[dict[str, Any]] = [
    {
        "category": "mcu",
        "mpn": "STM32G431CBT6",
        "manufacturer": "STMicroelectronics",
        "interfaces": ["can", "spi", "i2c", "uart", "pwm"],
        "gpio": 30,
        "package": "lqfp",
        "assembly_tier": "jlcpcb_basic",
        "stock_status": "catalog_ok",
        "lifecycle": "active",
        "notes": "motor-control friendly MCU with CAN and timers",
    },
    {
        "category": "mcu",
        "mpn": "ESP32-S3-WROOM-1",
        "manufacturer": "Espressif",
        "interfaces": ["spi", "i2c", "uart", "wifi"],
        "gpio": 36,
        "package": "module",
        "assembly_tier": "jlcpcb_extended",
        "stock_status": "catalog_ok",
        "lifecycle": "active",
        "notes": "wireless supervisor candidate, not preferred for hard real-time motor loops",
    },
    {
        "category": "motor_driver",
        "mpn": "DRV8313RHH",
        "manufacturer": "Texas Instruments",
        "interfaces": ["pwm"],
        "voltage_v": 60,
        "current_a": 2.5,
        "package": "htssop",
        "assembly_tier": "jlcpcb_extended",
        "stock_status": "catalog_ok",
        "lifecycle": "active",
        "notes": "small BLDC driver, low current for quadruped joints",
    },
    {
        "category": "motor_driver",
        "mpn": "TMC6300-LA",
        "manufacturer": "Analog Devices/Trinamic",
        "interfaces": ["pwm", "spi"],
        "voltage_v": 24,
        "current_a": 8,
        "package": "qfn",
        "assembly_tier": "jlcpcb_extended",
        "stock_status": "catalog_ok",
        "lifecycle": "active",
        "notes": "compact low-voltage 3-phase driver candidate",
    },
    {
        "category": "encoder",
        "mpn": "AS5047P",
        "manufacturer": "ams OSRAM",
        "interfaces": ["spi", "abi"],
        "package": "tssop",
        "assembly_tier": "jlcpcb_extended",
        "stock_status": "catalog_ok",
        "lifecycle": "active",
        "notes": "magnetic rotary encoder candidate for joints",
    },
    {
        "category": "imu",
        "mpn": "ICM-42688-P",
        "manufacturer": "TDK InvenSense",
        "interfaces": ["spi", "i2c"],
        "package": "lga",
        "assembly_tier": "jlcpcb_extended",
        "stock_status": "catalog_ok",
        "lifecycle": "active",
        "notes": "common 6-axis IMU candidate",
    },
    {
        "category": "buck_regulator",
        "mpn": "MP1584EN",
        "manufacturer": "Monolithic Power Systems",
        "interfaces": [],
        "voltage_v": 28,
        "current_a": 3,
        "package": "soic",
        "assembly_tier": "jlcpcb_basic",
        "stock_status": "catalog_ok",
        "lifecycle": "active",
        "notes": "common low-cost buck regulator candidate",
    },
    {
        "category": "battery_connector",
        "mpn": "XT30PW-M",
        "manufacturer": "AMASS",
        "interfaces": [],
        "current_a": 30,
        "package": "through_hole",
        "assembly_tier": "manual",
        "stock_status": "catalog_ok",
        "lifecycle": "active",
        "notes": "right-angle battery connector candidate",
    },
]


def project_path(raw: str | Path) -> Path:
    return Path(raw).expanduser().resolve()


def reports_dir(project_dir: Path) -> Path:
    return project_dir / "reports"


def library_dir(project_dir: Path) -> Path:
    return project_dir / "electrical" / "library"


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
    list_keys = {"requirements"}
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


def load_bom_request(project_dir: Path) -> dict[str, Any]:
    return load_simple_yaml(project_dir / "bom_request.yaml")


def _constraints(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("constraints", {}) if isinstance(data.get("constraints"), dict) else {}


def _candidate_score(requirement: dict[str, Any], candidate: dict[str, Any], assembly_preference: str, package_preference: str) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    interface = str(requirement.get("interface", ""))
    if interface and interface in candidate.get("interfaces", []):
        score += 20
        reasons.append(f"matches interface {interface}")
    min_voltage = _float_at(requirement, "min_voltage_v", 0.0)
    if min_voltage:
        voltage = _float_at(candidate, "voltage_v", 0.0)
        if voltage >= min_voltage:
            score += 20
            reasons.append(f"voltage {voltage:g}V >= {min_voltage:g}V")
        else:
            score -= 100
            reasons.append(f"voltage {voltage:g}V below {min_voltage:g}V")
    min_current = _float_at(requirement, "min_current_a", 0.0)
    if min_current:
        current = _float_at(candidate, "current_a", 0.0)
        if current >= min_current:
            score += 20
            reasons.append(f"current {current:g}A >= {min_current:g}A")
        else:
            score -= 100
            reasons.append(f"current {current:g}A below {min_current:g}A")
    min_gpio = _float_at(requirement, "min_gpio", 0.0)
    if min_gpio:
        gpio = _float_at(candidate, "gpio", 0.0)
        if gpio >= min_gpio:
            score += 10
            reasons.append(f"gpio {gpio:g} >= {min_gpio:g}")
        else:
            score -= 50
            reasons.append(f"gpio {gpio:g} below {min_gpio:g}")
    package = str(requirement.get("package", package_preference))
    if package and package == str(candidate.get("package", "")):
        score += 8
        reasons.append(f"matches package {package}")
    if str(candidate.get("assembly_tier", "")) == assembly_preference:
        score += 8
        reasons.append(f"matches assembly preference {assembly_preference}")
    if str(candidate.get("lifecycle", "")) == "active":
        score += 5
    if str(candidate.get("stock_status", "")) == "catalog_ok":
        score += 5
    return score, reasons


def select_parts(project_dir: Path) -> dict[str, Any]:
    data = load_bom_request(project_dir)
    project = str(data.get("project", project_dir.name))
    constraints = _constraints(data)
    assembly_preference = str(constraints.get("assembly_preference", "jlcpcb_basic"))
    package_preference = str(constraints.get("package_preference", "smd"))
    requirements = data.get("requirements", []) if isinstance(data.get("requirements"), list) else []

    blockers: list[str] = []
    warnings: list[str] = ["offline catalog mode: stock and price are not live"]
    selected_parts: list[dict[str, Any]] = []
    next_actions: list[str] = []

    for requirement in requirements:
        category = str(requirement.get("category", "unknown"))
        required = _bool_at(requirement, "required", True)
        quantity = int(_float_at(requirement, "quantity", 1))
        candidates = [candidate for candidate in CATALOG if candidate["category"] == category]
        ranked = []
        for candidate in candidates:
            score, reasons = _candidate_score(requirement, candidate, assembly_preference, package_preference)
            ranked.append((score, candidate, reasons))
        ranked.sort(key=lambda item: item[0], reverse=True)
        if not ranked:
            message = f"no candidate found for category {category}"
            if required:
                blockers.append(message)
            else:
                warnings.append(message)
            next_actions.append(f"add curated catalog entry or live lookup for {category}")
            continue
        score, candidate, reasons = ranked[0]
        entry_blockers: list[str] = []
        if score < 0:
            entry_blockers.append(f"best {category} candidate {candidate['mpn']} does not meet required constraints")
            next_actions.append(f"select higher rated {category} part or relax constraints")
        if candidate.get("stock_status") == "unavailable" or candidate.get("lifecycle") == "obsolete":
            entry_blockers.append(f"{candidate['mpn']} is unavailable or obsolete")
            next_actions.append(f"replace {candidate['mpn']} before PCB freeze")
        if candidate.get("assembly_tier") != "jlcpcb_basic":
            warnings.append(f"{candidate['mpn']} is not JLCPCB basic tier")
        if entry_blockers and required:
            blockers.extend(entry_blockers)
        else:
            warnings.extend(entry_blockers)
        selected_parts.append(
            {
                "category": category,
                "quantity": quantity,
                "required": required,
                "mpn": candidate["mpn"],
                "manufacturer": candidate["manufacturer"],
                "package": candidate["package"],
                "assembly_tier": candidate["assembly_tier"],
                "stock_status": candidate["stock_status"],
                "lifecycle": candidate["lifecycle"],
                "score": score,
                "reasons": reasons,
                "notes": candidate["notes"],
                "valid": not entry_blockers,
            }
        )

    if not blockers and not next_actions:
        next_actions.append("no BOM changes required before PCB MVP")

    return {
        "project": project,
        "valid": not blockers,
        "mode": "offline_curated_catalog",
        "blockers": blockers,
        "warnings": list(dict.fromkeys(warnings)),
        "summary": {
            "requirement_count": len(requirements),
            "selected_count": len(selected_parts),
            "assembly_preference": assembly_preference,
        },
        "selected_parts": selected_parts,
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def selected_parts_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": payload["project"],
        "mode": payload["mode"],
        "selected_parts": payload["selected_parts"],
    }


def availability(payload: dict[str, Any]) -> dict[str, Any]:
    blockers = [
        f"{part['mpn']} has invalid availability"
        for part in payload["selected_parts"]
        if part["stock_status"] == "unavailable" or part["lifecycle"] == "obsolete"
    ]
    warnings = [f"{part['mpn']} requires live stock verification" for part in payload["selected_parts"]]
    return {
        "project": payload["project"],
        "valid": not blockers,
        "mode": payload["mode"],
        "blockers": blockers,
        "warnings": warnings,
        "parts": [
            {
                "mpn": part["mpn"],
                "category": part["category"],
                "stock_status": part["stock_status"],
                "lifecycle": part["lifecycle"],
                "assembly_tier": part["assembly_tier"],
            }
            for part in payload["selected_parts"]
        ],
    }


def rationale_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Electronics BOM Selection Rationale",
        "",
        f"Project: {payload['project']}",
        f"Status: {'PASS' if payload['valid'] else 'FAIL'}",
        f"Mode: {payload['mode']}",
        "",
        "## Selected Parts",
    ]
    for part in payload["selected_parts"]:
        lines.append(f"- {part['category']}: {part['mpn']} x{part['quantity']} ({part['assembly_tier']})")
    lines.extend(["", "## Blockers"])
    if payload["blockers"]:
        lines.extend(f"- {blocker}" for blocker in payload["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    return "\n".join(lines) + "\n"

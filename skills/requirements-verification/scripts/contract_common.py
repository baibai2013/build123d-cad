from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_REQUIREMENT_KEYS = ("version", "project", "targets", "constraints")
REQUIRED_TARGETS = ("mass_kg", "payload_kg", "runtime_min", "flat_walk_speed_mps")
REQUIRED_ARCHITECTURE_KEYS = ("version", "system", "domains")
PASS_CONDITION_KEYS = ("required", "limit_min", "limit_max", "equals")


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
    """Parse the small YAML subset used by this skill without third-party deps."""
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
        key = key.strip()
        if not key:
            raise ValueError(f"{path}:{lineno}: empty key")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if raw_value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(raw_value)
    return root


def reports_dir(project_dir: Path) -> Path:
    return project_dir / "reports"


def validate_requirements(project_dir: Path) -> list[str]:
    errors: list[str] = []
    path = project_dir / "requirements.yaml"
    try:
        data = load_simple_yaml(path)
    except FileNotFoundError:
        return ["missing requirements.yaml"]
    except ValueError as exc:
        return [str(exc)]

    for key in REQUIRED_REQUIREMENT_KEYS:
        if key not in data:
            errors.append(f"requirements.yaml missing {key}")
    targets = data.get("targets")
    if not isinstance(targets, dict):
        errors.append("requirements.yaml targets must be a mapping")
        return errors
    for key in REQUIRED_TARGETS:
        if key not in targets:
            errors.append(f"requirements.yaml targets missing {key}")
        elif targets[key] is None:
            errors.append(f"requirements.yaml targets.{key} is null")
    return errors


def validate_architecture(project_dir: Path) -> list[str]:
    errors: list[str] = []
    path = project_dir / "architecture.yaml"
    try:
        data = load_simple_yaml(path)
    except FileNotFoundError:
        return ["missing architecture.yaml"]
    except ValueError as exc:
        return [str(exc)]
    for key in REQUIRED_ARCHITECTURE_KEYS:
        if key not in data:
            errors.append(f"architecture.yaml missing {key}")
    return errors


def validate_matrix(project_dir: Path) -> list[str]:
    errors: list[str] = []
    path = project_dir / "verification_matrix.yaml"
    try:
        data = load_simple_yaml(path)
    except FileNotFoundError:
        return ["missing verification_matrix.yaml"]
    except ValueError as exc:
        return [str(exc)]
    if not data:
        return ["verification_matrix.yaml is empty"]

    for domain, checks in data.items():
        if not isinstance(checks, dict):
            errors.append(f"verification_matrix.yaml {domain} must be a mapping")
            continue
        for check_name, check in checks.items():
            label = f"{domain}.{check_name}"
            if not isinstance(check, dict):
                errors.append(f"verification_matrix.yaml {label} must be a mapping")
                continue
            if "source" not in check:
                errors.append(f"verification_matrix.yaml {label} missing source")
            if not any(key in check for key in PASS_CONDITION_KEYS):
                errors.append(f"verification_matrix.yaml {label} missing pass condition")
            if check.get("blocker") is True and "artifact" not in check:
                errors.append(f"verification_matrix.yaml {label} blocker missing artifact")
    return errors


def validate_contract(project_dir: Path) -> dict[str, Any]:
    sections = {
        "requirements": validate_requirements(project_dir),
        "verification_matrix": validate_matrix(project_dir),
        "architecture": validate_architecture(project_dir),
    }
    errors = [error for section_errors in sections.values() for error in section_errors]
    risk_register_exists = (project_dir / "risk_register.md").exists()
    warnings = [] if risk_register_exists else ["missing risk_register.md"]
    return {
        "project": project_dir.name,
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "sections": sections,
        "inputs": {
            "requirements": str(project_dir / "requirements.yaml"),
            "verification_matrix": str(project_dir / "verification_matrix.yaml"),
            "architecture": str(project_dir / "architecture.yaml"),
            "risk_register": str(project_dir / "risk_register.md"),
        },
    }


def markdown_report(payload: dict[str, Any]) -> str:
    status = "PASS" if payload["valid"] else "FAIL"
    lines = [
        "# Requirements Validation",
        "",
        f"Project: {payload['project']}",
        f"Status: {status}",
        "",
        "## Errors",
    ]
    if payload["errors"]:
        lines.extend(f"- {error}" for error in payload["errors"])
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings"])
    if payload["warnings"]:
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"

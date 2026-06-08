from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DOMAIN_WEIGHTS = {
    "mechanical": 20,
    "pcb_reliability": 15,
    "electrical": 20,
    "dynamics": 20,
    "gait": 15,
    "manufacturability": 10,
}

PROTOTYPE_SCORE_THRESHOLD = 85


def project_path(raw: str | Path) -> Path:
    path = Path(raw).expanduser()
    return path.resolve()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def read_yaml_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def reports_dir(project_dir: Path) -> Path:
    return project_dir / "reports"


def artifact_exists(project_dir: Path, rel_path: str) -> bool:
    return bool(rel_path) and (project_dir / rel_path).exists()


def load_artifacts(project_dir: Path) -> dict[str, Any]:
    data = read_json(project_dir / "artifacts.json", default={})
    return data if isinstance(data, dict) else {}


def load_collected(project_dir: Path) -> dict[str, Any]:
    collected = read_json(reports_dir(project_dir) / "artifacts.collected.json", default=None)
    if isinstance(collected, dict):
        return collected
    return collect_artifacts_payload(project_dir)


def collect_artifacts_payload(project_dir: Path) -> dict[str, Any]:
    declared = load_artifacts(project_dir)
    artifacts = declared.get("artifacts", declared)
    domains: dict[str, dict[str, Any]] = {}
    missing: list[dict[str, str]] = []

    if not isinstance(artifacts, dict):
        artifacts = {}

    for domain, entries in artifacts.items():
        domain_entries: dict[str, Any] = {}
        if isinstance(entries, dict):
            iterator = entries.items()
        else:
            iterator = []
        for name, rel_path in iterator:
            if not isinstance(rel_path, str):
                domain_entries[str(name)] = {"path": rel_path, "exists": False}
                missing.append({"domain": str(domain), "name": str(name), "path": str(rel_path)})
                continue
            exists = artifact_exists(project_dir, rel_path)
            domain_entries[str(name)] = {"path": rel_path, "exists": exists}
            if not exists:
                missing.append({"domain": str(domain), "name": str(name), "path": rel_path})
        domains[str(domain)] = domain_entries

    return {
        "project": project_dir.name,
        "requirements_exists": (project_dir / "requirements.yaml").exists(),
        "verification_matrix_exists": (project_dir / "verification_matrix.yaml").exists(),
        "architecture_exists": (project_dir / "architecture.yaml").exists(),
        "domains": domains,
        "missing": missing,
    }


def load_domain_report(project_dir: Path, collected: dict[str, Any], domain: str, name: str) -> dict[str, Any]:
    entry = collected.get("domains", {}).get(domain, {}).get(name, {})
    if not isinstance(entry, dict) or not entry.get("exists"):
        return {}
    rel_path = entry.get("path")
    if not isinstance(rel_path, str):
        return {}
    payload = read_json(project_dir / rel_path, default={})
    return payload if isinstance(payload, dict) else {}


def normalize_bool(value: Any) -> bool:
    return bool(value) if value is not None else False


def report_blockers(report: dict[str, Any]) -> list[str]:
    blockers = report.get("blockers", [])
    if isinstance(blockers, list):
        return [str(item) for item in blockers]
    return []


def score_from_checks(report: dict[str, Any], checks: list[tuple[str, int]]) -> tuple[int, list[str]]:
    score = 0
    blockers = report_blockers(report)
    for key, points in checks:
        if normalize_bool(report.get(key)):
            score += points
    if blockers:
        score = max(0, score - min(score, 5 * len(blockers)))
    return score, blockers


def compute_design_score(project_dir: Path) -> dict[str, Any]:
    collected = load_collected(project_dir)
    mechanical = load_domain_report(project_dir, collected, "mechanical", "collision_report")
    mass = load_domain_report(project_dir, collected, "mechanical", "mass_properties")
    pcb_fit = load_domain_report(project_dir, collected, "electrical", "pcb_fit")
    circuit = load_domain_report(project_dir, collected, "electrical", "circuit_check")
    power = load_domain_report(project_dir, collected, "electrical", "power_budget")
    stand = load_domain_report(project_dir, collected, "simulation", "stand_result")
    flat_walk = load_domain_report(project_dir, collected, "simulation", "flat_walk_result")
    gait = load_domain_report(project_dir, collected, "control", "gait_score")

    scores: dict[str, int] = {}
    all_blockers: list[str] = []

    mechanical_score = 0
    if mechanical.get("no_assembly_interference"):
        mechanical_score += 10
    if mass.get("mass_within_target"):
        mechanical_score += 5
    if mass.get("center_of_mass_ok"):
        mechanical_score += 5
    all_blockers.extend(report_blockers(mechanical))
    scores["mechanical"] = min(DOMAIN_WEIGHTS["mechanical"], mechanical_score)

    pcb_score, blockers = score_from_checks(
        pcb_fit,
        [("connector_clearance_ok", 5), ("standoffs_ok", 5), ("board_flex_risk_ok", 5)],
    )
    all_blockers.extend(blockers)
    scores["pcb_reliability"] = min(DOMAIN_WEIGHTS["pcb_reliability"], pcb_score)

    electrical_score = 0
    if circuit.get("erc_pass"):
        electrical_score += 5
    if circuit.get("drc_pass"):
        electrical_score += 5
    if power.get("power_budget_margin_pct", 0) >= 20:
        electrical_score += 5
    if circuit.get("thermal_risk_ok"):
        electrical_score += 5
    all_blockers.extend(report_blockers(circuit))
    all_blockers.extend(report_blockers(power))
    scores["electrical"] = min(DOMAIN_WEIGHTS["electrical"], electrical_score)

    dynamics_score = 0
    if stand.get("stable_seconds", 0) >= 30:
        dynamics_score += 10
    if flat_walk.get("no_fall"):
        dynamics_score += 5
    if min(stand.get("joint_torque_margin_pct", 100), flat_walk.get("joint_torque_margin_pct", 100)) >= 20:
        dynamics_score += 5
    all_blockers.extend(report_blockers(stand))
    all_blockers.extend(report_blockers(flat_walk))
    scores["dynamics"] = min(DOMAIN_WEIGHTS["dynamics"], dynamics_score)

    gait_score = 0
    if gait.get("flat_walk_no_fall"):
        gait_score += 5
    if gait.get("body_attitude_ok"):
        gait_score += 5
    if gait.get("foot_slip_ratio", 1.0) <= 0.12:
        gait_score += 3
    if gait.get("average_speed_mps", 0) >= 0.5:
        gait_score += 2
    all_blockers.extend(report_blockers(gait))
    scores["gait"] = min(DOMAIN_WEIGHTS["gait"], gait_score)

    manufacturing_score = 10 if collected.get("domains", {}).get("manufacturing") else 0
    scores["manufacturability"] = manufacturing_score

    missing = collected.get("missing", [])
    if missing:
        all_blockers.extend(f"missing artifact: {item.get('domain')}.{item.get('name')}" for item in missing)

    total = int(sum(scores.values()))
    unique_blockers = sorted(set(all_blockers))
    return {
        "version": project_dir.name,
        "total_score": total,
        "threshold": PROTOTYPE_SCORE_THRESHOLD,
        "prototype_allowed": total >= PROTOTYPE_SCORE_THRESHOLD and not unique_blockers,
        "scores": scores,
        "blockers": unique_blockers,
        "weights": DOMAIN_WEIGHTS,
    }


def gate_requirements(project_dir: Path, collected: dict[str, Any]) -> list[str]:
    failures = []
    if not collected.get("requirements_exists"):
        failures.append("missing_requirements")
    if not collected.get("verification_matrix_exists"):
        failures.append("missing_verification_matrix")
    return failures


def gate_failures(project_dir: Path, gate: str) -> list[str]:
    collected = load_collected(project_dir)
    score = compute_design_score(project_dir)
    domains = collected.get("domains", {})
    failures: list[str] = []

    if gate in {"G0", "G1", "G2", "G3", "G4", "G5"}:
        failures.extend(gate_requirements(project_dir, collected))
    if gate in {"G1", "G2", "G3", "G4", "G5"} and not collected.get("architecture_exists"):
        failures.append("missing_architecture")
    if gate in {"G2", "G3", "G4", "G5"}:
        required_pairs = [
            ("mechanical", "collision_report"),
            ("electrical", "pcb_fit"),
            ("electrical", "circuit_check"),
            ("simulation", "stand_result"),
            ("control", "gait_score"),
        ]
        for domain, name in required_pairs:
            if not domains.get(domain, {}).get(name, {}).get("exists"):
                failures.append(f"missing_artifact:{domain}.{name}")
    if gate in {"G3", "G4", "G5"}:
        failures.extend(score["blockers"])
    if gate in {"G4", "G5"}:
        if score["total_score"] < PROTOTYPE_SCORE_THRESHOLD:
            failures.append("score_below_threshold")
    if gate == "G5":
        if not domains.get("manufacturing"):
            failures.append("missing_manufacturing_pack")
    return sorted(set(failures))


def gate_report(project_dir: Path, gate: str) -> dict[str, Any]:
    normalized = gate.upper()
    failures = gate_failures(project_dir, normalized)
    return {
        "gate": normalized,
        "passed": not failures,
        "blocking_failures": failures,
        "design_score": compute_design_score(project_dir),
    }


def next_actions_from_score(score: dict[str, Any]) -> list[str]:
    blockers = score.get("blockers", [])
    actions: list[str] = []
    joined = " ".join(blockers)
    if "torque" in joined or "joint" in joined:
        actions.append("increase actuator torque margin or reduce gait stride/body height")
    if "pcb" in joined or "connector" in joined:
        actions.append("add PCB standoff near high-load connector and improve connector clearance")
    if "fall" in joined or "walk" in joined:
        actions.append("reduce trot stride and rerun flat_walk scenario")
    if "missing artifact" in joined:
        actions.append("generate missing domain artifacts before rerunning gates")
    if not actions:
        actions.append("review lowest scoring domain and improve its input artifact")
    return actions

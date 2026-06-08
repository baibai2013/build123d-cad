#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from digital_twin_common import gate_report, project_path, reports_dir, write_json, write_text


GATE_NAMES = {
    "G0": "requirements_ready",
    "G1": "virtual_architecture_ready",
    "G2": "digital_prototype_ready",
    "G3": "multi_domain_validation_passed",
    "G4": "iteration_score_passed",
    "G5": "physical_prototype_allowed",
}


def markdown_report(payload: dict[str, object]) -> str:
    gate = str(payload["gate"])
    status = "PASS" if payload["passed"] else "FAIL"
    failures = payload.get("blocking_failures", [])
    lines = [
        f"# Gate {gate}: {GATE_NAMES.get(gate, gate)}",
        "",
        f"Status: {status}",
        "",
        "## Blocking Failures",
    ]
    if failures:
        lines.extend(f"- {failure}" for failure in failures)
    else:
        lines.append("- none")
    score = payload.get("design_score", {})
    if isinstance(score, dict):
        lines.extend(["", "## Design Score", "", f"Total: {score.get('total_score')}"])
    return "\n".join(lines) + "\n"


def run(project_dir: Path, gate: str) -> dict[str, object]:
    payload = gate_report(project_dir, gate)
    report_dir = reports_dir(project_dir)
    write_json(report_dir / "gate_report.json", payload)
    write_text(report_dir / "gate_report.md", markdown_report(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a robot dog digital-twin gate.")
    parser.add_argument("project_dir", help="Project directory containing digital-twin artifacts")
    parser.add_argument("--gate", default="G3", choices=sorted(GATE_NAMES), help="Gate to evaluate")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir), args.gate)
    print(f"{payload['gate']} passed={payload['passed']}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

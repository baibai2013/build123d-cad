#!/usr/bin/env python3
from __future__ import annotations

import argparse

from circuit_common import (
    check_project,
    circuit_check_report,
    markdown_report,
    power_budget_report,
    project_path,
    protection_checklist,
    reports_dir,
    thermal_report,
    write_json,
    write_text,
)


def run(project_dir):
    payload = check_project(project_dir)
    report_dir = reports_dir(project_dir)
    write_json(report_dir / "circuit_check.json", circuit_check_report(payload))
    write_json(report_dir / "power_budget.json", power_budget_report(payload))
    write_json(report_dir / "thermal_report.json", thermal_report(payload))
    write_text(report_dir / "protection_checklist.md", protection_checklist(payload))
    write_text(report_dir / "circuit_simulation_report.md", markdown_report(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Check circuit power budget, protection, and thermal risk.")
    parser.add_argument("project_dir", help="Project directory containing circuit_requirements.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    print(f"circuit valid={payload['valid']} blockers={len(payload['blockers'])}")
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

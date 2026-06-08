#!/usr/bin/env python3
from __future__ import annotations

import argparse

from fea_common import checklist, evaluate_project, project_path, reports_dir, static_case_report, write_json, write_text


def run(project_dir):
    payload = evaluate_project(project_dir)
    report_dir = reports_dir(project_dir)
    write_json(report_dir / "fea_report.json", payload)
    write_json(report_dir / "static_case_report.json", static_case_report(payload))
    write_text(report_dir / "fea_checklist.md", checklist(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate structural FEA metadata cases.")
    parser.add_argument("project_dir", help="Project directory containing fea_cases.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    print(f"fea valid={payload['valid']} blockers={len(payload['blockers'])}")
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

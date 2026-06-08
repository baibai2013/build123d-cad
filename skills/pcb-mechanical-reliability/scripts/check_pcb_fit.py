#!/usr/bin/env python3
from __future__ import annotations

import argparse

from pcb_mech_common import (
    check_project,
    compact_fit_report,
    connector_clearance_report,
    markdown_report,
    project_path,
    reports_dir,
    write_json,
    write_text,
)


def run(project_dir):
    payload = check_project(project_dir)
    report_dir = reports_dir(project_dir)
    write_json(report_dir / "pcb_fit.json", compact_fit_report(payload))
    reliability = dict(payload)
    reliability["domain"] = "pcb_mechanical_reliability"
    write_json(report_dir / "pcb_reliability_report.json", reliability)
    write_json(report_dir / "connector_clearance.json", connector_clearance_report(payload))
    write_text(report_dir / "pcb_mechanical_report.md", markdown_report(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Check PCB mechanical fit and reliability risks.")
    parser.add_argument("project_dir", help="Project directory containing pcb_mechanical.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    print(f"pcb mechanical valid={payload['valid']} blockers={len(payload['blockers'])}")
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse

from pcb_mech_common import check_project, markdown_report, project_path, reports_dir, write_text


def run(project_dir):
    payload = check_project(project_dir)
    write_text(reports_dir(project_dir) / "pcb_mechanical_report.md", markdown_report(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Write PCB mechanical reliability markdown report.")
    parser.add_argument("project_dir", help="Project directory containing pcb_mechanical.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    print(f"wrote pcb mechanical report valid={payload['valid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

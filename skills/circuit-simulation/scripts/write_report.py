#!/usr/bin/env python3
from __future__ import annotations

import argparse

from circuit_common import check_project, markdown_report, project_path, reports_dir, write_text


def run(project_dir):
    payload = check_project(project_dir)
    write_text(reports_dir(project_dir) / "circuit_simulation_report.md", markdown_report(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Write circuit simulation markdown report.")
    parser.add_argument("project_dir", help="Project directory containing circuit_requirements.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    print(f"wrote circuit simulation report valid={payload['valid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

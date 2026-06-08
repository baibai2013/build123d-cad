#!/usr/bin/env python3
from __future__ import annotations

import argparse

from fea_common import checklist, evaluate_project, project_path, reports_dir, write_text


def run(project_dir):
    payload = evaluate_project(project_dir)
    write_text(reports_dir(project_dir) / "fea_checklist.md", checklist(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Write FEA checklist markdown summary.")
    parser.add_argument("project_dir", help="Project directory containing fea_cases.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    print(f"wrote fea checklist valid={payload['valid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

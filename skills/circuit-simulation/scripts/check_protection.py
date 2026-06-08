#!/usr/bin/env python3
from __future__ import annotations

import argparse

from circuit_common import check_project, project_path, protection_checklist, reports_dir, write_text


def run(project_dir):
    payload = check_project(project_dir)
    write_text(reports_dir(project_dir) / "protection_checklist.md", protection_checklist(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Write circuit protection checklist.")
    parser.add_argument("project_dir", help="Project directory containing circuit_requirements.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    print(f"wrote protection checklist valid={payload['valid']}")
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

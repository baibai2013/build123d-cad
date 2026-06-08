#!/usr/bin/env python3
from __future__ import annotations

import argparse

from actuator_common import estimate_payload, markdown_report, project_path, reports_dir, write_text


def run(project_dir):
    payload = estimate_payload(project_dir)
    out = reports_dir(project_dir) / "actuator_sizing_report.md"
    write_text(out, markdown_report(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Write actuator sizing markdown report.")
    parser.add_argument("project_dir", help="Project directory containing requirements.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    print(f"wrote actuator report valid={payload['valid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

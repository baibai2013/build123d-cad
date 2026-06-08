#!/usr/bin/env python3
from __future__ import annotations

import argparse

from actuator_common import (
    actuator_spec_yaml,
    estimate_payload,
    markdown_report,
    project_path,
    reports_dir,
    write_json,
    write_text,
)


def run(project_dir):
    payload = estimate_payload(project_dir)
    report_dir = reports_dir(project_dir)
    write_json(report_dir / "torque_margin.json", payload)
    write_text(report_dir / "actuator_spec.yaml", actuator_spec_yaml(payload))
    write_text(report_dir / "actuator_sizing_report.md", markdown_report(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate actuator torque/speed/thermal margins.")
    parser.add_argument("project_dir", help="Project directory containing requirements.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    print(f"actuator valid={payload['valid']} minimum_margin_pct={payload['minimum_margin_pct']}")
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

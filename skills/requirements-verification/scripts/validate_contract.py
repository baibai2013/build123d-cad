#!/usr/bin/env python3
from __future__ import annotations

import argparse

from contract_common import markdown_report, project_path, reports_dir, validate_contract, write_json, write_text


def run(project_dir):
    payload = validate_contract(project_dir)
    report_dir = reports_dir(project_dir)
    write_json(report_dir / "requirements_validation.json", payload)
    write_text(report_dir / "requirements_validation.md", markdown_report(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a requirement contract and verification matrix.")
    parser.add_argument("project_dir", help="Project directory containing requirements.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    print(f"requirements valid={payload['valid']}")
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

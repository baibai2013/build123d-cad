#!/usr/bin/env python3
from __future__ import annotations

import argparse

from gait_common import best_gait_params_yaml, evaluate_project, project_path, reports_dir, write_json, write_text


def run(project_dir):
    payload = evaluate_project(project_dir)
    report_dir = reports_dir(project_dir)
    write_text(report_dir / "best_gait_params.yaml", best_gait_params_yaml(payload))
    write_json(report_dir / "failed_candidates.json", payload["failed_candidates"])
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Select the best scored gait candidate.")
    parser.add_argument("project_dir", help="Project directory containing gait_validation.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    best = payload["best_candidate"]
    print(f"best gait={best.get('name', 'best_candidate')} score={best.get('score', 0)} valid={best.get('valid', False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

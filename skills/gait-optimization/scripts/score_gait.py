#!/usr/bin/env python3
from __future__ import annotations

import argparse

from gait_common import (
    best_gait_params_yaml,
    evaluate_project,
    gait_score_report,
    markdown_report,
    project_path,
    reports_dir,
    trajectory_summary,
    write_json,
    write_text,
)


def run(project_dir):
    payload = evaluate_project(project_dir)
    report_dir = reports_dir(project_dir)
    write_json(report_dir / "gait_score.json", gait_score_report(payload))
    write_json(report_dir / "failed_candidates.json", payload["failed_candidates"])
    write_json(report_dir / "trajectory.json", trajectory_summary(payload))
    write_text(report_dir / "best_gait_params.yaml", best_gait_params_yaml(payload))
    write_text(report_dir / "gait_optimization_report.md", markdown_report(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Score gait validation metrics and suggest next parameters.")
    parser.add_argument("project_dir", help="Project directory containing gait_validation.yaml")
    args = parser.parse_args()
    payload = run(project_path(args.project_dir))
    print(f"gait valid={payload['valid']} score={payload['score']} blockers={len(payload['blockers'])}")
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

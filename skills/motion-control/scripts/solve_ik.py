from __future__ import annotations

import argparse

from motion_common import control_dir, ik_solution, markdown_report, project_path, reports_dir, solve_plan, write_json, write_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Solve robot-dog MVP leg IK targets.")
    parser.add_argument("project_dir", help="Project directory containing motion_plan.yaml")
    args = parser.parse_args(argv)

    project_dir = project_path(args.project_dir)
    payload = solve_plan(project_dir)
    write_json(reports_dir(project_dir) / "ik_report.json", payload)
    write_json(control_dir(project_dir) / "ik_solution.json", ik_solution(payload))
    write_text(reports_dir(project_dir) / "motion_control_report.md", markdown_report(payload))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

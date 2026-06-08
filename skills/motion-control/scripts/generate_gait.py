from __future__ import annotations

import argparse

from motion_common import control_dir, controller_yaml, generate_trajectory, markdown_report, project_path, reports_dir, solve_plan, write_json, write_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate robot-dog MVP gait trajectory.")
    parser.add_argument("project_dir", help="Project directory containing motion_plan.yaml")
    args = parser.parse_args(argv)

    project_dir = project_path(args.project_dir)
    ik_payload = solve_plan(project_dir)
    payload = generate_trajectory(project_dir, ik_payload)
    out_control = control_dir(project_dir)
    write_json(reports_dir(project_dir) / "motion_control_report.json", payload)
    write_json(out_control / "trajectory.json", payload["trajectory"])
    write_text(out_control / "controller_params.yaml", controller_yaml(payload))
    write_text(reports_dir(project_dir) / "motion_control_report.md", markdown_report(payload))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

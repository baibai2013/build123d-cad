from __future__ import annotations

import argparse

from mujoco_common import evaluate_project, markdown_report, mujoco_dir, project_path, reports_dir, scenario_result, trajectory_stub, write_json, write_text


def run(project_dir_raw: str) -> dict[str, object]:
    project_dir = project_path(project_dir_raw)
    payload = evaluate_project(project_dir)
    out_reports = reports_dir(project_dir)
    out_mujoco = mujoco_dir(project_dir)
    write_json(out_reports / "mujoco_result.json", payload)
    write_text(out_reports / "mujoco_validation_report.md", markdown_report(payload))
    for scenario in payload["scenarios"]:
        name = str(scenario["name"])
        write_json(out_mujoco / "results" / f"{name}.sim_result.json", scenario_result(str(payload["project"]), str(payload["backend"]), scenario))
        write_json(out_mujoco / "trajectories" / f"{name}.trajectory.json", trajectory_stub(str(payload["project"]), scenario))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic MuJoCo-style scenario checks.")
    parser.add_argument("project_dir", help="Project directory containing mujoco_scenarios.yaml")
    args = parser.parse_args(argv)
    payload = run(args.project_dir)
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

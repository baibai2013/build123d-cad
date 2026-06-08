from __future__ import annotations

import argparse

from sim2real_common import evaluate_project, parameter_update, project_path, reports_dir, write_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Propose conservative sim-to-real parameter updates.")
    parser.add_argument("project_dir", help="Project directory containing calibration_dataset.yaml")
    args = parser.parse_args(argv)

    project_dir = project_path(args.project_dir)
    payload = evaluate_project(project_dir)
    write_text(reports_dir(project_dir) / "parameter_update.yaml", parameter_update(payload))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

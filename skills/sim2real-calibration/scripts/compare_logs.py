from __future__ import annotations

import argparse

from sim2real_common import evaluate_project, markdown_report, project_path, reports_dir, write_json, write_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare simulation and real robot metrics.")
    parser.add_argument("project_dir", help="Project directory containing calibration_dataset.yaml")
    args = parser.parse_args(argv)

    project_dir = project_path(args.project_dir)
    payload = evaluate_project(project_dir)
    write_json(reports_dir(project_dir) / "sim2real_calibration.json", payload)
    write_text(reports_dir(project_dir) / "sim2real_report.md", markdown_report(payload))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

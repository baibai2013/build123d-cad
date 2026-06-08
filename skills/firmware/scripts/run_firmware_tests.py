from __future__ import annotations

import argparse

from firmware_common import evaluate_project, project_path, reports_dir, test_report, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run firmware dry-run metadata tests.")
    parser.add_argument("project_dir", help="Project directory containing firmware_plan.yaml")
    args = parser.parse_args(argv)

    project_dir = project_path(args.project_dir)
    payload = test_report(evaluate_project(project_dir))
    write_json(reports_dir(project_dir) / "firmware_test_report.json", payload)
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

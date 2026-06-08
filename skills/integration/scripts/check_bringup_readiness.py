from __future__ import annotations

import argparse

from integration_common import bringup_markdown, evaluate_project, project_path, reports_dir, write_json, write_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check robot-dog physical bring-up readiness.")
    parser.add_argument("project_dir", help="Project directory containing integration_plan.yaml")
    args = parser.parse_args(argv)

    project_dir = project_path(args.project_dir)
    payload = evaluate_project(project_dir)
    write_json(reports_dir(project_dir) / "integration_checklist.json", payload)
    write_text(reports_dir(project_dir) / "bringup_report.md", bringup_markdown(payload))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

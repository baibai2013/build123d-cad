from __future__ import annotations

import argparse

from integration_common import data_capture_markdown, evaluate_project, hil_plan_markdown, project_path, reports_dir, write_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write HIL and data-capture plan.")
    parser.add_argument("project_dir", help="Project directory containing integration_plan.yaml")
    args = parser.parse_args(argv)

    project_dir = project_path(args.project_dir)
    payload = evaluate_project(project_dir)
    write_text(reports_dir(project_dir) / "hil_plan.md", hil_plan_markdown(payload))
    write_text(reports_dir(project_dir) / "data_capture_checklist.md", data_capture_markdown(payload))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

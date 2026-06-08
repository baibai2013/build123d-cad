from __future__ import annotations

import argparse
import json
from pathlib import Path

from mujoco_common import markdown_report, project_path, reports_dir, write_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize an existing MuJoCo result report.")
    parser.add_argument("project_dir", help="Project directory containing reports/mujoco_result.json")
    args = parser.parse_args(argv)
    project_dir = project_path(args.project_dir)
    report_path = reports_dir(project_dir) / "mujoco_result.json"
    if not report_path.exists():
        raise FileNotFoundError(report_path)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    write_text(reports_dir(project_dir) / "mujoco_validation_report.md", markdown_report(payload))
    return 0 if payload.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())

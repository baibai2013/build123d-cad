from __future__ import annotations

import argparse
import sys

from wear_common import evaluate_project, maintenance_markdown, project_path, reports_dir, summary_markdown, wear_report, write_json, write_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Estimate robot-dog wear risks.")
    parser.add_argument("project_dir", help="Project directory containing wear_inputs.yaml")
    args = parser.parse_args(argv)

    project_dir = project_path(args.project_dir)
    payload = evaluate_project(project_dir)
    report = wear_report(payload)
    out_dir = reports_dir(project_dir)
    write_json(out_dir / "wear_report.json", report)
    write_text(out_dir / "maintenance_interval.md", maintenance_markdown(payload))
    write_text(out_dir / "wear_fatigue_report.md", summary_markdown(payload))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

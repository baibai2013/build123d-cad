from __future__ import annotations

import argparse

from firmware_common import calibration_payload, can_frames_markdown, evaluate_project, firmware_dir, manifest, project_path, reports_dir, write_json, write_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate firmware dry-run project manifest.")
    parser.add_argument("project_dir", help="Project directory containing firmware_plan.yaml")
    args = parser.parse_args(argv)

    project_dir = project_path(args.project_dir)
    payload = evaluate_project(project_dir)
    out = firmware_dir(project_dir)
    write_json(out / "project_manifest.json", manifest(payload))
    write_text(out / "can_frames.md", can_frames_markdown(payload))
    write_json(out / "calibration.json", calibration_payload(payload))
    write_json(reports_dir(project_dir) / "firmware_report.json", payload)
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse

from bom_common import availability, project_path, reports_dir, select_parts, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check offline electronics BOM availability status.")
    parser.add_argument("project_dir", help="Project directory containing bom_request.yaml")
    args = parser.parse_args(argv)

    project_dir = project_path(args.project_dir)
    payload = availability(select_parts(project_dir))
    write_json(reports_dir(project_dir) / "availability_report.json", payload)
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

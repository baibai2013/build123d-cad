from __future__ import annotations

import argparse

from bom_common import library_dir, project_path, rationale_markdown, reports_dir, select_parts, selected_parts_payload, write_json, write_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Select electronics BOM candidates from offline catalog.")
    parser.add_argument("project_dir", help="Project directory containing bom_request.yaml")
    args = parser.parse_args(argv)

    project_dir = project_path(args.project_dir)
    payload = select_parts(project_dir)
    write_json(reports_dir(project_dir) / "electronics_bom.json", payload)
    write_json(library_dir(project_dir) / "selected_parts.json", selected_parts_payload(payload))
    write_text(reports_dir(project_dir) / "selection_rationale.md", rationale_markdown(payload))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

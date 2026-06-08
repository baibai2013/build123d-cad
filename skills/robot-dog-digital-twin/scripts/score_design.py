#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from digital_twin_common import compute_design_score, project_path, reports_dir, write_json


def score(project_dir: Path) -> dict[str, object]:
    payload = compute_design_score(project_dir)
    write_json(reports_dir(project_dir) / "design_score.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a robot dog digital-twin design.")
    parser.add_argument("project_dir", help="Project directory containing collected artifacts")
    args = parser.parse_args()
    payload = score(project_path(args.project_dir))
    print(f"Design score: {payload['total_score']} prototype_allowed={payload['prototype_allowed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

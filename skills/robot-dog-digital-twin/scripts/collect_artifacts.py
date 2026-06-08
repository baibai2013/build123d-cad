#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from digital_twin_common import collect_artifacts_payload, project_path, reports_dir, write_json


def collect(project_dir: Path) -> dict[str, object]:
    payload = collect_artifacts_payload(project_dir)
    write_json(reports_dir(project_dir) / "artifacts.collected.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect robot dog digital-twin artifacts.")
    parser.add_argument("project_dir", help="Project directory containing requirements.yaml and artifacts.json")
    args = parser.parse_args()
    payload = collect(project_path(args.project_dir))
    print(f"Collected artifacts for {payload['project']}: {len(payload['missing'])} missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

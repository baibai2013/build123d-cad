#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from contract_common import project_path, write_text


REQUIREMENTS_TEMPLATE = """version: "1.0"
project:
  name: {name}
  type: quadruped
  dof: 12

targets:
  mass_kg: 5.0
  payload_kg: 0.5
  runtime_min: 30
  flat_walk_speed_mps: 0.5
  stand_stable_seconds: 30
  joint_torque_margin_pct: 20

constraints:
  manufacturing:
    primary: fdm_3d_print
    material: petg
  electronics:
    battery_voltage_nominal: 24
    max_current_a: 30
  safety:
    require_emergency_stop: true
    max_surface_temp_c: 65
"""


MATRIX_TEMPLATE = """mechanical:
  no_assembly_interference:
    target: no_assembly_interference
    source: mechanical
    artifact: mechanical/collision_report.json
    required: true
    blocker: true

dynamics:
  stand_stable_seconds:
    target: stand_stable_seconds
    source: simulation
    artifact: simulation/stand_result.json
    limit_min: 30
    blocker: true

gait:
  flat_walk_no_fall:
    target: flat_walk_no_fall
    source: gait_optimization
    artifact: control/gait_score.json
    required: true
    blocker: true
"""


ARCHITECTURE_TEMPLATE = """version: "1.0"
system:
  name: {name}
  morphology: quadruped
  legs: 4
  joints_per_leg: 3

domains:
  mechanical:
    body: printed_shell
  electrical:
    battery: 6s_lipo
  simulation:
    smoke_engine: pybullet
"""


RISK_TEMPLATE = """# Risk Register

| ID | Domain | Risk | Mitigation | Evidence Needed |
|---|---|---|---|---|
| R-001 | dynamics | Contact-model fidelity may be insufficient | Keep early gates conservative | Higher-fidelity simulation before G5 |
"""


def write_if_missing(path: Path, text: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    write_text(path, text)
    return True


def run(project_dir: Path, name: str, force: bool = False) -> list[str]:
    project_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    files = {
        "requirements.yaml": REQUIREMENTS_TEMPLATE.format(name=name),
        "verification_matrix.yaml": MATRIX_TEMPLATE,
        "architecture.yaml": ARCHITECTURE_TEMPLATE.format(name=name),
        "risk_register.md": RISK_TEMPLATE,
    }
    for rel_path, text in files.items():
        if write_if_missing(project_dir / rel_path, text, force):
            written.append(rel_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Create starter requirement contract files.")
    parser.add_argument("project_dir", help="Project directory to create")
    parser.add_argument("--name", default="quadruped_mvp", help="Project name")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()
    written = run(project_path(args.project_dir), args.name, args.force)
    print("written=" + ",".join(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

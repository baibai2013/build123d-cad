# circuit-simulation Module Handoff

Date: 2026-06-08

## Status

`skills/circuit-simulation/` MVP is implemented and verified.

## Scope Landed

- `SKILL.md` and `README.md` define circuit, power budget, protection, and thermal boundaries.
- `scripts/check_power_budget.py` reads `circuit_requirements.yaml` and writes machine-readable reports.
- `scripts/check_protection.py` writes a focused protection checklist.
- `scripts/write_report.py` writes a focused markdown report.
- `scripts/circuit_common.py` contains deterministic MVP checks for ERC/DRC, battery current, fuse rating, power rail margins, motor driver margins, protection coverage, and thermal estimates.
- `examples/quadruped_mvp/` is intentionally failed/underpowered/hot and should produce blockers.
- `tests/` covers smoke shape, blocking report generation, passing conservative-circuit case, protection checklist generation, and markdown report generation.

## Standard Outputs

For a project directory:

```text
reports/
  circuit_check.json
  power_budget.json
  thermal_report.json
  protection_checklist.md
  circuit_simulation_report.md
```

`circuit_check.json` is the compact machine-readable artifact for downstream digital-twin gates.

## Verification

Focused tests:

```bash
/private/tmp/build123d-cad-pytest-venv/bin/python -m pytest skills/circuit-simulation/tests/
```

Result:

```text
7 passed in 0.06s
```

Example behavior:

```bash
python3 skills/circuit-simulation/scripts/check_power_budget.py skills/circuit-simulation/examples/quadruped_mvp
```

Expected result: exits `1` because the example has failed ERC, oversized fuse, missing emergency stop, weak motor drivers, and thermal blockers.

```text
circuit valid=False blockers=12
```

Protection checklist:

```bash
python3 skills/circuit-simulation/scripts/check_protection.py skills/circuit-simulation/examples/quadruped_mvp
```

Expected result: exits `1` because the example is invalid.

```text
wrote protection checklist valid=False
```

Markdown report:

```bash
python3 skills/circuit-simulation/scripts/write_report.py skills/circuit-simulation/examples/quadruped_mvp
```

Result:

```text
wrote circuit simulation report valid=False
```

## Integration Updates

- Parent `SKILL.md` routes circuit reasonableness, power budget, current peak, protection, undervoltage, TVS, fuse, and thermal-risk requests to this subskill.
- `README.md` lists the subskill and directory.
- `shared/multi-skill-router.md` maps circuit/power/protection/thermal keywords.
- `shared/dependencies.md` registers `pcb/electronics-bom -> circuit-simulation -> robot-dog-digital-twin`.
- `shared/handoff-protocols.md` registers circuit simulation output artifacts.
- `shared/CHANGELOG.md` records the shared interface change.
- `pytest.ini` includes `skills/circuit-simulation/tests`.

## Next Module

Proceed to `gait-optimization` after context cleanup/compaction. It should consume gait/simulation metadata and emit `gait_score.json`, `best_gait_params.yaml`, `failed_candidates.json`, and trajectory summaries.

# Module Handoff

## Completed

- Created `skills/robot-dog-digital-twin/` skill skeleton.
- Added MVP references, scripts, tests, and `examples/quadruped_mvp/`.
- Added deterministic artifact collection, scoring, gate reporting, failure reporting,
  and next-iteration planning scripts.
- Connected the skill to parent routing, shared router, dependencies, handoff protocol,
  README, and `pytest.ini`.

## Outputs

Example project:

```text
skills/robot-dog-digital-twin/examples/quadruped_mvp/
```

Generated reports:

```text
reports/artifacts.collected.json
reports/design_score.json
reports/gate_report.json
reports/gate_report.md
reports/failure_report.md
reports/next_iteration_plan.md
```

## Verified Commands

```bash
python3 skills/robot-dog-digital-twin/scripts/collect_artifacts.py skills/robot-dog-digital-twin/examples/quadruped_mvp
python3 skills/robot-dog-digital-twin/scripts/score_design.py skills/robot-dog-digital-twin/examples/quadruped_mvp
python3 skills/robot-dog-digital-twin/scripts/run_gate.py skills/robot-dog-digital-twin/examples/quadruped_mvp --gate G0
python3 skills/robot-dog-digital-twin/scripts/run_gate.py skills/robot-dog-digital-twin/examples/quadruped_mvp --gate G3
python3 skills/robot-dog-digital-twin/scripts/propose_next_iteration.py skills/robot-dog-digital-twin/examples/quadruped_mvp
```

Expected status:

- G0 passes.
- G3 fails because the MVP example intentionally includes PCB clearance, flat-walk,
  and torque-margin blockers.

## Verification

System Python does not include pytest:

```text
python3 -m pytest skills/robot-dog-digital-twin/tests/
# No module named pytest
```

Verified with a temporary venv:

```text
/private/tmp/build123d-cad-pytest-venv/bin/python -m pytest skills/robot-dog-digital-twin/tests/
# 9 passed
```

## Next Module Inputs

The next planned P0 modules can consume:

- `requirements.yaml`
- `verification_matrix.yaml`
- `artifacts.json`
- `reports/design_score.json`
- `reports/failure_report.md`
- `reports/next_iteration_plan.md`

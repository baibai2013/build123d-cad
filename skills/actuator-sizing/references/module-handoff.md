# actuator-sizing Module Handoff

Date: 2026-06-08

## Status

`skills/actuator-sizing/` MVP is implemented and verified.

## Scope Landed

- `SKILL.md` and `README.md` define actuator sizing boundaries.
- `scripts/estimate_torque.py` reads `requirements.yaml`, `architecture.yaml`, and optional `actuator_candidate.yaml`.
- `scripts/write_report.py` writes a focused markdown report.
- `scripts/actuator_common.py` contains deterministic MVP calculations for hip/knee/ankle torque, speed, and thermal margin.
- `examples/quadruped_mvp/` is intentionally underpowered and should produce blockers.
- `tests/` covers smoke shape, blocking report generation, passing stronger-actuator case, and markdown report generation.

## Standard Outputs

For a project directory:

```text
reports/
  torque_margin.json
  actuator_spec.yaml
  actuator_sizing_report.md
```

`torque_margin.json` is the primary machine-readable artifact for downstream digital-twin gates.

## Verification

Focused tests:

```bash
/private/tmp/build123d-cad-pytest-venv/bin/python -m pytest skills/actuator-sizing/tests/
```

Result:

```text
6 passed in 0.03s
```

Example behavior:

```bash
python3 skills/actuator-sizing/scripts/estimate_torque.py skills/actuator-sizing/examples/quadruped_mvp
```

Expected result: exits `1` because the example actuator is intentionally underpowered.

```text
actuator valid=False minimum_margin_pct=-11.33
```

Report writer:

```bash
python3 skills/actuator-sizing/scripts/write_report.py skills/actuator-sizing/examples/quadruped_mvp
```

Result:

```text
wrote actuator report valid=False
```

## Integration Updates

- Parent `SKILL.md` routes actuator torque, motor, reducer, speed margin, and thermal margin requests to this subskill.
- `README.md` lists the subskill and directory.
- `shared/multi-skill-router.md` maps actuator-related keywords.
- `shared/dependencies.md` registers `requirements-verification -> actuator-sizing -> robot-dog-digital-twin`.
- `shared/handoff-protocols.md` registers actuator output artifacts.
- `pytest.ini` includes `skills/actuator-sizing/tests`.

## Next Module

Proceed to `pcb-mechanical-reliability` after context cleanup/compaction. It should consume PCB/mechanical geometry metadata and emit `pcb_fit.json`, `pcb_reliability_report.json`, and connector clearance blockers.

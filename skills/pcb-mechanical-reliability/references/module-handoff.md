# pcb-mechanical-reliability Module Handoff

Date: 2026-06-08

## Status

`skills/pcb-mechanical-reliability/` MVP is implemented and verified.

## Scope Landed

- `SKILL.md` and `README.md` define PCB mechanical reliability boundaries.
- `scripts/check_pcb_fit.py` reads `pcb_mechanical.yaml` and writes machine-readable reports.
- `scripts/write_report.py` writes a focused markdown report.
- `scripts/pcb_mech_common.py` contains deterministic MVP checks for board fit, mounting support, board flex, connector clearance, cable bend radius, and strain relief.
- `examples/quadruped_mvp/` is intentionally under-supported and should produce blockers.
- `tests/` covers smoke shape, blocking report generation, passing supported-board case, connector sidecar output, and markdown report generation.

## Standard Outputs

For a project directory:

```text
reports/
  pcb_fit.json
  pcb_reliability_report.json
  connector_clearance.json
  pcb_mechanical_report.md
```

`pcb_fit.json` is the compact machine-readable artifact for downstream digital-twin gates.

## Verification

Focused tests:

```bash
/private/tmp/build123d-cad-pytest-venv/bin/python -m pytest skills/pcb-mechanical-reliability/tests/
```

Result:

```text
6 passed in 0.03s
```

Example behavior:

```bash
python3 skills/pcb-mechanical-reliability/scripts/check_pcb_fit.py skills/pcb-mechanical-reliability/examples/quadruped_mvp
```

Expected result: exits `1` because the example PCB is intentionally under-supported.

```text
pcb mechanical valid=False blockers=11
```

Report writer:

```bash
python3 skills/pcb-mechanical-reliability/scripts/write_report.py skills/pcb-mechanical-reliability/examples/quadruped_mvp
```

Result:

```text
wrote pcb mechanical report valid=False
```

## Integration Updates

- Parent `SKILL.md` routes PCB stiffness, flex, standoff, connector load, cable bend, and PCB fit requests to this subskill.
- `README.md` lists the subskill and directory.
- `shared/multi-skill-router.md` maps PCB mechanical reliability keywords.
- `shared/dependencies.md` registers `pcb+mechanical -> pcb-mechanical-reliability -> robot-dog-digital-twin`.
- `shared/handoff-protocols.md` registers PCB mechanical reliability output artifacts.
- `shared/CHANGELOG.md` records the shared interface change.
- `pytest.ini` includes `skills/pcb-mechanical-reliability/tests`.

## Next Module

Proceed to `circuit-simulation` after context cleanup/compaction. It should consume electrical metadata and emit `circuit_check.json`, `power_budget.json`, `thermal_report.json`, and `protection_checklist.md`.

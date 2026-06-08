# fea Module Handoff

Date: 2026-06-08

## Status

`skills/fea/` MVP is implemented and verified.

## Scope Landed

- `SKILL.md` and `README.md` define structural FEA gate boundaries.
- `scripts/run_static_case.py` reads `fea_cases.yaml` and writes machine-readable reports.
- `scripts/summarize_fea.py` writes a focused markdown checklist.
- `scripts/fea_common.py` contains deterministic MVP checks for stress, yield margin, safety factor, deflection, first modal frequency, and gait excitation ratio.
- `examples/quadruped_mvp/` is intentionally structurally risky and should produce blockers.
- `tests/` covers smoke shape, blocking report generation, passing strong-case report, and checklist generation.

## Standard Outputs

For a project directory:

```text
reports/
  fea_report.json
  static_case_report.json
  fea_checklist.md
```

`fea_report.json` is the compact machine-readable artifact for downstream digital-twin gates.

## Verification

Focused tests:

```bash
/private/tmp/build123d-cad-pytest-venv/bin/python -m pytest skills/fea/tests/
```

Result:

```text
6 passed in 0.03s
```

Example behavior:

```bash
python3 skills/fea/scripts/run_static_case.py skills/fea/examples/quadruped_mvp
```

Expected result: exits `1` because the example has safety-factor, deflection, and modal-ratio blockers.

```text
fea valid=False blockers=3
```

Markdown checklist:

```bash
python3 skills/fea/scripts/summarize_fea.py skills/fea/examples/quadruped_mvp
```

Result:

```text
wrote fea checklist valid=False
```

## Integration Updates

- Parent `SKILL.md` routes FEA, structural strength, stiffness, stress, deflection, modal, and drop-impact requests to this subskill.
- `README.md` lists the subskill and directory.
- `shared/multi-skill-router.md` maps structural FEA keywords.
- `shared/dependencies.md` registers `mechanical -> fea -> robot-dog-digital-twin`.
- `shared/handoff-protocols.md` registers FEA output artifacts.
- `shared/CHANGELOG.md` records the shared interface change.
- `pytest.ini` includes `skills/fea/tests`.

## Next Module

Proceed to `wear-fatigue` after context cleanup/compaction. It should consume load/trajectory/material metadata and emit `wear_report.json`, `fatigue_report.json`, and `maintenance_interval.md`.

# Module Handoff

Completed module: `integration`

Purpose:

- Gate safe physical assembly, first power-on, HIL, and motor-motion readiness.
- Produce bring-up and data-capture plans without touching hardware.

Inputs:

- `<project>/integration_plan.yaml`

Outputs:

- `<project>/reports/integration_checklist.json`
- `<project>/reports/bringup_report.md`
- `<project>/reports/hil_plan.md`
- `<project>/reports/data_capture_checklist.md`

Verification:

- Run `python -m pytest skills/integration/tests/`.

Context handoff:

- After this module is complete, clear active context and load only this handoff
  plus the next target skill files before continuing.

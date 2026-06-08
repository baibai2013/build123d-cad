# Module Handoff

Completed module: `wear-fatigue`

Purpose:

- Check gear/reducer, bearing, foot pad, joint interface, harness, and connector
  wear/fatigue risks before physical prototype release.
- Produce deterministic JSON and Markdown reports for `robot-dog-digital-twin`.

Inputs:

- `<project>/wear_inputs.yaml`

Outputs:

- `<project>/reports/wear_report.json`
- `<project>/reports/fatigue_report.json`
- `<project>/reports/maintenance_interval.md`
- `<project>/reports/wear_fatigue_report.md`

Verification:

- Run `python -m pytest skills/wear-fatigue/tests/`.

Context handoff:

- After this module is complete, clear active context and load only this handoff
  plus the next target skill files before continuing.

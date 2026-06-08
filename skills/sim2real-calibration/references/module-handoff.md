# Module Handoff

Completed module: `sim2real-calibration`

Purpose:

- Compare simulation and real prototype metrics.
- Suggest conservative simulation parameter updates.

Inputs:

- `<project>/calibration_dataset.yaml`

Outputs:

- `<project>/reports/sim2real_calibration.json`
- `<project>/reports/sim2real_report.md`
- `<project>/reports/parameter_update.yaml`

Verification:

- Run `python -m pytest skills/sim2real-calibration/tests/`.

Context handoff:

- After this module is complete, clear active context and load only this handoff
  plus the next target skill files before continuing.

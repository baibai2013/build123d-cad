# Module Handoff

Completed module: `firmware`

Purpose:

- Validate embedded firmware readiness without compiling, flashing, or moving hardware.
- Generate MCU/bus/control/safety/calibration file contracts.

Inputs:

- `<project>/firmware_plan.yaml`

Outputs:

- `<project>/reports/firmware_report.json`
- `<project>/reports/firmware_test_report.json`
- `<project>/firmware/project_manifest.json`
- `<project>/firmware/can_frames.md`
- `<project>/firmware/calibration.json`

Verification:

- Run `python -m pytest skills/firmware/tests/`.

Context handoff:

- After this module is complete, clear active context and load only this handoff
  plus the next target skill files before continuing.

# Module Handoff

Completed module: `motion-control`

Purpose:

- Solve early leg IK targets.
- Generate deterministic phase gait trajectories and controller parameter files.
- Provide motion artifacts for simulation, MuJoCo, viewer playback, and firmware.

Inputs:

- `<project>/motion_plan.yaml`

Outputs:

- `<project>/reports/ik_report.json`
- `<project>/reports/motion_control_report.json`
- `<project>/control/ik_solution.json`
- `<project>/control/trajectory.json`
- `<project>/control/controller_params.yaml`

Verification:

- Run `python -m pytest skills/motion-control/tests/`.

Context handoff:

- After this module is complete, clear active context and load only this handoff
  plus the next target skill files before continuing.

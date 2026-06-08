# Module Handoff

Completed module: `mujoco-simulation`

Purpose:

- Define and validate MuJoCo/MJCF dynamics scenarios for robot-dog virtual
  prototypes.
- Produce deterministic scenario and aggregate reports for `robot-dog-digital-twin`.

Inputs:

- `<project>/mujoco_scenarios.yaml`
- Optional `<project>/simulation/mujoco/robot.xml`

Outputs:

- `<project>/reports/mujoco_result.json`
- `<project>/reports/mujoco_validation_report.md`
- `<project>/simulation/mujoco/results/<scenario>.sim_result.json`
- `<project>/simulation/mujoco/trajectories/<scenario>.trajectory.json`

Verification:

- Run `python -m pytest skills/mujoco-simulation/tests/`.

Context handoff:

- After this module is complete, clear active context and load only this handoff
  plus the next target skill files before continuing.

# Output Contract

`run_scenarios.py` writes:

- `reports/mujoco_result.json`
- `reports/mujoco_validation_report.md`
- `simulation/mujoco/results/<scenario>.sim_result.json`
- `simulation/mujoco/trajectories/<scenario>.trajectory.json`

The aggregate JSON includes:

- `project`
- `backend`
- `valid`
- `blockers`
- `warnings`
- `summary`
- `scenarios`
- `next_actions`

`valid: false` means `robot-dog-digital-twin` must treat MuJoCo dynamics as a
blocking validation domain.

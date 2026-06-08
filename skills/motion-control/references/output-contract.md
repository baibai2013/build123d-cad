# Output Contract

`solve_ik.py` writes:

- `reports/ik_report.json`
- `control/ik_solution.json`

`generate_gait.py` writes:

- `reports/motion_control_report.json`
- `control/trajectory.json`
- `control/controller_params.yaml`

Reports include:

- `project`
- `valid`
- `blockers`
- `warnings`
- `summary`
- `next_actions`

`valid: false` means motion-control artifacts should not feed dynamics or
firmware gates until blockers are resolved.

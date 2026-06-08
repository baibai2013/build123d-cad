# Input Contract

`mujoco_scenarios.yaml` contains a MuJoCo/MJCF model reference, scenario limits,
and either metadata-mode observations or future solver-backed results.

Required top-level fields:

```yaml
project: quadruped_mvp
backend: metadata
model:
  mjcf: simulation/mujoco/robot.xml
limits:
  stand_stable_seconds_min: 30
scenarios: []
```

Use `backend: metadata` for the MVP. Future `backend: mujoco` should fill the
same fields from a real MuJoCo run.

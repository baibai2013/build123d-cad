# Input Contract

`firmware_plan.yaml` describes a planned embedded firmware target.

Required top-level fields:

```yaml
project: quadruped_mvp
target: {}
control_loop: {}
bus: {}
safety: {}
calibration: {}
```

The MVP is metadata-based. It validates that the plan is complete enough for a
future firmware project generator or hardware bring-up dry run.

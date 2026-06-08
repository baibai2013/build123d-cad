# Input Contract

`integration_plan.yaml` contains readiness flags for physical prototype bring-up.

Required top-level fields:

```yaml
project: quadruped_mvp
gates: {}
safety: {}
testbench: {}
data_capture: {}
```

All fields are dry-run declarations. The skill does not manipulate hardware.

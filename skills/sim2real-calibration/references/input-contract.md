# Input Contract

`calibration_dataset.yaml` contains paired simulation and real metrics.

Required top-level fields:

```yaml
project: quadruped_mvp
tolerances: {}
simulation: {}
real: {}
```

The MVP compares aggregate metrics, not raw time-series logs.

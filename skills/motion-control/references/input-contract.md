# Input Contract

`motion_plan.yaml` contains leg geometry, joint limits, IK targets, and gait
parameters.

Required top-level fields:

```yaml
project: quadruped_mvp
link_lengths:
  thigh_mm: 90
  shank_mm: 95
joint_limits_deg: {}
ik_targets: []
gait: {}
```

Coordinates use a sagittal leg plane for the MVP: `x_mm` forward/back and
`z_mm` vertical, with negative `z_mm` below the hip.

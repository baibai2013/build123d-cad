# Input Contract

`wear_inputs.yaml` contains target maintenance life plus component-specific
observations from CAD, simulation, supplier data, or hand estimates.

Required top-level fields:

```yaml
project: quadruped_mvp
target_maintenance_hours: 50
gears: []
bearings: []
foot_pads: []
joint_interfaces: []
harnesses: []
connectors: []
```

Each component entry should include `name`. Numeric limits are interpreted as
engineering estimates, not final certification values.

Use UTF-8 for all files.

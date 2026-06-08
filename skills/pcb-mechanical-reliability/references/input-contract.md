# Input Contract

The MVP reads a project directory containing `pcb_mechanical.yaml`.

```yaml
version: "1.0"
board:
  name: main_control_board
  width_mm: 78
  length_mm: 112
  thickness_mm: 1.2
  mass_g: 42
  enclosure_clearance_mm: 1.2
  edge_clearance_mm: 2.5

mounting:
  hole_count: 3
  standoff_count: 3
  hole_edge_distance_mm: 2.4
  max_unsupported_span_mm: 86

loads:
  vibration_g: 4
  drop_height_m: 0.4

connectors:
  - name: battery_xt30
    kind: power
    height_mm: 8.5
    clearance_mm: 1.0
    nearest_standoff_mm: 42
    cable_bend_radius_mm: 18
    cable_min_bend_radius_mm: 25
    strain_relief: false
```

All lengths use millimeters except `drop_height_m`.

The contract is intentionally metadata-based. Detailed CAD/PCB parsing can be added later
without changing the downstream report names.

# Standoff Rules

MVP blocker thresholds:

- Minimum enclosure clearance: 2 mm.
- Minimum board edge clearance: 2 mm.
- Minimum PCB thickness for robot-dog vibration: 1.6 mm.
- Minimum mounting holes: 4 for boards larger than 5000 mm^2.
- Minimum hole edge distance: 3 mm.
- Maximum unsupported span: 70 mm.
- Maximum estimated board flex: 1.5 mm.

The board-flex estimate is a conservative beam approximation:

```text
deflection = load * span^3 / (48 * E * I)
I = width * thickness^3 / 12
load = board_mass * g * vibration_g
```

This is not FEA. It is a fast rule check to catch obviously risky layouts.

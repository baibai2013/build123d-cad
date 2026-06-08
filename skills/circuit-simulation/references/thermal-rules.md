# Thermal Rules

MVP thermal estimate:

```text
estimated_temp_c = ambient_c + dissipation_w * thermal_resistance_c_w
```

Blocker threshold:

- `estimated_temp_c > max_temp_c`

Warning threshold:

- `estimated_temp_c > max_temp_c - 10`

This is not a CFD or board-level thermal simulation. It is a fast first-pass risk
check for regulators, drivers, MOSFETs, and hot protection devices.

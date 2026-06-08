# Torque Model

MVP formulas are intentionally conservative and simple.

Total supported mass:

```text
total_mass_kg = mass_kg + payload_kg
```

Per-leg static load:

```text
load_per_leg_n = total_mass_kg * 9.81 / stance_legs
```

Joint torque estimates:

```text
hip_torque_nm = load_per_leg_n * body_half_width_m * slope_factor
knee_torque_nm = load_per_leg_n * femur_length_m * dynamic_factor * slope_factor
ankle_torque_nm = load_per_leg_n * tibia_length_m * 0.6 * dynamic_factor
```

This is not a replacement for dynamics simulation. It is a G0/G1 sizing guardrail.

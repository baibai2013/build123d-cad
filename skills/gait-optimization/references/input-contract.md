# Input Contract

The MVP reads a project directory containing `gait_validation.yaml`.

```yaml
version: "1.0"
target:
  stand_stable_seconds: 30
  average_speed_mps_min: 0.5
  max_body_roll_deg: 8
  max_body_pitch_deg: 8
  foot_slip_ratio_max: 0.12
  joint_torque_margin_pct_min: 20
  cost_of_transport_max: 2.5

gait_params:
  name: trot_v0
  stride_mm: 62
  clearance_mm: 42
  duty_factor: 0.48
  body_height_mm: 135
  phase_pattern: trot

validation:
  single_leg_ik_pass: true
  phase_complete: true
  stand_stable_seconds: 21
  flat_walk_no_fall: false
  fall_time_s: 4.2
  max_body_roll_deg: 11
  max_body_pitch_deg: 9
  foot_slip_ratio: 0.18
  joint_torque_margin_pct: 12
  average_speed_mps: 0.43
  cost_of_transport: 3.1

candidates:
  - name: safer_trot
    params:
      stride_mm: 42
      clearance_mm: 30
      duty_factor: 0.58
      body_height_mm: 120
    validation:
      single_leg_ik_pass: true
      phase_complete: true
      stand_stable_seconds: 32
      flat_walk_no_fall: true
      max_body_roll_deg: 6
      max_body_pitch_deg: 6
      foot_slip_ratio: 0.08
      joint_torque_margin_pct: 26
      average_speed_mps: 0.52
      cost_of_transport: 2.2
```

The contract is metadata-based so it can be populated by PyBullet, MuJoCo, or a
hand-authored smoke test.

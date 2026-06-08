# Sim2Real Calibration Report

Project: quadruped_mvp
Status: FAIL

## Error Summary
- speed_error_pct: -26.923
- slip_error_abs: 0.1
- torque_error_pct: 36.538
- roll_error_deg: 3.5
- pitch_error_deg: 3.2
- latency_error_ms: 20

## Blockers
- speed error -26.9% exceeds 15%
- slip error 0.100 exceeds 0.05
- torque error 36.5% exceeds 20%
- posture error roll=3.5deg pitch=3.2deg exceeds 3deg
- latency error 20.0ms exceeds 10ms

## Next Actions
- increase drivetrain loss or retune gait speed model
- adjust friction/contact parameters and foot material model
- increase actuator load scale or inertia estimate
- review COM, inertia, and contact damping
- add control latency parameter and rerun gait simulation

# Safety Gates

Blockers:

- `safety.emergency_stop` is false.
- `safety.undervoltage_cutoff_v` is missing or below safe configured value.
- `safety.overcurrent_limit_a` is missing.
- `safety.thermal_shutdown_c` is missing or too high.
- calibration lacks joint zeroing or encoder offset capture.
- control loop frequency is below the declared minimum.

The MVP must never flash hardware. It only reports readiness.

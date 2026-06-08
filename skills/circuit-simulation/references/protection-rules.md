# Protection Rules

MVP blockers:

- `safety.emergency_stop` must be true for robot-dog prototypes.
- `battery.fuse_current_a` must be present and not exceed `battery.max_current_a`.
- `safety.undervoltage_cutoff_v` must be at least 70% of nominal battery voltage.
- `safety.tvs_diode` should be present for motor-driver power rails.

MVP warnings:

- Missing reverse-polarity protection is a warning in low-current prototypes and a
  blocker in later gates.
- Bulk capacitance below 1000 uF is a warning for motor-heavy designs.

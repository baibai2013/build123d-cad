# Load Cases

MVP load-case categories:

- `static_stance`: sustained standing load.
- `max_torque`: joint shell load at maximum actuator torque.
- `drop_landing`: landing/drop impact multiplier.
- `side_impact`: lateral hit or fall onto the side.

Blockers are based on result metrics, not on the load-case name.

Default gates:

- Minimum safety factor: 2.0.
- Maximum deflection: 2.0 mm unless case override is provided.
- Minimum modal ratio: first mode should be at least 2x gait excitation frequency.

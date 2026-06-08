# Power Rail Rules

MVP blocker thresholds:

- Minimum current margin: 20%.
- Battery peak current must not exceed `battery.max_current_a`.
- Fuse current should be at or below the declared battery max current.
- Regulator efficiency below 70% is a warning.

Power rail margin:

```text
current_margin_pct = (regulator_current_a - load_current_a) / regulator_current_a * 100
```

Total battery current is estimated from rail output power and motor driver continuous
current demand.

# Gait Contract

The MVP supports phase-table gait generation:

- `trot`: diagonal leg pairs out of phase.
- `walk`: four legs evenly phased.
- `bound`: front pair and rear pair out of phase.

Trajectory output uses:

```json
{
  "format": "build123d-cad.trajectory.v1",
  "points": [
    {
      "timeFromStartSec": 0.0,
      "positionsByNameDeg": {
        "front_left_hip_pitch": 0.0
      }
    }
  ]
}
```

The output can later feed `simulation`, `viewer`, `mujoco-simulation`, or
firmware bring-up tooling.

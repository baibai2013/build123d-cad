# Quadruped MVP

The MVP example intentionally uses simplified artifacts:

- Body is a box.
- Leg is a simplified three-link limb.
- PCB is a rectangular board with connector metadata.
- Battery is a mass block.
- Robot model may be URDF first, with MJCF later.
- Gait starts as a trot phase table.

The goal is not physical fidelity. The goal is a reproducible loop that can say:

```text
prototype_allowed: true/false
blockers: [...]
next_actions: [...]
```

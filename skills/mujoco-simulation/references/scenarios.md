# Scenarios

MVP scenario types:

- `stand`: stable pose hold without falling.
- `walk_flat`: flat-ground walking stability, slip, torque, and energy.
- `slope`: uphill/downhill posture and torque margin.
- `step_obstacle`: foot clearance and no-stumble check.
- `drop`: landing contact and penetration check.
- `push_disturbance`: recovery after external force.

Required scenarios should be marked `required: true`. A required failing scenario
is a gate blocker.

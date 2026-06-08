# Update Rules

Conservative heuristics:

- Real slip higher than sim slip: reduce friction estimate or increase contact damping review.
- Real torque higher than sim torque: increase actuator load scale.
- Real speed lower than sim speed: increase drivetrain loss estimate.
- Real latency higher than sim latency: increase control latency parameter.
- Real roll/pitch higher than sim: review COM/inertia and contact tuning.

Updates are suggestions, not proof. Re-run simulation and physical tests after applying.

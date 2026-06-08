# Backend Plan

MVP:

- Parse `mujoco_scenarios.yaml`.
- Validate scenario metadata deterministically.
- Produce stable reports for digital-twin gates.

Next:

- Add optional `mujoco` Python backend.
- Load MJCF from `model.mjcf`.
- Run each scenario with deterministic seeds.
- Export solver-derived contact force, penetration, torque, pose, fall, energy,
  and trajectory metrics into the same output contract.

The output contract should remain stable when replacing metadata mode with real
MuJoCo simulation.

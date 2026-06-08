---
name: mujoco-simulation
description: |
  MuJoCo-oriented robot-dog dynamics validation, MJCF scenario contracts, contact,
  terrain, actuator, stability, torque, slip, and disturbance checks for virtual
  prototypes. Use this skill when the user asks for MuJoCo, MJCF, high-fidelity
  legged-robot simulation, contact/friction validation, slope/step/drop/push
  scenarios, or serious gait simulation beyond PyBullet smoke tests.
---

# mujoco-simulation

This skill defines and evaluates MuJoCo-style dynamics scenarios for robot-dog
virtual prototypes. The MVP uses deterministic scenario metadata so tests and
digital-twin gates can run without a local MuJoCo install. It establishes the
file contract that later real `mujoco` runners will fill with solver output.

## When To Use

Use this skill for:

- MJCF/MuJoCo scenario planning and validation.
- Stand, flat-walk, slope, step-obstacle, drop, and push-disturbance checks.
- Contact/friction, foot slip, body roll/pitch, torque margin, and fall checks.
- Generating `mujoco_result.json` for `robot-dog-digital-twin` gates.

## Workflow

1. Read `<project>/mujoco_scenarios.yaml`.
2. Evaluate each scenario against stability, posture, contact, torque, slip, and energy limits.
3. Write per-scenario `*.sim_result.json` plus a project-level `mujoco_result.json`.
4. Mark blockers when any required scenario falls, exceeds posture/contact limits, or violates torque/slip thresholds.

## Commands

```bash
python skills/mujoco-simulation/scripts/run_scenarios.py skills/mujoco-simulation/examples/quadruped_mvp
python skills/mujoco-simulation/scripts/summarize_results.py skills/mujoco-simulation/examples/quadruped_mvp
```

## Rules

- Keep the MVP deterministic and conservative.
- Do not claim metadata-mode results are real MuJoCo solver output.
- Use PyBullet `simulation` for lightweight CI smoke; use this skill for MuJoCo/MJCF contracts and higher-fidelity scenario gates.
- Do not import sibling subskill code. Read files only.

## References

- `references/input-contract.md` for `mujoco_scenarios.yaml` fields.
- `references/scenarios.md` for MVP scenario definitions.
- `references/output-contract.md` for report fields.
- `references/backend-plan.md` for moving from metadata backend to real MuJoCo.
- `references/examples.md` for sample project layout.

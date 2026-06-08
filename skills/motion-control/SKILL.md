---
name: motion-control
description: |
  Executable robot-dog motion-control MVP for leg IK, gait phase generation,
  trajectory contracts, controller parameters, and simulation/firmware handoff.
  Use this skill when the user asks for FK/IK, inverse kinematics, gait
  generator, trot/walk/bound trajectories, controller parameters, motion-control
  code, or a trajectory to feed simulation, MuJoCo, or firmware.
---

# motion-control

This skill turns robot-dog kinematics and gait intent into machine-readable
motion artifacts. The MVP implements deterministic 2-link sagittal IK and simple
phase-based gait trajectories. It is a file-contract layer, not a full MPC/WBC
controller.

## When To Use

Use this skill for:

- Checking whether foot targets are reachable by the leg geometry.
- Generating initial trot/walk phase tables and joint trajectories.
- Producing `trajectory.json` and `controller_params.yaml` for simulation or firmware.
- Reporting IK blockers before gait/dynamics validation.

## Workflow

1. Read `<project>/motion_plan.yaml`.
2. Solve IK targets against link lengths and joint limits.
3. Generate a phase-based gait trajectory for the requested gait.
4. Write reports and handoff files into `<project>/reports/` and `<project>/control/`.

## Commands

```bash
python skills/motion-control/scripts/solve_ik.py skills/motion-control/examples/quadruped_mvp
python skills/motion-control/scripts/generate_gait.py skills/motion-control/examples/quadruped_mvp
```

## Rules

- Keep MVP kinematics deterministic and conservative.
- Treat unreachable required foot targets or joint-limit violations as blockers.
- Keep output trajectory format compatible with simulation/viewer-style `trajectory.json`.
- Do not claim this replaces full whole-body control, MPC, state estimation, or real-time firmware.
- Do not import sibling subskill code. Read files only.

## References

- `references/input-contract.md` for `motion_plan.yaml` fields.
- `references/ik-model.md` for MVP 2-link IK.
- `references/gait-contract.md` for phase and trajectory output.
- `references/output-contract.md` for report fields.
- `references/examples.md` for sample project layout.

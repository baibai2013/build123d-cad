# robot-dog-digital-twin

Developer notes for the robot dog digital-twin orchestrator.

This subskill is the first MVP layer for deciding whether a simplified robot dog
virtual prototype can proceed toward a physical prototype. It consumes artifacts from
existing build123d-cad domains and produces deterministic reports.

## Scope

- Reads requirements, verification matrix, and artifact reports.
- Scores mechanical, PCB reliability, electrical, dynamics, gait, and manufacturability domains.
- Runs G0-G5 gates.
- Writes failure and next-iteration reports.

## Non-Scope

- Does not generate CAD, PCB, URDF, MJCF, or trajectories.
- Does not import sibling subskill implementation code.
- Does not trigger physical manufacturing, ordering, flashing, or motor motion.

## Quick Check

```bash
pytest skills/robot-dog-digital-twin/tests/
python skills/robot-dog-digital-twin/scripts/collect_artifacts.py skills/robot-dog-digital-twin/examples/quadruped_mvp
python skills/robot-dog-digital-twin/scripts/score_design.py skills/robot-dog-digital-twin/examples/quadruped_mvp
python skills/robot-dog-digital-twin/scripts/run_gate.py skills/robot-dog-digital-twin/examples/quadruped_mvp --gate G3
```

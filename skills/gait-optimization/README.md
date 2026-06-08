# gait-optimization

Developer notes for the gait optimization subskill.

This subskill is a deterministic early gate for robot-dog virtual prototypes. It
does not replace MuJoCo, MPC, reinforcement learning, or physical walking tests.
It scores obvious gait failures and proposes safer next parameters before the
design reaches physical prototype work.

## Scope

- Score IK, phase, stand, flat-walk, posture, slip, speed, torque margin, and energy metrics.
- Compare simple candidate gait parameter sets.
- Write gait score, best-parameter, failed-candidate, trajectory summary, and markdown reports.
- Emit blockers for the digital-twin orchestrator.

## Non-Scope

- No reinforcement learning.
- No full-body controller implementation.
- No real actuator command generation.

## Quick Check

```bash
pytest skills/gait-optimization/tests/
python skills/gait-optimization/scripts/score_gait.py skills/gait-optimization/examples/quadruped_mvp
```

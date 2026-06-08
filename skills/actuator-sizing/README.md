# actuator-sizing

Developer notes for the robot-dog actuator sizing subskill.

This subskill is a deterministic early gate for robot-dog virtual prototypes. It
does not try to replace detailed motor simulation. It provides a conservative first
pass that can block obviously underpowered designs before CAD, gait, and physical
prototype work goes deeper.

## Scope

- Estimate hip/knee/ankle torque and speed requirements.
- Compare against an actuator candidate.
- Write torque and thermal margin reports.
- Emit blockers when margin is too low.

## Non-Scope

- No vendor catalog search.
- No real purchase recommendation without explicit candidate data.
- No closed-loop control simulation.

## Quick Check

```bash
pytest skills/actuator-sizing/tests/
python skills/actuator-sizing/scripts/estimate_torque.py skills/actuator-sizing/examples/quadruped_mvp
```

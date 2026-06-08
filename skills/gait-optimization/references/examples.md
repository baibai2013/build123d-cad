# Examples

Run the intentionally failing example:

```bash
python skills/gait-optimization/scripts/score_gait.py skills/gait-optimization/examples/quadruped_mvp
```

Expected result:

```text
gait valid=False ...
```

The example fails flat walk, posture, slip, speed, torque margin, and energy checks
on purpose. It verifies the blocker path used by the digital twin.

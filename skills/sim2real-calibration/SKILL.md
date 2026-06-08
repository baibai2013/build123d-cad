---
name: sim2real-calibration
description: |
  Sim-to-real calibration skill for robot-dog virtual prototypes. Use this skill
  when comparing simulation logs against physical prototype logs, estimating
  friction/mass/latency/torque scale/contact parameter corrections, reducing
  sim-real gap, or generating parameter updates for MuJoCo/PyBullet/digital twin.
---

# sim2real-calibration

This skill compares simulation metrics with measured prototype metrics and
proposes conservative parameter updates. The MVP is file-based and does not
connect to hardware. It helps reduce the sim-real gap after a physical prototype
exists.

## When To Use

Use this skill for:

- Comparing simulated and measured speed, slip, torque, roll/pitch, and latency.
- Producing parameter update suggestions for simulation/MuJoCo.
- Blocking digital-twin trust when sim-real error is too high.
- Creating calibration reports after physical testing.

## Workflow

1. Read `<project>/calibration_dataset.yaml`.
2. Compare `simulation` and `real` metrics against tolerances.
3. Estimate conservative parameter updates.
4. Write calibration report artifacts into `<project>/reports/`.

## Commands

```bash
python skills/sim2real-calibration/scripts/compare_logs.py skills/sim2real-calibration/examples/quadruped_mvp
python skills/sim2real-calibration/scripts/propose_parameter_update.py skills/sim2real-calibration/examples/quadruped_mvp
```

## Rules

- Never claim calibrated parameters are validated without a follow-up simulation and physical re-test.
- Treat missing real logs or excessive error in required metrics as blockers.
- Keep updates conservative and bounded.
- Do not import sibling subskill code. Read files only.

## References

- `references/input-contract.md` for `calibration_dataset.yaml` fields.
- `references/metrics.md` for comparison metrics.
- `references/update-rules.md` for parameter update heuristics.
- `references/output-contract.md` for report fields.
- `references/examples.md` for sample project layout.

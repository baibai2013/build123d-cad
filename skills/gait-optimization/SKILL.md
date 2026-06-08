---
name: gait-optimization
description: |
  Gait validation, scoring, and parameter recommendation for robot-dog virtual
  prototypes. Use this skill whenever the user asks whether walking logic is
  reasonable, gait parameters are stable, flat-walk/slope tests pass, foot slip is
  too high, body roll/pitch is excessive, or the next gait iteration should be proposed.
---

# gait-optimization

This skill checks early gait reasonableness for robot-dog virtual prototypes. It
consumes gait parameters and validation metrics, then writes deterministic gait
score, failed-candidate, and next-parameter reports.

## When To Use

Use this skill for:

- Single-leg IK, four-leg phase, stand, and flat-walk validation.
- Roll/pitch, foot slip, speed, torque margin, and cost-of-transport scoring.
- Comparing simple candidate gait parameters before deeper simulation.
- Producing `gait_score.json`, `best_gait_params.yaml`, and `failed_candidates.json`
  for `robot-dog-digital-twin` gates.

## Workflow

1. Read `<project>/gait_validation.yaml`.
2. Score current gait validation metrics.
3. Mark blockers for falls, failed IK, incomplete phase coverage, unstable posture, high slip, low torque margin, or low speed.
4. Score candidate gait parameter sets when present.
5. Write reports into `<project>/reports/`.

## Commands

```bash
python skills/gait-optimization/scripts/score_gait.py skills/gait-optimization/examples/quadruped_mvp
python skills/gait-optimization/scripts/search_params.py skills/gait-optimization/examples/quadruped_mvp
python skills/gait-optimization/scripts/write_report.py skills/gait-optimization/examples/quadruped_mvp
```

## Rules

- Keep MVP checks deterministic and conservative.
- Treat failed IK, falling during flat walk, stand time below target, body roll/pitch above limits, foot slip above limit, or torque margin below 20% as blockers.
- Do not run reinforcement learning or claim sim-to-real stability from this report alone.
- Do not import sibling subskill code. Read files only.

## References

- `references/input-contract.md` for `gait_validation.yaml` fields.
- `references/gait-levels.md` for validation levels.
- `references/stability-metrics.md` for scoring thresholds.
- `references/output-contract.md` for report fields.
- `references/examples.md` for sample project layout.

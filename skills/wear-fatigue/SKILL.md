---
name: wear-fatigue
description: |
  Wear, fatigue, bearing life, harness bend, connector retention, foot pad wear,
  and maintenance interval checks for robot-dog and hardware virtual prototypes.
  Use this skill when the user asks whether gears, bearings, joints, feet, wires,
  connectors, or moving mechanical interfaces will wear out, fatigue, loosen, or
  block physical prototype release.
---

# wear-fatigue

This skill checks early wear and fatigue risks for robot-dog virtual prototypes.
The MVP consumes deterministic wear metadata and writes reports that can be used
by `robot-dog-digital-twin` gates. It does not replace physical endurance tests,
tribology analysis, or supplier-qualified reducer/bearing data.

## When To Use

Use this skill for:

- Gear or reducer contact stress and service life checks.
- Bearing L10 life and radial/axial load checks.
- Foot pad wear interval and replaceability checks.
- Joint limit impact and screw loosening risk checks.
- Wire harness bend radius, motion envelope, and pinch risk checks.
- Connector mating-cycle, vibration retention, and strain relief checks.

## Workflow

1. Read `<project>/wear_inputs.yaml`.
2. Evaluate wear interfaces against declared limits and target maintenance hours.
3. Mark blockers for short life, excessive stress, bend-radius violations, pinch risk, missing retention, or missing strain relief.
4. Write reports into `<project>/reports/`.

## Commands

```bash
python skills/wear-fatigue/scripts/estimate_wear.py skills/wear-fatigue/examples/quadruped_mvp
python skills/wear-fatigue/scripts/estimate_fatigue.py skills/wear-fatigue/examples/quadruped_mvp
```

## Rules

- Keep MVP checks deterministic and conservative.
- Treat component service life below `target_maintenance_hours` as a blocker.
- Treat bearing L10 life below the target, gear contact stress above allowable, or harness bend radius below minimum as blockers.
- Do not claim the MVP predicts final product lifetime; it is a pre-prototype gate and file contract.
- Do not import sibling subskill code. Read files only.

## References

- `references/input-contract.md` for `wear_inputs.yaml` fields.
- `references/wear-models.md` for MVP scoring rules.
- `references/bearing-life.md` for bearing L10 expectations.
- `references/output-contract.md` for report fields.
- `references/examples.md` for sample project layout.

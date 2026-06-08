---
name: fea
description: |
  Structural FEA gate, static-load, deflection, modal, and drop-risk checks for
  robot-dog and hardware virtual prototypes. Use this skill whenever the user asks
  whether a part is strong enough, too flexible, likely to break, needs a finite
  element check, or should be blocked before physical prototype because of stress,
  safety factor, deflection, or modal frequency.
---

# fea

This skill checks early structural strength and stiffness risks for robot-dog
virtual prototypes. The MVP consumes FEA case metadata and writes deterministic
reports. It does not run a solver yet; it provides a stable file contract for
later CalculiX/Gmsh or FreeCAD FEM integration.

## When To Use

Use this skill for:

- Static stress and safety-factor checks.
- Deflection and stiffness checks.
- Modal frequency checks against gait excitation.
- Drop or landing impact risk summaries.
- Producing `fea_report.json` for `robot-dog-digital-twin` gates.

## Workflow

1. Read `<project>/fea_cases.yaml`.
2. Evaluate each part/case against material yield strength, safety factor, deflection, and modal limits.
3. Mark blockers for low safety factor, excessive deflection, or modal frequency too close to gait excitation.
4. Write reports into `<project>/reports/`.

## Commands

```bash
python skills/fea/scripts/run_static_case.py skills/fea/examples/quadruped_mvp
python skills/fea/scripts/summarize_fea.py skills/fea/examples/quadruped_mvp
```

## Rules

- Keep MVP checks deterministic and conservative.
- Treat safety factor below 2.0, deflection above the declared limit, or modal frequency ratio below 2.0 as blockers.
- Do not claim this replaces solver-backed FEA or physical load testing.
- Do not import sibling subskill code. Read files only.

## References

- `references/input-contract.md` for `fea_cases.yaml` fields.
- `references/load-cases.md` for MVP case definitions.
- `references/materials.md` for material defaults.
- `references/output-contract.md` for report fields.
- `references/examples.md` for sample project layout.

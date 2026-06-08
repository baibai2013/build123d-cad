# fea

Developer notes for the structural FEA subskill.

This subskill is a deterministic early gate for robot-dog virtual prototypes. It
does not run a real finite-element solver in the MVP. It checks solver-like
metadata and creates a stable report contract that can later be backed by
CalculiX/Gmsh, FreeCAD FEM, or another headless solver.

## Scope

- Check stress, yield margin, safety factor, deflection, and modal frequency.
- Summarize drop/landing load cases.
- Emit blockers for the digital-twin orchestrator.

## Non-Scope

- No mesh generation in the MVP.
- No solver execution in the MVP.
- No fatigue-life model; use `wear-fatigue` later for life/maintenance estimates.

## Quick Check

```bash
pytest skills/fea/tests/
python skills/fea/scripts/run_static_case.py skills/fea/examples/quadruped_mvp
```

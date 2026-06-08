---
name: integration
description: |
  Robot-dog integration, bring-up, HIL planning, prototype readiness, hardware
  gate, assembly test, first power-on checklist, data capture, and physical test
  safety validation. Use this skill when the user asks whether a prototype is
  ready for assembly, power-on, HIL, bring-up, hardware testing, or real-world
  data collection after digital-twin gates.
---

# integration

This skill checks whether a robot-dog project is ready for safe physical
integration. The MVP is a dry-run gate: it writes bring-up/HIL checklists and
blocks unsafe first power-on conditions. It does not power hardware, flash
firmware, move actuators, or collect real logs.

## When To Use

Use this skill for:

- Physical prototype readiness checks after digital-twin validation.
- First power-on and bring-up checklists.
- HIL/test bench planning.
- Required human gates before assembly, power, firmware flash, and motor motion.
- Data-capture plan for sim2real calibration.

## Workflow

1. Read `<project>/integration_plan.yaml`.
2. Check digital-twin, manufacturing, safety, firmware, assembly, and testbench prerequisites.
3. Generate bring-up report, HIL plan, and data-capture checklist.
4. Return non-zero when any required human or safety gate is missing.

## Commands

```bash
python skills/integration/scripts/check_bringup_readiness.py skills/integration/examples/quadruped_mvp
python skills/integration/scripts/write_hil_plan.py skills/integration/examples/quadruped_mvp
```

## Rules

- Never execute physical actions. This skill only reports readiness.
- Treat missing emergency stop, current-limited supply, fire-safe test area, firmware dry-run, or human approval as blockers.
- Physical motor motion requires a separate explicit human gate.
- Do not import sibling subskill code. Read files only.

## References

- `references/input-contract.md` for `integration_plan.yaml` fields.
- `references/bringup-gates.md` for safety gates.
- `references/data-capture.md` for sim2real logs.
- `references/output-contract.md` for report fields.
- `references/examples.md` for sample project layout.

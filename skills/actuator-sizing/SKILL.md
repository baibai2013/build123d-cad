---
name: actuator-sizing
description: |
  Actuator sizing and torque/speed/thermal margin checks for robot-dog and legged
  robot virtual prototypes. Use this skill whenever the user needs motor, gearbox,
  actuator torque, speed, reduction ratio, thermal margin, knee/hip/ankle sizing,
  or blocker reports before digital-twin gates.
---

# actuator-sizing

This skill estimates whether a simplified robot-dog actuator set has enough torque,
speed, and thermal margin for early digital-twin gates. It consumes requirement
contracts and architecture assumptions, then writes machine-readable actuator reports.

## When To Use

Use this skill for:

- Robot-dog hip/knee/ankle torque margin checks.
- Selecting or validating actuator specs before CAD/simulation iteration.
- Producing `actuator_spec.yaml` and `torque_margin.json`.
- Feeding `robot-dog-digital-twin` G2/G3 blocker decisions.

## Workflow

1. Read `requirements.yaml` for mass, payload, speed, and slope targets.
2. Read `architecture.yaml` for leg count and joints per leg.
3. Load an actuator preset or use the built-in MVP preset.
4. Estimate joint torque and speed requirements.
5. Write `reports/actuator_spec.yaml`, `reports/torque_margin.json`, and
   `reports/actuator_sizing_report.md`.

## Commands

```bash
python skills/actuator-sizing/scripts/estimate_torque.py skills/actuator-sizing/examples/quadruped_mvp
python skills/actuator-sizing/scripts/write_report.py skills/actuator-sizing/examples/quadruped_mvp
```

## Rules

- Keep calculations deterministic and conservative.
- Treat torque margin below 20% as a blocker.
- Do not select real purchasable parts unless a user explicitly provides a candidate list.
- Do not import sibling subskill code. Read requirement files only.

## References

- `references/torque-model.md` for formulas.
- `references/thermal-margin.md` for MVP heat checks.
- `references/output-contract.md` for report fields.
- `references/examples.md` for sample project layout.

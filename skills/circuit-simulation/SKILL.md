---
name: circuit-simulation
description: |
  Circuit, power budget, protection, and thermal risk checks for robot-dog and
  hardware virtual prototypes. Use this skill whenever the user asks whether a
  circuit is reasonable, power rails have enough margin, motor current is safe,
  protection is adequate, or PCB/electronics thermal risk blocks a physical prototype.
---

# circuit-simulation

This skill checks early electrical reasonableness for robot-dog virtual prototypes.
It consumes a circuit metadata contract, then writes deterministic circuit, power,
thermal, and protection reports.

## When To Use

Use this skill for:

- Battery, fuse, emergency-stop, reverse-polarity, TVS, and undervoltage checks.
- Power rail current and power margin checks.
- Motor driver peak/continuous current checks.
- Thermal risk estimates for regulators, motor drivers, and MOSFETs.
- Producing `circuit_check.json`, `power_budget.json`, and `thermal_report.json`
  for `robot-dog-digital-twin` gates.

## Workflow

1. Read `<project>/circuit_requirements.yaml`.
2. Check ERC/DRC status when provided.
3. Check battery voltage/current limits and total power budget.
4. Check each power rail for current margin and regulator thermal risk.
5. Check motor driver current margin.
6. Check protection coverage.
7. Write reports into `<project>/reports/`.

## Commands

```bash
python skills/circuit-simulation/scripts/check_power_budget.py skills/circuit-simulation/examples/quadruped_mvp
python skills/circuit-simulation/scripts/check_protection.py skills/circuit-simulation/examples/quadruped_mvp
python skills/circuit-simulation/scripts/write_report.py skills/circuit-simulation/examples/quadruped_mvp
```

## Rules

- Keep MVP checks deterministic and conservative.
- Treat any failed ERC/DRC, missing emergency stop, missing fuse, or current margin below 20% as a blocker.
- Treat estimated component temperature above its declared limit as a blocker.
- Do not place orders, energize hardware, or claim physical safety from this report alone.
- Do not import sibling subskill code. Read files only.

## References

- `references/input-contract.md` for `circuit_requirements.yaml` fields.
- `references/power-rails.md` for power budget rules.
- `references/protection-rules.md` for safety/protection checks.
- `references/thermal-rules.md` for MVP heat estimates.
- `references/output-contract.md` for report fields.
- `references/examples.md` for sample project layout.

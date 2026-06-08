---
name: firmware
description: |
  Robot-dog firmware dry-run planning and validation skill for MCU target,
  motor-control loop, CAN protocol, safety state machine, calibration contract,
  build manifest, and hardware bring-up gates. Use this skill when the user asks
  for embedded firmware, motor firmware, FOC loop, CAN frames, calibration,
  firmware project scaffolding, or safe pre-flash validation.
---

# firmware

This skill defines a safe firmware dry-run contract for robot-dog prototypes. The
MVP validates firmware requirements and emits project manifests, CAN frame specs,
and calibration placeholders. It does not compile vendor firmware, flash devices,
spin motors, or interact with hardware.

## When To Use

Use this skill for:

- MCU/firmware project manifest planning.
- Motor-control loop and bus-rate sanity checks.
- CAN frame and telemetry contract generation.
- Safety-state, emergency-stop, undervoltage, overcurrent, and thermal gates.
- Calibration manifest requirements before hardware bring-up.

## Workflow

1. Read `<project>/firmware_plan.yaml`.
2. Validate target MCU, control loop, bus, safety, and calibration requirements.
3. Write reports into `<project>/reports/` and firmware artifacts into `<project>/firmware/`.
4. Return non-zero when required safety/build prerequisites are missing.

## Commands

```bash
python skills/firmware/scripts/generate_project.py skills/firmware/examples/quadruped_mvp
python skills/firmware/scripts/run_firmware_tests.py skills/firmware/examples/quadruped_mvp
```

## Rules

- Never flash, upload, power hardware, or move motors without explicit separate tooling and user confirmation.
- Treat missing emergency stop, undervoltage, overcurrent, or calibration as blockers.
- Keep this MVP deterministic and hardware-free.
- Do not import sibling subskill code. Read files only.

## References

- `references/input-contract.md` for `firmware_plan.yaml` fields.
- `references/safety-gates.md` for blockers.
- `references/can-contract.md` for CAN frame output.
- `references/output-contract.md` for report fields.
- `references/examples.md` for sample project layout.

---
name: pcb-mechanical-reliability
description: |
  PCB mechanical reliability checks for robot-dog and hardware virtual prototypes.
  Use this skill whenever the user asks whether a PCB is mechanically reasonable,
  stiff enough, supported well, clear of the enclosure, safe for connector loads,
  or suitable for vibration/drop before a physical prototype.
---

# pcb-mechanical-reliability

This skill checks early PCB mechanical reliability for robot-dog virtual prototypes.
It consumes board geometry and mounting metadata, then writes deterministic fit,
clearance, stiffness, and connector-risk reports.

## When To Use

Use this skill for:

- PCB stiffness, flex, mounting hole, and standoff checks.
- Connector clearance, cable bend radius, and strain relief checks.
- Board-to-enclosure fit risk before CAD/PCB iteration goes deeper.
- Producing `pcb_fit.json`, `pcb_reliability_report.json`, and
  `connector_clearance.json` for `robot-dog-digital-twin` gates.

## Workflow

1. Read `<project>/pcb_mechanical.yaml`.
2. Check board dimensions, thickness, edge clearance, and enclosure clearance.
3. Check mounting holes and standoff spacing.
4. Estimate board flex from unsupported span and vibration load.
5. Check connector clearance, nearest support, cable bend radius, and strain relief.
6. Write reports into `<project>/reports/`.

## Commands

```bash
python skills/pcb-mechanical-reliability/scripts/check_pcb_fit.py skills/pcb-mechanical-reliability/examples/quadruped_mvp
python skills/pcb-mechanical-reliability/scripts/write_report.py skills/pcb-mechanical-reliability/examples/quadruped_mvp
```

## Rules

- Keep MVP checks deterministic and conservative.
- Treat enclosure clearance below 2 mm as a blocker.
- Treat excessive board flex, insufficient standoffs, or unsupported power connectors as blockers.
- Do not run FEA or import CAD/PCB sibling code in this skill. Read files only.
- Use this report as an early gate, not as a replacement for physical vibration/drop testing.

## References

- `references/input-contract.md` for `pcb_mechanical.yaml` fields.
- `references/standoff-rules.md` for mounting and board-flex rules.
- `references/connector-loads.md` for connector and cable checks.
- `references/output-contract.md` for report fields.
- `references/examples.md` for sample project layout.

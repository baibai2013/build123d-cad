---
name: electronics-bom
description: |
  Electronics BOM and robot-dog component selection MVP. Use this skill when the
  user asks for electronic BOM, MCU/driver/encoder/power/connector selection,
  JLCPCB/LCSC-ready part candidates, curated robot electronics library, BOM
  rationale, availability checks, or component choices to feed pcb, circuit
  simulation, firmware, and digital-twin gates.
owner: hardware
status: active
phase: P1-mvp
since: 2026-06-02
updated: 2026-06-08
---

# electronics-bom

This skill selects early robot-dog electronics BOM candidates from an offline
curated catalog and writes machine-readable BOM artifacts. The MVP is a stable
file contract for `pcb`, `circuit-simulation`, `firmware`, and
`robot-dog-digital-twin`; it does not perform live purchasing or guarantee
current stock/pricing.

## When To Use

Use this skill for:

- MCU, motor driver, encoder, IMU, regulator, battery connector, and protection part candidates.
- Producing a BOM contract before PCB layout.
- Selecting JLCPCB/LCSC-friendly common parts from an offline library.
- Writing `electronics_bom.json` and selection rationale for downstream skills.

## Workflow

1. Read `<project>/bom_request.yaml`.
2. Match requested categories against the curated catalog.
3. Score candidates by fit, voltage/current margin, package preference, assembly tier, and stock status.
4. Write reports into `<project>/reports/` and selected parts into `<project>/electrical/library/`.

## Commands

```bash
python skills/electronics-bom/scripts/select_parts.py skills/electronics-bom/examples/quadruped_mvp
python skills/electronics-bom/scripts/check_availability.py skills/electronics-bom/examples/quadruped_mvp
```

## Rules

- Treat unavailable required categories as blockers.
- Prefer `jlcpcb_basic` over `jlcpcb_extended` when scores are otherwise close.
- Do not claim live prices or stock unless a live connector is explicitly added and run.
- Do not place orders. Query/selection is not a transaction.
- Do not import sibling subskill code. Read files only.

## References

- `references/input-contract.md` for `bom_request.yaml` fields.
- `references/catalog-rules.md` for scoring and fallback rules.
- `references/output-contract.md` for report fields.
- `references/examples.md` for sample project layout.

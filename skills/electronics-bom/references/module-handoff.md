# Module Handoff

Completed module: `electronics-bom`

Purpose:

- Select early robot-dog electronics part candidates from an offline curated catalog.
- Produce BOM artifacts for PCB, circuit simulation, firmware, and digital-twin gates.

Inputs:

- `<project>/bom_request.yaml`

Outputs:

- `<project>/reports/electronics_bom.json`
- `<project>/reports/availability_report.json`
- `<project>/reports/selection_rationale.md`
- `<project>/electrical/library/selected_parts.json`

Verification:

- Run `python -m pytest skills/electronics-bom/tests/`.

Context handoff:

- After this module is complete, clear active context and load only this handoff
  plus the next target skill files before continuing.

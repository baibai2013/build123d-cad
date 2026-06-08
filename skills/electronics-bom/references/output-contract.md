# Output Contract

`select_parts.py` writes:

- `reports/electronics_bom.json`
- `reports/selection_rationale.md`
- `electrical/library/selected_parts.json`

`check_availability.py` writes:

- `reports/availability_report.json`

Report fields:

- `project`
- `valid`
- `blockers`
- `warnings`
- `selected_parts`
- `next_actions`

`valid: false` means downstream PCB/circuit/firmware work should not freeze part
choices.

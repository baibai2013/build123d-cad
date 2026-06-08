# Output Contract

Reports are written to `<project>/reports/`.

```text
reports/
  circuit_check.json
  power_budget.json
  thermal_report.json
  protection_checklist.md
  circuit_simulation_report.md
```

`circuit_check.json` is the primary compact artifact.

Required top-level fields:

- `project`
- `valid`
- `blockers`
- `warnings`
- `checks`
- `battery`
- `power_rails`
- `motor_drivers`
- `thermal`
- `protection`
- `next_actions`

`power_budget.json` focuses on battery and rail margins.

`thermal_report.json` focuses on component temperature estimates.

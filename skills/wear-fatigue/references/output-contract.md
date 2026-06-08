# Output Contract

`estimate_wear.py` writes:

- `reports/wear_report.json`
- `reports/maintenance_interval.md`
- `reports/wear_fatigue_report.md`

`estimate_fatigue.py` writes:

- `reports/fatigue_report.json`
- `reports/maintenance_interval.md`
- `reports/wear_fatigue_report.md`

The JSON reports include:

- `project`
- `valid`
- `blockers`
- `warnings`
- `summary`
- `components`
- `next_actions`

`valid: false` means the digital twin gate must not allow physical prototype
release until blockers are resolved.

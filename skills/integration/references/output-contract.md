# Output Contract

`check_bringup_readiness.py` writes:

- `reports/integration_checklist.json`
- `reports/bringup_report.md`

`write_hil_plan.py` writes:

- `reports/hil_plan.md`
- `reports/data_capture_checklist.md`

`valid: false` means physical integration must not proceed beyond the reported
stage.

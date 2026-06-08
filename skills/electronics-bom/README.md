# electronics-bom

Offline curated electronics BOM selection for robot-dog MVP projects.

Run the example:

```bash
python skills/electronics-bom/scripts/select_parts.py skills/electronics-bom/examples/quadruped_mvp
python skills/electronics-bom/scripts/check_availability.py skills/electronics-bom/examples/quadruped_mvp
```

Outputs:

- `reports/electronics_bom.json`
- `reports/availability_report.json`
- `reports/selection_rationale.md`
- `electrical/library/selected_parts.json`

This MVP does not perform live stock/price lookup or purchasing.

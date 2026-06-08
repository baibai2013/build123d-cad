# Output Contract

Reports are written to `<project>/reports/`.

```text
reports/
  fea_report.json
  static_case_report.json
  fea_checklist.md
```

`fea_report.json` is the primary artifact for digital-twin gates.

Required top-level fields:

- `project`
- `valid`
- `blockers`
- `warnings`
- `summary`
- `cases`
- `next_actions`

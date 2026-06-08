# Output Contract

Reports are written to `<project>/reports/`.

```text
reports/
  pcb_fit.json
  pcb_reliability_report.json
  connector_clearance.json
  pcb_mechanical_report.md
```

`pcb_fit.json` is the primary compact artifact.

Required top-level fields:

- `project`
- `valid`
- `blockers`
- `scores`
- `board`
- `mounting`
- `flex`
- `connectors`
- `next_actions`

`pcb_reliability_report.json` carries the same check data with a `domain` field for
digital-twin artifact collection.

`connector_clearance.json` is a connector-focused sidecar for mechanical/CAD iteration.

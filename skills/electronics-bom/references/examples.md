# Examples

Example project:

```text
skills/electronics-bom/examples/quadruped_mvp/
  bom_request.yaml
  reports/
    electronics_bom.json
    availability_report.json
    selection_rationale.md
  electrical/library/
    selected_parts.json
```

The bundled example is intentionally mixed: most categories pass, one required
high-current driver request fails to demonstrate blocker behavior.

# Output Contract

The skill writes:

```text
reports/actuator_spec.yaml
reports/torque_margin.json
reports/actuator_sizing_report.md
```

`torque_margin.json` fields:

```json
{
  "valid": false,
  "minimum_margin_pct": 8,
  "blockers": ["front_knee torque margin below threshold"],
  "joints": {
    "hip": {"required_torque_nm": 4.2, "available_torque_nm": 6.0, "margin_pct": 42.8}
  }
}
```

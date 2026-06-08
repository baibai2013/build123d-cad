# Thermal Margin

MVP thermal check:

```text
thermal_margin_pct = (continuous_torque_nm - estimated_continuous_torque_nm)
                     / continuous_torque_nm * 100
```

Treat thermal margin below 20% as a blocker in early gates.

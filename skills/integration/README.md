# integration

Robot-dog physical integration and bring-up dry-run gate.

Run the example:

```bash
python skills/integration/scripts/check_bringup_readiness.py skills/integration/examples/quadruped_mvp
python skills/integration/scripts/write_hil_plan.py skills/integration/examples/quadruped_mvp
```

Outputs are written to `<project>/reports/`.

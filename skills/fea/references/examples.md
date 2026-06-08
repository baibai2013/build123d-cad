# Examples

Run the intentionally failing example:

```bash
python skills/fea/scripts/run_static_case.py skills/fea/examples/quadruped_mvp
```

Expected result:

```text
fea valid=False ...
```

The example has low safety factor, excessive deflection, and modal ratio blockers
on purpose.

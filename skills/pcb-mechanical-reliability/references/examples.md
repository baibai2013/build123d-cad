# Examples

Run the intentionally failing example:

```bash
python skills/pcb-mechanical-reliability/scripts/check_pcb_fit.py skills/pcb-mechanical-reliability/examples/quadruped_mvp
```

Expected result:

```text
pcb mechanical valid=False ...
```

The example is under-supported on purpose. It verifies the blocker path used by
`robot-dog-digital-twin`.

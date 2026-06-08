# Examples

Run the intentionally failing example:

```bash
python skills/circuit-simulation/scripts/check_power_budget.py skills/circuit-simulation/examples/quadruped_mvp
```

Expected result:

```text
circuit valid=False ...
```

The example has failed ERC, missing emergency stop, weak motor drivers, and hot
power electronics on purpose. It verifies the blocker path used by the digital twin.

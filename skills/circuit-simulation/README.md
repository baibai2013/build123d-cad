# circuit-simulation

Developer notes for the circuit simulation subskill.

This subskill is a deterministic early gate for robot-dog virtual prototypes. It
does not replace SPICE, EMC testing, or physical thermal measurement. It blocks
obviously risky power, protection, and thermal designs before prototype work goes
deeper.

## Scope

- Check ERC/DRC status.
- Check battery and total current budget.
- Check power rail current margins.
- Check motor driver current margins.
- Estimate component thermal risk.
- Check protection coverage.
- Emit blocker reports for the digital-twin orchestrator.

## Non-Scope

- No full SPICE transient simulation in the MVP.
- No signal-integrity or EMI simulation.
- No real hardware energizing or manufacturing action.

## Quick Check

```bash
pytest skills/circuit-simulation/tests/
python skills/circuit-simulation/scripts/check_power_budget.py skills/circuit-simulation/examples/quadruped_mvp
```

# pcb-mechanical-reliability

Developer notes for the PCB mechanical reliability subskill.

This subskill is a deterministic early gate for robot-dog virtual prototypes. It
does not replace detailed structural simulation or physical vibration testing. It
blocks obviously risky board layouts before the design reaches physical prototype
work.

## Scope

- Check PCB envelope and enclosure clearance.
- Check mounting hole and standoff layout.
- Estimate board flex from unsupported span and vibration load.
- Check connector height clearance, nearby support, cable bend radius, and strain relief.
- Emit blocker reports for the digital-twin orchestrator.

## Non-Scope

- No FEA mesh generation.
- No KiCad or tscircuit parsing in the MVP.
- No purchase or manufacturing order decisions.

## Quick Check

```bash
pytest skills/pcb-mechanical-reliability/tests/
python skills/pcb-mechanical-reliability/scripts/check_pcb_fit.py skills/pcb-mechanical-reliability/examples/quadruped_mvp
```

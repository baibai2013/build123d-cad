# requirements-verification

Developer notes for the requirement contract and verification matrix subskill.

This subskill is the G0/G1 input layer for digital-twin workflows. It produces the
contract files that downstream skills consume, especially `robot-dog-digital-twin`.

## Scope

- Generate starter project contract files.
- Validate required requirement groups and measurable target fields.
- Validate verification matrix entries, sources, thresholds, and blocker flags.
- Write deterministic validation reports.

## Non-Scope

- Does not generate CAD, PCB, firmware, or simulation artifacts.
- Does not score a full design. That belongs to `robot-dog-digital-twin`.
- Does not approve physical manufacturing.

## Quick Check

```bash
pytest skills/requirements-verification/tests/
python skills/requirements-verification/scripts/validate_contract.py skills/requirements-verification/examples/quadruped_mvp
```

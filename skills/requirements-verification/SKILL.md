---
name: requirements-verification
description: |
  Requirement contract and verification matrix authoring for hardware and robot-dog
  digital-twin projects. Use when the user needs requirements.yaml, verification_matrix.yaml,
  architecture.yaml, risk_register.md, measurable gates, blocker thresholds, or validation
  readiness before robot-dog-digital-twin scoring.
---

# requirements-verification

This skill turns vague robot or hardware goals into a machine-checkable contract. It
creates and validates `requirements.yaml`, `verification_matrix.yaml`, `architecture.yaml`,
and `risk_register.md` before downstream CAD, PCB, simulation, or digital-twin gates run.

## When To Use

Use this skill for:

- Defining measurable requirements for a robot dog or hardware prototype.
- Creating a verification matrix that maps goals to validating domains and artifacts.
- Checking whether a project can enter digital-twin G0/G1 validation.
- Producing inputs consumed by `robot-dog-digital-twin`.

## Workflow

1. Capture top-level requirements in `requirements.yaml`.
2. Map each target to a verification item in `verification_matrix.yaml`.
3. Add architecture assumptions in `architecture.yaml`.
4. Record unverified assumptions and physical-test-only risks in `risk_register.md`.
5. Run `scripts/validate_contract.py` and fix errors before downstream gates.

## Commands

```bash
python skills/requirements-verification/scripts/new_contract.py /path/to/project --name quadruped_mvp
python skills/requirements-verification/scripts/validate_contract.py /path/to/project
```

## Outputs

Project inputs:

```text
requirements.yaml
verification_matrix.yaml
architecture.yaml
risk_register.md
```

Validation reports:

```text
reports/requirements_validation.json
reports/requirements_validation.md
```

## Rules

- Every critical target must be measurable.
- Every blocker-class verification item must declare a source domain and pass condition.
- Do not allow physical prototype gates when requirements or verification matrix are incomplete.
- Do not import sibling subskill code. Handoff is by files only.

## References

- `references/contract-schema.md` for accepted fields.
- `references/verification-matrix.md` for matrix conventions.
- `references/risk-register.md` for risk wording and escalation.
- `references/quadruped-contract.md` for the MVP robot-dog contract.

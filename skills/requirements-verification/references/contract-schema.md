# Requirement Contract Schema

The MVP contract uses four project-root files:

```text
requirements.yaml
verification_matrix.yaml
architecture.yaml
risk_register.md
```

## requirements.yaml

Required top-level keys:

- `version`
- `project`
- `targets`
- `constraints`

Required target keys:

- `mass_kg`
- `payload_kg`
- `runtime_min`
- `flat_walk_speed_mps`

The validator accepts additional domain-specific target keys, but critical targets must
be numeric or boolean values. Use `null` only for goals that are explicitly not ready.

## verification_matrix.yaml

The matrix is a domain-keyed mapping. Each domain contains named checks.

Each check must include:

- `source`: validating domain or subskill.
- One pass condition: `required`, `limit_min`, `limit_max`, or `equals`.

Recommended optional fields:

- `artifact`: expected report path or report name.
- `blocker`: true when failure blocks physical prototype gates.
- `target`: requirement target key this check verifies.

## architecture.yaml

The MVP validator requires:

- `version`
- `system`
- `domains`

Use this file for high-level robot morphology, actuation assumptions, electronics
architecture, battery assumptions, and manufacturing strategy.

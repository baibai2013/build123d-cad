# Input Contract

`bom_request.yaml` describes required electronics categories and constraints.

Required top-level fields:

```yaml
project: quadruped_mvp
constraints:
  assembly_preference: jlcpcb_basic
requirements: []
```

Each requirement should include:

- `category`
- `quantity`
- `required`
- optional voltage/current/interface/package constraints

Use UTF-8 for all files.

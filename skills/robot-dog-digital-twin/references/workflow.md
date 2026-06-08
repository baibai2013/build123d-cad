# Workflow

The digital-twin loop is:

```text
requirements
  -> artifacts
  -> gates
  -> design score
  -> failure report
  -> next iteration plan
```

The orchestrator treats all domain outputs as files. It does not call Python modules
from sibling subskills.

## Project Layout

```text
<project>/
  requirements.yaml
  verification_matrix.yaml
  artifacts.json
  mechanical/
  electrical/
  simulation/
  control/
  manufacturing/
  reports/
```

`reports/` is created by the scripts when needed.

# Output Contract

Reports are written to `<project>/reports/`.

```text
reports/
  gait_score.json
  best_gait_params.yaml
  failed_candidates.json
  trajectory.json
  gait_optimization_report.md
```

`gait_score.json` is the primary compact artifact.

Required top-level fields:

- `project`
- `valid`
- `score`
- `blockers`
- `warnings`
- `levels`
- `metrics`
- `current_params`
- `best_candidate`
- `next_actions`

`best_gait_params.yaml` should be safe to feed into the next design iteration.

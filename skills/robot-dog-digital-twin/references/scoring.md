# Scoring

MVP weights:

```yaml
mechanical: 20
pcb_reliability: 15
electrical: 20
dynamics: 20
gait: 15
manufacturability: 10
```

The scoring script uses deterministic report fields. Missing reports receive partial
or zero credit and are surfaced as risks.

Physical prototype should require:

```text
total_score >= 85
no blockers
```

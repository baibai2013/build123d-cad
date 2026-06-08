# Verification Matrix

The verification matrix connects goals to deterministic evidence.

Good matrix entries answer four questions:

1. What target is being verified?
2. Which domain produces the evidence?
3. What artifact or report contains the evidence?
4. What pass condition decides whether this is acceptable?

Example:

```yaml
dynamics:
  stand_stable_seconds:
    target: stand_stable_seconds
    source: simulation
    artifact: simulation/stand_result.json
    limit_min: 30
    blocker: true
```

`blocker: true` means failure prevents G3/G5 digital-twin approval. Scores can help
rank versions, but blockers decide release gates.

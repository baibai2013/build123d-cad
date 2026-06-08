# Risk Register

The risk register records assumptions that cannot yet be fully validated virtually.

Use short entries with:

- risk id
- affected domain
- failure mode
- current mitigation
- required future evidence

Example:

```markdown
| ID | Domain | Risk | Mitigation | Evidence Needed |
|---|---|---|---|---|
| R-001 | dynamics | PyBullet contact model may overestimate stability | Require MuJoCo rerun before G5 | MuJoCo slope and push tests |
```

Physical manufacturing, ordering, flashing, and motor motion still require explicit
human confirmation even when all virtual risks are closed.

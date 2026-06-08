---
name: robot-dog-digital-twin
description: |
  Mechanical dog digital-twin orchestrator. Use this skill whenever the user mentions
  robot dog digital twins, virtual prototypes, design gates before physical builds,
  multi-domain validation across CAD/PCB/circuit/simulation/gait, design scoring,
  failure reports, or iteration plans. This skill only reads file artifacts from
  other build123d-cad subskills, runs deterministic gates and scoring, and produces
  design_score, gate_report, failure_report, and next_iteration_plan outputs.
---

# robot-dog-digital-twin

This skill orchestrates a robot-dog virtual prototype before physical manufacturing.
It does not model CAD, author PCB, generate URDF, or run a simulator directly. It reads
the artifacts produced by those skills, checks gates, scores the design, and explains
what to change next.

## When To Use

Use this skill for:

- Digital twin or virtual prototype workflows for a robot dog.
- "Can this design enter physical prototype?" decisions.
- Multi-domain validation over mechanical, PCB reliability, circuit, dynamics, gait,
  and manufacturability reports.
- Generating `design_score.json`, `gate_report.json`, `failure_report.md`, or
  `next_iteration_plan.md`.

## Workflow

1. Read `requirements.yaml`.
2. Read `verification_matrix.yaml`.
3. Read `artifacts.json` and discover known domain reports.
4. Run gates G0-G5 with `scripts/run_gate.py`.
5. Score the design with `scripts/score_design.py`.
6. Produce next-iteration guidance with `scripts/propose_next_iteration.py`.

## Commands

```bash
python skills/robot-dog-digital-twin/scripts/collect_artifacts.py skills/robot-dog-digital-twin/examples/quadruped_mvp
python skills/robot-dog-digital-twin/scripts/score_design.py skills/robot-dog-digital-twin/examples/quadruped_mvp
python skills/robot-dog-digital-twin/scripts/run_gate.py skills/robot-dog-digital-twin/examples/quadruped_mvp --gate G3
python skills/robot-dog-digital-twin/scripts/propose_next_iteration.py skills/robot-dog-digital-twin/examples/quadruped_mvp
```

## Outputs

Outputs are written under the project directory:

```text
reports/
  artifacts.collected.json
  design_score.json
  gate_report.json
  gate_report.md
  failure_report.md
  next_iteration_plan.md
```

## Rules

- Do not import code from sibling subskills.
- Do not decide physical manufacturing by score alone. Blockers fail the gate.
- Do not start physical manufacturing, ordering, flashing, or motor motion.
- If tests fail, fix this skill before moving to the next module.

## References

- `references/workflow.md` for the full loop.
- `references/gates.md` for G0-G5 rules.
- `references/scoring.md` for deterministic scoring.
- `references/failure-taxonomy.md` for blocker categories.
- `references/quadruped-mvp.md` for the MVP artifact layout.

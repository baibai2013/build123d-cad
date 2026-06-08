#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from digital_twin_common import (
    compute_design_score,
    next_actions_from_score,
    project_path,
    reports_dir,
    write_text,
)


def failure_report(score: dict[str, object], actions: list[str]) -> str:
    lines = [
        "# Failure Report",
        "",
        f"Total score: {score['total_score']}",
        f"Prototype allowed: {score['prototype_allowed']}",
        "",
        "## Blockers",
    ]
    blockers = score.get("blockers", [])
    if blockers:
        lines.extend(f"- {blocker}" for blocker in blockers)
    else:
        lines.append("- none")
    lines.extend(["", "## Recommended Next Actions"])
    lines.extend(f"- {action}" for action in actions)
    return "\n".join(lines) + "\n"


def iteration_plan(actions: list[str]) -> str:
    lines = ["# Next Iteration Plan", ""]
    lines.extend(f"{idx}. {action}" for idx, action in enumerate(actions, start=1))
    return "\n".join(lines) + "\n"


def propose(project_dir: Path) -> tuple[dict[str, object], list[str]]:
    score = compute_design_score(project_dir)
    actions = next_actions_from_score(score)
    report_dir = reports_dir(project_dir)
    write_text(report_dir / "failure_report.md", failure_report(score, actions))
    write_text(report_dir / "next_iteration_plan.md", iteration_plan(actions))
    return score, actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Write robot dog next-iteration reports.")
    parser.add_argument("project_dir", help="Project directory containing digital-twin artifacts")
    args = parser.parse_args()
    score, actions = propose(project_path(args.project_dir))
    print(f"Wrote next iteration plan with {len(actions)} action(s); score={score['total_score']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

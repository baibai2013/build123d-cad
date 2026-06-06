"""simulation 子技能 smoke — 结构骨架(无 pybullet 依赖,恒跑)。"""
from __future__ import annotations

from pathlib import Path

import pytest

EXPECTED_SCRIPTS = ["run_sim.py", "verify_sim.py", "sim_render.py"]
EXPECTED_REFS = [
    "pybullet-headless.md", "control-modes.md",
    "stability-checks.md", "output-contract.md",
]


@pytest.mark.smoke
def test_skill_md_exists(subskill_root: Path):
    md = subskill_root / "SKILL.md"
    assert md.exists(), f"{md} 缺失"
    assert md.stat().st_size > 0, f"{md} 为空"


@pytest.mark.smoke
def test_readme_exists(subskill_root: Path):
    assert (subskill_root / "README.md").exists(), "README.md 缺失"


@pytest.mark.smoke
def test_subskill_dirs_present(subskill_root: Path):
    for d in ("references", "scripts", "tests"):
        assert (subskill_root / d).is_dir(), f"{subskill_root}/{d} 缺失"


@pytest.mark.smoke
def test_skill_md_size_under_250(subskill_root: Path):
    md = subskill_root / "SKILL.md"
    n = len(md.read_text(encoding="utf-8").splitlines())
    assert n <= 250, f"SKILL.md {n} 行 > 上限 250"


@pytest.mark.smoke
def test_scripts_present(scripts_dir: Path):
    for s in EXPECTED_SCRIPTS:
        assert (scripts_dir / s).exists(), f"scripts/{s} 缺失"


@pytest.mark.smoke
def test_references_present(subskill_root: Path):
    refs = subskill_root / "references"
    for r in EXPECTED_REFS:
        assert (refs / r).exists(), f"references/{r} 缺失"

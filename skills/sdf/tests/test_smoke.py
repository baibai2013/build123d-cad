"""sdf 子技能 smoke — P0 阶段只验骨架,P1/P3 阶段升级真跑。"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.smoke
def test_skill_md_exists(subskill_root: Path):
    md = subskill_root / "SKILL.md"
    assert md.exists(), f"{md} 缺失"
    assert md.stat().st_size > 0, f"{md} 为空"


@pytest.mark.smoke
def test_readme_exists(subskill_root: Path):
    readme = subskill_root / "README.md"
    assert readme.exists(), f"{readme} 缺失"


@pytest.mark.smoke
def test_subskill_dirs_present(subskill_root: Path):
    """references/ scripts/ tests/ 三个标准目录就位。"""
    for d in ("references", "scripts", "tests"):
        assert (subskill_root / d).is_dir(), f"{subskill_root}/{d} 缺失"


@pytest.mark.smoke
def test_skill_md_size_under_250(subskill_root: Path):
    """子技能 SKILL.md ≤ 250 行(08 §7 加新子技能质量门)。"""
    md = subskill_root / "SKILL.md"
    lines = md.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 250, f"SKILL.md {len(lines)} 行 > 上限 250"


@pytest.mark.smoke
def test_skill_md_has_frontmatter(subskill_root: Path):
    """sdf SKILL.md 已有 YAML frontmatter(P1-1 复刻完成态特征)。"""
    text = (subskill_root / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---"), "sdf SKILL.md 应有 frontmatter"
    assert "name: sdf" in text


@pytest.mark.smoke
def test_export_script_present(subskill_root: Path):
    """L2 export_sdf.py 就位(P1-1 落地特征)。"""
    assert (subskill_root / "scripts" / "export_sdf.py").exists()


@pytest.mark.smoke
def test_l1_generator_present(subskill_root: Path):
    """L1 整块复刻:scripts/sdf 生成器包就位。"""
    pkg = subskill_root / "scripts" / "sdf"
    for f in ("__main__.py", "cli.py", "source.py", "validation.py"):
        assert (pkg / f).exists(), f"L1 缺 {f}"


@pytest.mark.smoke
def test_references_complete(subskill_root: Path):
    """references/ 关键参考齐(L1 复刻自 earthtojake)。"""
    refs = subskill_root / "references"
    expected = [
        "design-ledger.md", "frame-semantics.md", "gen-sdf.md",
        "generator-contract.md", "sdf-workflow.md", "validation.md",
    ]
    missing = [f for f in expected if not (refs / f).exists()]
    assert not missing, f"references/ 缺: {missing}"

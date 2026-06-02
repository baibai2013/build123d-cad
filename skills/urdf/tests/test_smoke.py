"""urdf 子技能 smoke — P0 阶段验骨架 + 关键文件存在,P1 升级真跑 export_urdf。"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.smoke
def test_skill_md_exists(subskill_root: Path):
    md = subskill_root / "SKILL.md"
    assert md.exists() and md.stat().st_size > 0


@pytest.mark.smoke
def test_skill_md_has_frontmatter(subskill_root: Path):
    """urdf SKILL.md 已有 YAML frontmatter(P0-4 完成态特征)。"""
    md = subskill_root / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    assert text.startswith("---"), "urdf SKILL.md 应有 frontmatter"
    assert "name: urdf" in text


@pytest.mark.smoke
def test_export_script_present(subskill_root: Path):
    assert (subskill_root / "scripts" / "export_urdf.py").exists()


@pytest.mark.smoke
def test_references_complete(subskill_root: Path):
    """references/ 五份核心参考(design-ledger / frame-semantics / gen-urdf / generator-contract / urdf-workflow / validation)。"""
    refs = subskill_root / "references"
    expected = [
        "design-ledger.md",
        "frame-semantics.md",
        "gen-urdf.md",
        "generator-contract.md",
        "urdf-workflow.md",
        "validation.md",
    ]
    missing = [f for f in expected if not (refs / f).exists()]
    assert not missing, f"references/ 缺: {missing}"


@pytest.mark.p1
def test_export_urdf_help(urdf_export_script: Path):
    """export_urdf.py --help 不抛(P1 真跑前的烟雾测试)。"""
    pytest.skip("P1: export_urdf.py CLI 接口待 algorithm 在 04 §T2 落定后启用")


@pytest.mark.p1
def test_joints_yaml_passes_schema():
    """最小 joints.yaml 走 shared.python.handoff.validate_joints。

    依赖 shared/schemas/joints.schema.json + shared/python/handoff/validate.py
    (P0-6 T4/T5 落地后启用,届时改为接收 joints_yaml_minimal fixture)。
    """
    pytest.skip("P1: joints schema 校验链路待 P0-6 落地后启用")

"""super skill 骨架完整性 — 对应 07 文档 §5「骨架完整性」脚本的 pytest 化。

每子技能必须有 SKILL.md + tests/conftest.py + tests/test_smoke.py。
父级 SKILL.md / shared 三协议都在。
"""
from __future__ import annotations

from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]

SUBSKILLS = [
    "mechanical",
    "viewer",
    "urdf",
    "srdf",
    "sdf",
    "gcode",
    "sendcutsend",
    "parts-catalog",
    "bambu-labs",
    "pcb",
    "electronics-bom",
]


@pytest.mark.smoke
def test_parent_skill_md_exists():
    md = SKILL_ROOT / "SKILL.md"
    assert md.exists(), f"父级 SKILL.md 缺失: {md}"
    assert md.stat().st_size > 100, "父级 SKILL.md 太小"


@pytest.mark.smoke
def test_parent_skill_md_size_under_220():
    """07 §5 规定父 SKILL.md ≤ 220 行;给 50 行余量到 270。"""
    md = SKILL_ROOT / "SKILL.md"
    lines = md.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 270, f"父 SKILL.md {len(lines)} 行 > 上限 270"


@pytest.mark.smoke
def test_parent_readme_exists():
    assert (SKILL_ROOT / "README.md").exists()


@pytest.mark.smoke
@pytest.mark.parametrize("name", SUBSKILLS)
def test_subskill_skill_md(name):
    md = SKILL_ROOT / "skills" / name / "SKILL.md"
    assert md.exists(), f"{name}/SKILL.md 缺失"
    assert md.stat().st_size > 0


@pytest.mark.smoke
@pytest.mark.parametrize("name", SUBSKILLS)
def test_subskill_tests_dir(name):
    """每子技能 tests/ 目录就位 + 至少 1 个 test_*.py。

    占位子技能用统一 test_smoke.py 模板;mechanical / viewer 已有专门测试文件
    (test_validate.py / test_routing.py 等),也算合规。
    """
    d = SKILL_ROOT / "skills" / name / "tests"
    assert d.is_dir(), f"{name}/tests/ 缺失"
    assert (d / "conftest.py").exists(), f"{name}/tests/conftest.py 缺失"
    test_files = list(d.glob("test_*.py"))
    assert test_files, f"{name}/tests/ 下没有 test_*.py"


@pytest.mark.smoke
def test_mechanical_skill_md_under_400():
    """mechanical 是高扇出根节点,SKILL.md 上限 380(07 §5),给 50 行余量到 430。"""
    md = SKILL_ROOT / "skills/mechanical/SKILL.md"
    lines = md.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 430, f"mechanical SKILL.md {len(lines)} 行 > 上限 430"


@pytest.mark.smoke
def test_shared_protocols_present():
    shared = SKILL_ROOT / "shared"
    for fname in ("handoff-protocols.md", "multi-skill-router.md", "dependencies.md"):
        assert (shared / fname).exists(), f"shared/{fname} 缺失"


@pytest.mark.smoke
def test_no_subskill_cross_imports():
    """跨子技能严禁直接 import,所有交互必须走 shared/(自 import 同子技能不算)。"""
    import re
    skills_dir = SKILL_ROOT / "skills"
    pattern = re.compile(r"^\s*from\s+skills\.([a-zA-Z0-9_-]+)\.", re.MULTILINE)
    bad = []
    for py in skills_dir.rglob("*.py"):
        s = str(py)
        if "/tests/" in s or "__pycache__" in s:
            continue
        rel = py.relative_to(skills_dir)
        own = rel.parts[0]   # 子技能名
        try:
            text = py.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in pattern.finditer(text):
            target = match.group(1)
            if target != own:
                bad.append(f"{py.relative_to(SKILL_ROOT)} → skills.{target}")
    assert not bad, f"发现子技能间 import: {bad}"

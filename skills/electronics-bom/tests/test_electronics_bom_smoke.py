"""electronics-bom 子技能 smoke 测试 — P0 占位。

验证父级 pytest 能扫到本 skill,SKILL.md / README.md 文件存在。
P3 启动后由 hardware 替换为真实 lookup / 数据源测试(见 06 §3.3a.2)。
"""

from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent


def test_placeholder() -> None:
    """占位用例,仅保证 pytest 能扫到本文件。"""
    assert True


def test_skill_md_exists() -> None:
    """SKILL.md 文件存在(P0 占位完整性自检)。"""
    skill_md = SKILL_ROOT / "SKILL.md"
    assert skill_md.is_file(), f"缺 {skill_md}"
    assert skill_md.stat().st_size > 0, "SKILL.md 不应为空"


def test_readme_exists() -> None:
    """README.md 文件存在。"""
    readme = SKILL_ROOT / "README.md"
    assert readme.is_file(), f"缺 {readme}"

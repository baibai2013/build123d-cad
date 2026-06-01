# scripts/validate/* 脚本最小可加载性测试
#
# 不真跑(避免依赖 build123d / OCC 大件),只验证语法 + import 顶层 OK。
# 真正的功能测试 P0-9 benchmarks 与 P1 agent-eval 承接。
import ast
from pathlib import Path

import pytest

VALIDATE_SCRIPTS = [
    "validate_part.py",
    "assembly_check.py",
    "contract_verify.py",
    "visual_compare.py",
]


@pytest.mark.parametrize("script", VALIDATE_SCRIPTS)
def test_validate_script_parses(mechanical_root, script):
    path = mechanical_root / "scripts" / "validate" / script
    assert path.is_file(), f"validate 脚本缺失: {path}"
    src = path.read_text(encoding="utf-8")
    try:
        ast.parse(src)
    except SyntaxError as exc:
        pytest.fail(f"{script} 语法错误: {exc}")


def test_assets_examples_present(mechanical_root):
    """13 个示例零件是否完整迁过来"""
    parts_dir = mechanical_root / "assets" / "parts"
    assert parts_dir.is_dir(), f"assets/parts/ 缺失: {parts_dir}"
    files = sorted(parts_dir.glob("*.py"))
    assert len(files) >= 13, f"assets/parts/ 示例零件不足 13 个,实有 {len(files)}"


def test_legacy_skill_archived(mechanical_root):
    """legacy SKILL.md 是否归档以备查询"""
    legacy = mechanical_root / "SKILL.legacy.md"
    assert legacy.is_file(), "SKILL.legacy.md 归档不存在"
    assert legacy.stat().st_size > 50_000, "legacy 文件异常小,可能没归档完整"

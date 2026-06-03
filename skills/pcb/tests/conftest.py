"""pcb 子技能级 fixture(P3 落地:骨架 smoke 常跑 + kicad-cli 实跑 skip-if-absent)。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SUBSKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SUBSKILL_ROOT / "scripts"
# 让 tests 能 import scripts/ 下的模块(new_project / pcb_common 等)。
sys.path.insert(0, str(SCRIPTS))


@pytest.fixture(scope="session")
def subskill_root() -> Path:
    """本子技能根目录(skills/pcb/)。"""
    return SUBSKILL_ROOT


@pytest.fixture(scope="session")
def scripts_dir() -> Path:
    return SCRIPTS


@pytest.fixture
def kicad_cli():
    """kicad-cli 路径;未装则 skip(实跑类测试用)。"""
    from pcb_common import which_kicad_cli

    cli = which_kicad_cli(required=False)
    if cli is None:
        pytest.skip("kicad-cli(KiCad 9.x)未安装,跳过实跑出件测试")
    return cli

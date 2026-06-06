"""simulation 子技能级 fixture。

结构 smoke 恒跑;真跑类(test_sim_smoke)用 importorskip pybullet,缺则自动 skip(CI 安全)。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SUBSKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SUBSKILL_ROOT / "scripts"
# 让 tests 能 import scripts/ 下的模块(run_sim / verify_sim / sim_render)。
sys.path.insert(0, str(SCRIPTS))


@pytest.fixture(scope="session")
def subskill_root() -> Path:
    return SUBSKILL_ROOT


@pytest.fixture(scope="session")
def scripts_dir() -> Path:
    return SCRIPTS

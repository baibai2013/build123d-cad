"""pcb 子技能(tscircuit)级 fixture。

骨架 smoke 常跑;dfm_check 用本地 fixtures 单测(无需 tsci/bun/key,CI 可跑)。
真出件/报价的实跑类测试需 tsci/jlcpcb-mcp,标 p3 默认 skip。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SUBSKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SUBSKILL_ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
# 让 tests 能 import scripts/ 下的模块(dfm_check)。
sys.path.insert(0, str(SCRIPTS))


@pytest.fixture(scope="session")
def subskill_root() -> Path:
    return SUBSKILL_ROOT


@pytest.fixture(scope="session")
def scripts_dir() -> Path:
    return SCRIPTS


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES

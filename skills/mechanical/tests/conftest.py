# mechanical 子技能级 fixture
#
# MECHANICAL_ROOT 指向本子技能根目录,所有结构性测试以此为基准。
import os
from pathlib import Path

import pytest

MECHANICAL_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def mechanical_root() -> Path:
    return MECHANICAL_ROOT


@pytest.fixture(scope="session")
def skill_root() -> Path:
    # super skill 根(build123d-cad/);跨子技能 handoff 测试可能要用
    return MECHANICAL_ROOT.parent.parent

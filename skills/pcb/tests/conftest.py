"""pcb 子技能级 fixture(P0 占位,P1/P3 实现时升级)。"""
from __future__ import annotations

from pathlib import Path

import pytest

SUBSKILL_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def subskill_root() -> Path:
    """本子技能根目录(skills/pcb/)。"""
    return SUBSKILL_ROOT

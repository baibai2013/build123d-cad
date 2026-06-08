from __future__ import annotations

import shutil
from pathlib import Path

import pytest


SUBSKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SUBSKILL_ROOT.parents[1]


@pytest.fixture(scope="session")
def subskill_root() -> Path:
    return SUBSKILL_ROOT


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture()
def example_project(subskill_root: Path, tmp_path: Path) -> Path:
    src = subskill_root / "examples" / "quadruped_mvp"
    dst = tmp_path / "quadruped_mvp"
    shutil.copytree(src, dst)
    return dst

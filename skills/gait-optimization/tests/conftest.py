from __future__ import annotations

import shutil
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def subskill_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def example_project(subskill_root: Path) -> Path:
    return subskill_root / "examples" / "quadruped_mvp"


@pytest.fixture()
def example_project_copy(tmp_path: Path, example_project: Path) -> Path:
    target = tmp_path / "quadruped_mvp"
    shutil.copytree(example_project, target)
    return target

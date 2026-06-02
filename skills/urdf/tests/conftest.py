# urdf 子技能级 fixture
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

URDF_SKILL = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = URDF_SKILL / "scripts"
REPO_ROOT = URDF_SKILL.parents[1]

# 让 tests 可 import L1(scripts/urdf) 与 L2(scripts/export_urdf)
for path in (
    str(SCRIPTS_DIR),
    str(SCRIPTS_DIR / "packages"),
    str(SCRIPTS_DIR / "packages" / "cadpy_metadata" / "src"),
):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def subskill_root() -> Path:
    """本子技能根(skills/urdf/);test_smoke.py 用。"""
    return URDF_SKILL


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def example_joints() -> Path:
    return REPO_ROOT / "shared" / "schemas" / "example" / "single_leg.joints.yaml"


@pytest.fixture
def out_dir(tmp_path: Path) -> Path:
    d = tmp_path / "out"
    d.mkdir()
    return d


@pytest.fixture(scope="session")
def urdf_export_script() -> Path:
    """export_urdf.py 入口;P0-4 已就位。"""
    p = SCRIPTS_DIR / "export_urdf.py"
    if not p.exists():
        pytest.skip(f"export_urdf.py 未就位: {p}")
    return p


@pytest.fixture(scope="session")
def urdf_xml_validator():
    """xmllint --noout;缺工具时返回 None,case 用 skipif 过滤。"""
    return shutil.which("xmllint")

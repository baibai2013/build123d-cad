# sdf 子技能级 fixture
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SDF_SKILL = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SDF_SKILL / "scripts"
REPO_ROOT = SDF_SKILL.parents[1]
SHARED_CADPY_SRC = REPO_ROOT / "shared" / "python" / "cadpy_metadata" / "src"

# 让 tests 可 import L1(scripts/sdf)、L2(scripts/export_sdf)与 shared cadpy_metadata
# (R5:cadpy 已抽 shared,不再 vendor 第三份)
for path in (str(SCRIPTS_DIR), str(SHARED_CADPY_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def subskill_root() -> Path:
    """本子技能根目录(skills/sdf/)。"""
    return SDF_SKILL


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def example_world() -> Path:
    return REPO_ROOT / "shared" / "schemas" / "example" / "playground.world.yaml"


@pytest.fixture(scope="session")
def example_joints() -> Path:
    return REPO_ROOT / "shared" / "schemas" / "example" / "single_leg.joints.yaml"


@pytest.fixture
def out_dir(tmp_path: Path) -> Path:
    d = tmp_path / "out"
    d.mkdir()
    return d


@pytest.fixture
def sample_urdf(out_dir: Path, example_joints: Path) -> Path:
    """跑 P0-4 export_urdf 出一份真 URDF 供 sdf 测试消费(单腿 3 link 2 joint)。"""
    pytest.importorskip("yaml")
    pytest.importorskip("jsonschema")
    urdf_scripts = REPO_ROOT / "skills" / "urdf" / "scripts"
    if str(urdf_scripts) not in sys.path:
        sys.path.insert(0, str(urdf_scripts))
    import export_urdf  # noqa: E402

    report = export_urdf.export(example_joints, out_dir / "urdf", no_l1=True)
    return report.output_urdf

"""父级 tests/ 跨子技能共享 fixture。

P0-7 骨架就位:
- skill_root / workspace_root / tmp_output_dir 三个最常用的路径 fixture
- mechanical_hip_bracket_step (session) 跨 viewer/urdf 测试链复用,缺则 skip
- joints_yaml_minimal (session) 给 urdf 测试链
- b3d_session 探测 build123d/OCP 是否可用,benchmarks/真建模测试用 skipif
- slow_marker_filter (autouse) 默认 skip @pytest.mark.slow,nightly 设 RUN_SLOW=1

引用文档:share/build123d-cad改造/07-测试与验证基建.md §6 + examples/conftest-fixtures.md §1
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]


# ----------------------------------------------------------------------------
# 路径类
# ----------------------------------------------------------------------------

@pytest.fixture(scope="session")
def skill_root() -> Path:
    """super skill 仓根目录(build123d-cad/)。"""
    return SKILL_ROOT


@pytest.fixture(scope="session")
def workspace_root(tmp_path_factory) -> Path:
    """session 级临时项目工作区,模拟 ~/work/<project>/。"""
    return tmp_path_factory.mktemp("ws")


@pytest.fixture
def tmp_output_dir(tmp_path) -> Path:
    """每个 test 一个 output/<task>/,符合 08 §2.0 handoff 协议。"""
    d = tmp_path / "output" / "task"
    d.mkdir(parents=True)
    (d / "parts").mkdir()
    (d / "meshes").mkdir()
    (d / "_errors").mkdir()
    return d


# ----------------------------------------------------------------------------
# 上游样件(跨子技能链式 skip-aware)
# ----------------------------------------------------------------------------

@pytest.fixture(scope="session")
def mechanical_hip_bracket_step(tmp_path_factory) -> Path:
    """跑一次 mechanical 出 hip_bracket.step;给 viewer/urdf 测试链复用。

    mechanical 子技能的实跑脚本(scripts/parts/hip_bracket.py)P0-2 之后未必落地,
    所以本 fixture 在脚本不存在时直接 pytest.skip 而不报错。
    """
    out = tmp_path_factory.mktemp("hip-bracket") / "hip_bracket.step"
    script = SKILL_ROOT / "skills/mechanical/scripts/parts/hip_bracket.py"
    if not script.exists():
        pytest.skip(f"mechanical 子技能 hip_bracket 脚本未就位: {script}")
    venv_py = Path.home() / "work/build123d-parts-lib/.venv/bin/python"
    py = str(venv_py) if venv_py.exists() else "python3"
    try:
        subprocess.check_call([py, str(script), "--out", str(out)])
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        pytest.skip(f"hip_bracket 出件失败: {e}")
    if not out.exists() or out.stat().st_size < 1024:
        pytest.skip(f"hip_bracket STEP 过小,可能未实际生成: {out}")
    return out


@pytest.fixture(scope="session")
def joints_yaml_minimal(tmp_path_factory) -> Path:
    """最小可用 joints.yaml(2 link 1 joint),给 urdf 测试链与 schema 校验复用。"""
    p = tmp_path_factory.mktemp("joints") / "joints.yaml"
    p.write_text(
        "schema_version: 1\n"
        "robot: minimal_test\n"
        "mesh_units: mm\n"
        "mesh_uri_style: relative\n"
        "links:\n"
        "  - name: base_link\n"
        "    inertial:\n"
        "      mass: 1.0\n"
        "      origin: {xyz: [0,0,0], rpy: [0,0,0]}\n"
        "      inertia: {ixx: 0.001, iyy: 0.001, izz: 0.001, ixy: 0, ixz: 0, iyz: 0}\n"
        "  - name: arm_link\n"
        "joints:\n"
        "  - name: arm_joint\n"
        "    type: revolute\n"
        "    parent: base_link\n"
        "    child: arm_link\n"
        "    origin: {xyz: [0, 0, 0.1], rpy: [0, 0, 0]}\n"
        "    axis: [0, 0, 1]\n"
        "    limit: {lower: -1.57, upper: 1.57, effort: 10, velocity: 5}\n",
        encoding="utf-8",
    )
    return p


# ----------------------------------------------------------------------------
# 环境探测
# ----------------------------------------------------------------------------

@pytest.fixture(scope="session")
def b3d_session() -> dict:
    """build123d / OCP 是否可用。失败返回空 dict,case 用 skipif 过滤。

    benchmarks 真建模测试用法:
        @pytest.mark.skipif(not request.getfixturevalue('b3d_session'), reason='build123d 不可用')
    """
    info: dict = {}
    try:
        import build123d as bd
        info["build123d"] = getattr(bd, "__version__", "unknown")
    except ImportError:
        return info
    try:
        import OCP  # noqa: F401
        info["OCP"] = "ok"
    except ImportError:
        pass
    return info


# ----------------------------------------------------------------------------
# slow marker 自动 skip(可被 RUN_SLOW=1 关闭)
# ----------------------------------------------------------------------------

def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_SLOW", "0") == "1":
        return
    skip_slow = pytest.mark.skip(reason="@slow,默认 skip;RUN_SLOW=1 启用")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

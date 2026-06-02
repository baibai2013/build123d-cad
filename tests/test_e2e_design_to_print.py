"""跨子技能 e2e:mechanical → viewer → urdf。

P0 阶段全部 skip(等 mechanical 的 hip_bracket.py + viewer/urdf 实跑链路就位);
P1 阶段 testing 把 skip 改为真跑。
"""
from __future__ import annotations

import pytest


@pytest.mark.p1
@pytest.mark.slow
def test_mechanical_to_viewer_handoff(mechanical_hip_bracket_step, tmp_output_dir):
    """mechanical 出 STEP → viewer 起 server → /health 200 → 文件可加载。

    依赖:viewer 子技能 start.sh + /health endpoint(03 文档 §6 落地后启用)。
    """
    pytest.skip("P1: viewer 集成待 fullstack 完成 03 §6/§7 后启用")


@pytest.mark.p1
@pytest.mark.slow
def test_mechanical_to_urdf_handoff(
    mechanical_hip_bracket_step, joints_yaml_minimal, tmp_output_dir
):
    """mechanical 出 STEP + joints.yaml → urdf 子技能转 URDF → xmllint 通过。

    依赖:urdf 子技能 export_urdf.py(04 文档 §T2/§T3 落地后启用)。
    """
    pytest.skip("P1: urdf 实跑待 algorithm 完成 04 §T2 后启用")


@pytest.mark.p1
def test_handoff_joints_yaml_schema(joints_yaml_minimal):
    """joints.yaml 走 JSON Schema 校验。

    依赖:shared/schemas/joints.schema.json + shared/python/handoff/validate.py
    (P0-6 的 T4/T5 落地后启用)。
    """
    pytest.skip("P1: joints schema 校验待 P0-6 T4/T5 落地后启用")

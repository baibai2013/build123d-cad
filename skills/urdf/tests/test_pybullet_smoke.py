"""M2 验收: 导出的 URDF 必须能被 pybullet.loadURDF() 不报错加载."""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("yaml")
pytest.importorskip("jsonschema")
pb = pytest.importorskip("pybullet", reason="pip install pybullet")

import export_urdf  # noqa: E402


def test_pybullet_load_urdf(example_joints: Path, out_dir: Path) -> None:
    report = export_urdf.export(example_joints, out_dir, no_l1=True)
    assert report.output_urdf.exists()

    cid = pb.connect(pb.DIRECT)
    try:
        pb.setAdditionalSearchPath(str(report.output_urdf.parent))
        body_id = pb.loadURDF(str(report.output_urdf))
        assert body_id >= 0, "loadURDF returned negative id"
        njoints = pb.getNumJoints(body_id)
        # 注: pybullet 把 URDF 第一个 link 作为 base, 其余 link 通过 joints 串.
        # 对 3-link 2-joint 单腿: pybullet 报告 njoints=2(base 不算 joint).
        assert njoints == report.joint_count, (
            f"pybullet sees {njoints} joints, yaml has {report.joint_count}"
        )
        for i in range(njoints):
            info = pb.getJointInfo(body_id, i)
            joint_name = info[1].decode()
            assert joint_name.endswith("_joint"), f"joint name unexpected: {joint_name}"
    finally:
        pb.disconnect(cid)

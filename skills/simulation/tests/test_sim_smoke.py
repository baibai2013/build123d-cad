"""simulation 真跑 smoke — importorskip pybullet,用其自带 r2d2.urdf 跑极小 headless 仿真。

零额外 fixture 文件(r2d2.urdf 来自 pybullet_data),缺 pybullet 自动 skip → CI 安全。
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pb = pytest.importorskip("pybullet", reason="pip install pybullet")
import pybullet_data  # noqa: E402

import run_sim  # noqa: E402  (经 conftest 把 scripts/ 注入 sys.path)
import verify_sim  # noqa: E402


def _r2d2() -> str:
    return os.path.join(pybullet_data.getDataPath(), "r2d2.urdf")


@pytest.mark.smoke
@pytest.mark.requires_pybullet
def test_tiny_passive_drop(tmp_path: Path):
    rec = run_sim.simulate(
        _r2d2(), mode="passive", steps=120,   # 0.5 s,小尺寸,够快
        outdir=str(tmp_path), width=160, height=120, no_video=True,
    )
    assert (tmp_path / "r2d2.results.json").exists()
    assert list((tmp_path / "frames").glob("frame_*")), "未出任何关键帧"
    s = rec["summary"]
    assert s["max_pos"] < 1e3 and not s["nan_or_inf"], "数值爆炸"
    assert s["min_base_z"] > -1.0, "穿地"
    assert len(rec["joints"]) > 0, "没解析到关节"


@pytest.mark.smoke
@pytest.mark.requires_pybullet
def test_verify_exit_codes(tmp_path: Path):
    # 稳定跌落 → 退 0(base 贴地 + 2s 足够落定)
    rc = verify_sim.main([_r2d2(), "--mode", "passive", "--steps", "480",
                          "--base-z", "0.05",
                          "--outdir", str(tmp_path), "--width", "160", "--height", "120"])
    assert rc == 0, f"稳定 r2d2 应退 0,实退 {rc}"
    assert (tmp_path / "_verify" / "checklist.txt").exists()
    # 不存在的文件 → 退 2
    assert verify_sim.main(["/tmp/__no_such__.urdf"]) == 2
    # 不认识的后缀 → 退 2
    assert verify_sim.main(["/tmp/__x__.txt"]) == 2

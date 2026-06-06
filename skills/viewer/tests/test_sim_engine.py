"""SIM engine —— 仿真数据面板(results.json 曲线 + 判稳徽章 + 帧 scrubber)已落地。

3D 轨迹回放走 cad 引擎(?trajectory=,见 docs/simulation-design.md);本引擎是数据视图。
轻量静态校验 dist 就位 + 关键结构;真起 server 的端到端在 test_start.py(engineImpl.sim=ready)覆盖。
"""
from __future__ import annotations

from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "engines" / "sim"
DIST = ENGINE_DIR / "dist" / "index.html"


@pytest.mark.smoke
def test_sim_dist_present():
    assert DIST.exists(), "engines/sim/dist/index.html 缺失(引擎应为 ready)"
    assert DIST.stat().st_size > 500, "dist/index.html 过小,疑似占位"


@pytest.mark.smoke
def test_sim_dashboard_structure():
    """数据面板应含:results.json fetch、帧 scrubber、canvas 曲线、判稳徽章。"""
    html = DIST.read_text(encoding="utf-8")
    for marker in ("/files/", "results", "slider", "canvas", "checks", "drawChart"):
        assert marker in html, f"sim 引擎页缺关键结构: {marker}"


@pytest.mark.smoke
def test_sim_handles_video_and_csv_branches():
    """除 results.json 外,引擎页还要兜 mp4/webm/csv 分支(路由都落 sim)。"""
    html = DIST.read_text(encoding="utf-8")
    for marker in (".mp4", ".csv", "<video"):
        assert marker in html, f"sim 引擎页缺分支处理: {marker}"

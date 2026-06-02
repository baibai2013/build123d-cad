"""viewer 测试通用 fixture。

- workspace_dir:tmp 目录,放测试用的 .step / .kicad_pcb / .csv 等
- server_url:启动 server 并返回 health URL,会话级 fixture(每会话起一次,结束 shutdown)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest

VIEWER_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = VIEWER_ROOT / "scripts"
START_SH = SCRIPTS / "start.sh"


@pytest.fixture(scope="session")
def workspace_dir(tmp_path_factory):
    ws = tmp_path_factory.mktemp("viewer-ws")
    # 准备各类后缀样件(全是空文件,只为路由 + 文件代理测试)
    for name in [
        "sample.step", "sample.stl", "sample.glb",
        "robot.urdf", "trace.gcode", "plate.dxf",
        "board.kicad_pcb", "board.gbr",
        "sch.kicad_sch", "export.svg",
        "wave.csv", "clip.mp4",
        "secret.exe",  # 不在路由的后缀,测白名单
    ]:
        (ws / name).write_text(f"fake content for {name}\n")
    return ws


def _shutdown_all_viewer_servers():
    """清掉残留 viewer server(测试隔离)。"""
    try:
        subprocess.run(
            ["pkill", "-f", "build123d-cad/skills/viewer/scripts/backend/server.mjs"],
            check=False, capture_output=True, timeout=5,
        )
        time.sleep(0.5)
    except Exception:
        pass


def _http_get(url, timeout=2):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", errors="replace")


def _start_server(workspace, sample_file):
    proc = subprocess.run(
        ["bash", str(START_SH), str(sample_file), str(workspace)],
        capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, f"start.sh failed: stderr={proc.stderr!r}"
    url = proc.stdout.strip()
    assert url.startswith("http://127.0.0.1:"), f"unexpected url: {url!r}"
    return url


@pytest.fixture(scope="session")
def server(workspace_dir):
    """起一个会话级 server,会话结束 shutdown。"""
    _shutdown_all_viewer_servers()
    sample = workspace_dir / "sample.step"
    url = _start_server(workspace_dir, sample)
    # 解析 base
    from urllib.parse import urlparse, parse_qs
    p = urlparse(url)
    base = f"http://{p.hostname}:{p.port}"
    yield {
        "base": base,
        "port": p.port,
        "first_url": url,
        "workspace": workspace_dir,
    }
    # teardown
    try:
        urllib.request.urlopen(f"{base}/__cad/shutdown", data=b"", timeout=2)
    except Exception:
        pass
    _shutdown_all_viewer_servers()


@pytest.fixture
def http_get():
    return _http_get

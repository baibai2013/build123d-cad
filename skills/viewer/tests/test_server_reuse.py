"""Server 复用测试。

规格 §5.1:同 workspace 第二次起 → 同端口复用,不新起 server。
不同 workspace → 新起一个 server,端口不同。
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import urlparse

VIEWER_ROOT = Path(__file__).resolve().parent.parent
START_SH = VIEWER_ROOT / "scripts" / "start.sh"


def _start(file_path, workspace):
    proc = subprocess.run(
        ["bash", str(START_SH), str(file_path), str(workspace)],
        capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    return urlparse(proc.stdout.strip())


def test_same_workspace_reuses_port(server, workspace_dir):
    """server fixture 已起一个 → 第二次同 workspace 应复用同端口。"""
    p2 = _start(workspace_dir / "sample.stl", workspace_dir)
    assert p2.port == server["port"], "同 workspace 应复用端口"


def test_different_workspace_gets_new_port(server, workspace_dir, tmp_path_factory):
    other_ws = tmp_path_factory.mktemp("other-ws")
    (other_ws / "x.step").write_text("x")
    p3 = _start(other_ws / "x.step", other_ws)
    assert p3.port != server["port"], "不同 workspace 不应复用端口"
    # cleanup: 关掉这个 server
    import urllib.request
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{p3.port}/__cad/shutdown", data=b"", timeout=2)
    except Exception:
        pass

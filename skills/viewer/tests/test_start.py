"""start.sh + server 端到端冒烟。

- bash start.sh <step> → stdout 唯一一行 URL
- 健康检查返回 build123d-cad/viewer + serverApiVersion 2
- /__cad/shutdown 优雅关停
"""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse, parse_qs


VIEWER_ROOT = Path(__file__).resolve().parent.parent
START_SH = VIEWER_ROOT / "scripts" / "start.sh"


def test_start_outputs_single_line_url(server):
    url = server["first_url"]
    p = urlparse(url)
    assert p.scheme == "http"
    assert p.hostname == "127.0.0.1"
    q = parse_qs(p.query)
    assert q["engine"] == ["cad"]


def test_health_endpoint(server):
    with urllib.request.urlopen(f"{server['base']}/__cad/server", timeout=3) as r:
        assert r.status == 200
        body = json.loads(r.read())
    assert body["app"] == "build123d-cad/viewer"
    assert body["serverApiVersion"] >= 2
    assert body["schemaVersion"] >= 1
    assert set(body["engines"]) == {"cad", "pcb", "sch", "sim", "tscircuit"}
    # cad / tscircuit 是 ready(有 dist/index.html),其它是 stub(规格 §5.2)
    assert body["engineImpl"]["cad"] == "ready"
    assert body["engineImpl"]["tscircuit"] == "ready"
    for e in ("pcb", "sch", "sim"):
        assert body["engineImpl"][e] == "stub"


def test_cad_index_html(server, http_get):
    url = f"{server['base']}/?engine=cad&dir={server['workspace']}&file=sample.step"
    status, body = http_get(url)
    assert status == 200
    assert "<!doctype html>" in body.lower()
    assert "CAD Viewer" in body  # cad-viewer 原始 title


def test_assets_served(server, http_get):
    """cad SPA 的 assets/index-*.js 应该 200。"""
    base = server["base"]
    # 取 cad index.html 里的 main script src
    _, html = http_get(f"{base}/?engine=cad&dir={server['workspace']}&file=sample.step")
    import re
    m = re.search(r'src="(/assets/index-[^"]+\.js)"', html)
    assert m, "未找到 cad 主 script"
    status, _ = http_get(f"{base}{m.group(1)}")
    assert status == 200


def test_files_proxy(server, http_get):
    base = server["base"]
    ws = server["workspace"]
    status, body = http_get(f"{base}/files/sample.step?dir={ws}")
    assert status == 200
    assert "fake content" in body


def test_files_proxy_unsupported_ext_blocked(server):
    base = server["base"]
    ws = server["workspace"]
    try:
        urllib.request.urlopen(f"{base}/files/secret.exe?dir={ws}", timeout=3)
        assert False, "should have raised"
    except urllib.error.HTTPError as e:
        assert e.code == 415


def test_files_proxy_dir_outside_workspace_blocked(server):
    base = server["base"]
    try:
        urllib.request.urlopen(f"{base}/files/passwd?dir=/etc", timeout=3)
        assert False, "should have raised"
    except urllib.error.HTTPError as e:
        assert e.code == 403


def test_bad_engine_returns_400(server):
    base = server["base"]
    try:
        urllib.request.urlopen(f"{base}/?engine=bogus&dir=/tmp&file=x.step", timeout=3)
        assert False, "should have raised"
    except urllib.error.HTTPError as e:
        assert e.code == 400


def test_unsupported_extension_exit_2(workspace_dir):
    f = workspace_dir / "secret.exe"
    proc = subprocess.run(
        ["bash", str(START_SH), str(f), str(workspace_dir)],
        capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 2
    assert "unsupported" in proc.stderr.lower()


def test_missing_file_exit_3(workspace_dir):
    proc = subprocess.run(
        ["bash", str(START_SH), str(workspace_dir / "does-not-exist.step"), str(workspace_dir)],
        capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 3


def test_file_outside_workspace_exit_2(workspace_dir, tmp_path):
    """file 不在 workspace_root 内应当报错。"""
    other = tmp_path / "outside.step"
    other.write_text("x")
    proc = subprocess.run(
        ["bash", str(START_SH), str(other), str(workspace_dir)],
        capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 2

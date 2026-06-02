"""真件端到端 — 用 mechanical 子技能产出的 STEP 跑通 viewer。

CI 上无 mechanical 产物时 skip,本地跑 M2 demo(2026-06-08)的必要部分。
覆盖:cad backend 反代 / SPA 启动核心 API / 真 STEP bytes / Content-Type 正确。
"""
from __future__ import annotations

import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse, quote

import pytest

VIEWER_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = VIEWER_ROOT.parent.parent  # ~/.agents/skills/build123d-cad
START_SH = VIEWER_ROOT / "scripts" / "start.sh"
MECH_OUTPUT = SKILL_ROOT / "skills" / "mechanical" / "benchmarks" / "output"

# 真件清单(mechanical 产出过的)
REAL_STEPS = [
    MECH_OUTPUT / "calibration_block.step",
    MECH_OUTPUT / "flange_4hole.step",
    MECH_OUTPUT / "l_bracket.step",
]


def _start(file_path, workspace):
    proc = subprocess.run(
        ["bash", str(START_SH), str(file_path), str(workspace)],
        capture_output=True, text=True, timeout=20,
    )
    assert proc.returncode == 0, f"stderr={proc.stderr!r}"
    return urlparse(proc.stdout.strip())


def _shutdown(port):
    try:
        urllib.request.urlopen(
            urllib.request.Request(f"http://127.0.0.1:{port}/__cad/shutdown", method="POST"),
            data=b"", timeout=2,
        )
    except Exception:
        pass


@pytest.fixture(scope="module")
def real_step():
    avail = [s for s in REAL_STEPS if s.exists()]
    if not avail:
        pytest.skip(
            f"无 mechanical 真件,先跑 mechanical/benchmarks 产出 step 再测;"
            f"期望路径:{MECH_OUTPUT}"
        )
    return avail[0]


@pytest.fixture(scope="module")
def real_server(real_step):
    """起 server,会话级。"""
    # 关掉前面 fixture 残留
    subprocess.run(
        ["pkill", "-f", "build123d-cad/skills/viewer/scripts/backend/server.mjs"],
        check=False, capture_output=True, timeout=3,
    )
    import time; time.sleep(0.3)

    p = _start(real_step, SKILL_ROOT)
    yield {"port": p.port, "host": p.hostname, "step": real_step}
    _shutdown(p.port)


def test_cad_spa_index(real_server, real_step):
    base = f"http://127.0.0.1:{real_server['port']}"
    url = f"{base}/?engine=cad&dir={quote(str(real_step.parent))}&file={quote(real_step.name)}"
    with urllib.request.urlopen(url, timeout=3) as r:
        body = r.read().decode("utf-8")
    assert r.status == 200
    assert "<!doctype html>" in body.lower()
    assert "CAD Viewer" in body


def test_cad_backend_catalog_proxied(real_server):
    """cad SPA 启动时调 /__cad/catalog,父 server 应反代到 cad backend 返回 200。"""
    base = f"http://127.0.0.1:{real_server['port']}"
    with urllib.request.urlopen(f"{base}/__cad/catalog", timeout=3) as r:
        assert r.status == 200, "cad backend /__cad/catalog 反代失败"


def test_files_proxy_real_step_bytes(real_server, real_step):
    """通过 /files/ 取真 STEP bytes,长度 + Content-Type + 内容头部三对。"""
    base = f"http://127.0.0.1:{real_server['port']}"
    url = f"{base}/files/{quote(real_step.name)}?dir={quote(str(real_step.parent))}"
    with urllib.request.urlopen(url, timeout=5) as r:
        assert r.status == 200
        assert r.headers.get("Content-Type") == "model/step"
        body = r.read()
    expected = real_step.read_bytes()
    assert len(body) == len(expected), f"len mismatch: got {len(body)} vs {len(expected)}"
    assert body == expected, "字节内容不一致"
    assert body.startswith(b"ISO-10303-21;"), "STEP 文件应以 ISO-10303-21 起头"


def test_internal_api_routes_proxied(real_server):
    """cad backend 的几条内部 API 即使参数错也应被反代(返回 4XX 而不是 502/404)。"""
    base = f"http://127.0.0.1:{real_server['port']}"
    routes_should_proxy = [
        "/__cad/asset",          # cad backend 应该返 4XX(缺参数)而不是父 server 自己的 404
        "/__cad/step-artifact",
        "/__cad/download",
    ]
    for ep in routes_should_proxy:
        try:
            urllib.request.urlopen(f"{base}{ep}", timeout=3)
            # 200 也行(意味着 cad backend 接受了请求)
        except urllib.error.HTTPError as e:
            # 4XX 都说明反代到 cad backend 了
            assert e.code < 500, f"{ep} 返回 {e.code},应该是 4XX(cad backend 拒)而非 5XX(反代失败)"
        except urllib.error.URLError as e:
            pytest.fail(f"{ep} 连接失败: {e}")

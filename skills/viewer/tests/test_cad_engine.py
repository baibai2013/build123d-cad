"""CAD engine 端到端(无浏览器版本)。

完整端到端用 headless Chrome 截图断言是 P1-5(等 web_preview.snapshot 实现);
这里只验证 server 把 cad SPA + 关键 chunk 都吐出来,前端代码本身是 cad-viewer 已验证过的。
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

import pytest


VIEWER_ROOT = Path(__file__).resolve().parent.parent
CAD_DIST = VIEWER_ROOT / "scripts" / "engines" / "cad" / "dist"


def test_cad_dist_exists():
    """T2 复刻产物应该就位。"""
    assert (CAD_DIST / "index.html").exists()
    assert (CAD_DIST / "assets").is_dir()
    # 关键 loader chunks
    assets = list((CAD_DIST / "assets").glob("*.js"))
    names = [a.name for a in assets]
    assert any("STLLoader" in n for n in names), "STL loader 缺失"
    assert any("GLTFLoader" in n for n in names), "GLTF loader 缺失"
    assert any("parseUrdf" in n for n in names), "URDF parser 缺失"


def test_cad_serves_index(server, http_get):
    base = server["base"]
    status, body = http_get(f"{base}/?engine=cad&dir={server['workspace']}&file=sample.step")
    assert status == 200
    assert "<!doctype html>" in body.lower()
    # 应该至少有 index 主 script + 主 css
    assert re.search(r'/assets/index-[^"]+\.js', body)
    assert re.search(r'/assets/index-[^"]+\.css', body)


def test_cad_chunks_load(server, http_get):
    base = server["base"]
    _, html = http_get(f"{base}/?engine=cad&dir={server['workspace']}&file=sample.step")
    # 把 modulepreload 的几个 vendor 都拉一遍
    for m in re.finditer(r'href="(/assets/[^"]+\.(?:js|css))"', html):
        path = m.group(1)
        status, _ = http_get(f"{base}{path}")
        assert status == 200, f"asset {path} 拉取失败"


@pytest.mark.skip(reason="P1-5: headless Chrome 截图断言,依赖 playwright")
def test_cad_renders_step_via_headless_chrome():
    """P1-5 才落地。"""
    pass

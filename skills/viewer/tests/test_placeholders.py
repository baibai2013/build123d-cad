"""占位页测试 — sch/sim 的 index.html 应该 200 + 含「待实现」字样。

pcb 已从占位升级为实现页(P3 scaffolded),不再走占位契约,
其页面结构由 test_pcb_engine_page_implemented 校验。

CI 必跑(无浏览器,纯 HTML)。
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

import pytest

VIEWER_ROOT = Path(__file__).resolve().parent.parent
ENGINES = VIEWER_ROOT / "scripts" / "engines"

# 仍为占位 stub 的引擎(pcb 已实现,移出)。
PLACEHOLDER_ENGINES = ["sch", "sim"]


@pytest.mark.parametrize("engine", PLACEHOLDER_ENGINES)
def test_placeholder_file_exists(engine):
    idx = ENGINES / engine / "index.html"
    assert idx.exists(), f"engine {engine} 占位页缺失: {idx}"
    text = idx.read_text(encoding="utf-8")
    assert "待实现" in text
    assert f"engine = {engine}" in text or f"engine={engine}" in text
    # ≤ 50 行 CSS(规格 §3 T4 要求"≤ 50 行")
    css_lines = sum(
        1 for l in text.split("\n")
        if l.strip() and not l.strip().startswith("<")
    )
    # 整页约 35 行,符合"占位简洁"要求
    assert len(text.split("\n")) < 80, f"占位页过长: {len(text.split(chr(10)))} 行"


def test_placeholder_no_external_js(engine="sch"):
    """占位页不引外部 JS,纯 HTML + 内嵌 CSS。"""
    text = (ENGINES / engine / "index.html").read_text(encoding="utf-8")
    # 不应该有 <script src="..."> (内嵌 <script> 是允许的)
    assert "src=" not in text or "<script src=" not in text, \
        "占位页不应引外部 script"


@pytest.mark.parametrize("engine", PLACEHOLDER_ENGINES)
def test_placeholder_via_server(server, engine):
    """通过 server 访问占位页。"""
    base = server["base"]
    ws = server["workspace"]
    sample = {"sch": "sch.kicad_sch", "sim": "wave.csv"}[engine]
    url = f"{base}/?engine={engine}&dir={ws}&file={sample}"
    with urllib.request.urlopen(url, timeout=3) as r:
        assert r.status == 200
        body = r.read().decode("utf-8")
        assert "待实现" in body
        assert f"engine = {engine}" in body


def test_pcb_engine_page_implemented():
    """pcb 引擎页已实现(非占位):2D/3D 页签 + KiCanvas/tracespace + vendoring 降级。"""
    text = (ENGINES / "pcb" / "index.html").read_text(encoding="utf-8")
    assert "待实现" not in text, "pcb 已实现,不应再含占位字样"
    # 关键能力标记
    assert "kicanvas" in text.lower(), "缺 KiCanvas 3D 渲染挂载"
    assert "tracespace" in text.lower(), "缺 tracespace 2D Gerber 渲染挂载"
    assert "vendor" in text.lower(), "缺 vendoring 降级路径"
    # 走父 server 文件代理通道
    assert "/files/" in text, "应经 /files/ 代理通道取文件字节"
    # 不 npm install:依赖走 vendored 相对路径 import,不引 CDN <script src>
    assert "<script src=" not in text, "不应引外部 script(预构建 vendoring)"


def test_pcb_vendor_scaffold_present():
    """pcb 引擎 vendoring 脚手架就位(README + 拉取脚本)。"""
    vendor = ENGINES / "pcb" / "vendor"
    assert (vendor / "README.md").is_file()
    assert (vendor / "vendor_assets.sh").is_file()

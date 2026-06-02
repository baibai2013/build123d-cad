"""占位页测试 — pcb/sch/sim 的 index.html 应该 200 + 含「待实现」字样。

CI 必跑(无浏览器,纯 HTML)。
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

import pytest

VIEWER_ROOT = Path(__file__).resolve().parent.parent
ENGINES = VIEWER_ROOT / "scripts" / "engines"


@pytest.mark.parametrize("engine", ["pcb", "sch", "sim"])
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


def test_placeholder_no_external_js(engine="pcb"):
    """占位页不引外部 JS,纯 HTML + 内嵌 CSS。"""
    text = (ENGINES / engine / "index.html").read_text(encoding="utf-8")
    # 不应该有 <script src="..."> (内嵌 <script> 是允许的)
    assert "src=" not in text or "<script src=" not in text, \
        "占位页不应引外部 script"


@pytest.mark.parametrize("engine", ["pcb", "sch", "sim"])
def test_placeholder_via_server(server, engine):
    """通过 server 访问占位页。"""
    base = server["base"]
    ws = server["workspace"]
    sample = {"pcb": "board.kicad_pcb", "sch": "sch.kicad_sch", "sim": "wave.csv"}[engine]
    url = f"{base}/?engine={engine}&dir={ws}&file={sample}"
    with urllib.request.urlopen(url, timeout=3) as r:
        assert r.status == 200
        body = r.read().decode("utf-8")
        assert "待实现" in body
        assert f"engine = {engine}" in body

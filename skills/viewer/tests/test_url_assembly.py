"""URL 拼装单测 — 不起 server,纯模拟 start.sh 的拼接逻辑。

start.sh 在拿到 port 后会:
  http://127.0.0.1:<port>/?engine=<E>&dir=<encoded-abs>&file=<encoded-rel>

这里只验证:engine 路由正确 + URL 编码符合预期(空格/中文/特殊字符)。
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

import pytest

VIEWER_ROOT = Path(__file__).resolve().parent.parent
ROUTER = VIEWER_ROOT / "scripts" / "backend" / "router.mjs"


def _route(path: str):
    script = (
        f"import {{ routeByExtension }} from {json.dumps(str(ROUTER))};"
        f"const r = routeByExtension({json.dumps(path)});"
        f"process.stdout.write(JSON.stringify({{r}}));"
    )
    out = subprocess.check_output(
        ["node", "--input-type=module", "-e", script], text=True, timeout=5,
    )
    return json.loads(out)["r"]


def _encode(s: str):
    """复刻 start.sh 中 node encodeURIComponent(s)。"""
    out = subprocess.check_output(
        ["node", "-e", "process.stdout.write(encodeURIComponent(process.argv[1]))", s],
        text=True, timeout=5,
    )
    return out


def assemble(port: int, file_abs: str):
    """模拟 start.sh 的拼装逻辑(不起 server)。"""
    engine = _route(file_abs)
    if engine is None:
        return None
    p = Path(file_abs)
    return f"http://127.0.0.1:{port}/?engine={engine}&dir={_encode(str(p.parent))}&file={_encode(p.name)}"


@pytest.mark.parametrize("file_abs,expected_engine", [
    ("/tmp/proj/hip_bracket.step", "cad"),
    ("/tmp/proj/board.kicad_pcb", "pcb"),
    ("/tmp/proj/sch.kicad_sch", "sch"),
    ("/tmp/proj/wave.csv", "sim"),
])
def test_assemble_basic(file_abs, expected_engine):
    url = assemble(4188, file_abs)
    assert url is not None
    p = urlparse(url)
    assert p.hostname == "127.0.0.1"
    assert p.port == 4188
    q = parse_qs(p.query)
    assert q["engine"] == [expected_engine]
    assert unquote(q["dir"][0]) == str(Path(file_abs).parent)
    assert unquote(q["file"][0]) == Path(file_abs).name


def test_assemble_unsupported_returns_none():
    assert assemble(4188, "/tmp/foo.unknown") is None


@pytest.mark.parametrize("file_abs,expected_filename", [
    ("/tmp/proj/有 空格.step", "有 空格.step"),
    ("/tmp/proj/中文文件.stl", "中文文件.stl"),
    ("/tmp/proj/q?weird&name.step", "q?weird&name.step"),
    ("/tmp/proj/with#hash.step", "with#hash.step"),
])
def test_assemble_special_chars(file_abs, expected_filename):
    url = assemble(4188, file_abs)
    assert url is not None
    p = urlparse(url)
    q = parse_qs(p.query)
    # 解码后应得到原始名
    assert unquote(q["file"][0]) == expected_filename
    # 原始 URL 里 '?' '#' '&' 应被编码
    raw_query = p.query
    if "?" in expected_filename:
        assert "%3F" in raw_query
    if "&" in expected_filename:
        # '&' 在文件名里编码为 %26,与 query 分隔符 '&' 区分
        assert "file=" in raw_query and "%26" in raw_query
    if "#" in expected_filename:
        assert "%23" in raw_query


def test_url_protocol_only_127():
    """规格 §6:只允许 127.0.0.1 监听。"""
    url = assemble(4188, "/tmp/x.step")
    assert urlparse(url).hostname == "127.0.0.1"

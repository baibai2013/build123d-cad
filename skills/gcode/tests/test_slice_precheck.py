"""slice_precheck.py 测试(P1-1)。

离线主体:overhang 角度逻辑 / 贴床排除 / STL 解析 / gcode 注释解析 —— 纯函数,
无切片器、无 build123d 依赖。真切片 e2e 标 @slow(默认 skip,RUN_SLOW=1 才跑),
且本机无 OrcaSlicer 时自动 skip。
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import slice_precheck as sp  # noqa: E402


# ── 一个 2 三角形正方形 ASCII STL(z=5 平面,朝下),用于解析器测试 ──────────────
def _square_stl(z: float, facing_down: bool = True) -> str:
    # 顶点绕序决定法线朝向;facing_down 时法线 -Z
    a, b, c, d = (0, 0, z), (10, 0, z), (10, 10, z), (0, 10, z)
    if facing_down:
        tris = [(a, c, b), (a, d, c)]
    else:
        tris = [(a, b, c), (a, c, d)]
    lines = ["solid s"]
    for t in tris:
        lines.append(" facet normal 0 0 0")
        lines.append("  outer loop")
        for v in t:
            lines.append(f"   vertex {v[0]} {v[1]} {v[2]}")
        lines.append("  endloop")
        lines.append(" endfacet")
    lines.append("endsolid s")
    return "\n".join(lines)


# ── overhang 角度逻辑 ────────────────────────────────────────────────────────
def test_analyze_overhang_flags_elevated_ceiling():
    """悬空的水平天花(90°)应被标,贴床的同朝向面应被排除。"""
    facets = [
        sp.Facet(n=(0, 0, -1), area=100.0, zc=0.0),   # 贴床底面 → 排除
        sp.Facet(n=(0, 0, -1), area=50.0, zc=10.0),   # 悬空天花 → 90° 违规
        sp.Facet(n=(0, 0, 1), area=100.0, zc=12.0),   # 朝上 → 忽略
        sp.Facet(n=(1, 0, 0), area=80.0, zc=6.0),     # 竖直壁 → 忽略
    ]
    r = sp.analyze_overhang(facets, threshold_deg=45.0, bed_tol=0.5)
    assert r["overhang_face_count"] == 1
    assert r["max_overhang_deg"] == 90.0
    assert r["violations"][0]["area_mm2"] == 50.0


def test_overhang_threshold_boundary():
    """30° 下垂面:阈值 45 不报,阈值 25 报。"""
    nz = -math.sin(math.radians(30))
    f = sp.Facet(n=(math.sqrt(1 - nz * nz), 0, nz), area=20.0, zc=10.0)
    floor = sp.Facet(n=(0, 0, -1), area=10.0, zc=0.0)
    assert sp.analyze_overhang([f, floor], 45.0)["overhang_face_count"] == 0
    flagged = sp.analyze_overhang([f, floor], 25.0)
    assert flagged["overhang_face_count"] == 1
    assert abs(flagged["violations"][0]["angle_deg"] - 30.0) < 0.2


def test_analyze_overhang_empty():
    r = sp.analyze_overhang([], 45.0)
    assert r["overhang_face_count"] == 0 and r["max_overhang_deg"] == 0.0


# ── STL 解析 ─────────────────────────────────────────────────────────────────
def test_read_ascii_stl(tmp_path):
    p = tmp_path / "sq.stl"
    p.write_text(_square_stl(5.0, facing_down=True))
    facets = sp._read_stl(p)
    assert len(facets) == 2
    # 朝下面法线 z 分量为负
    assert all(f.n[2] < 0 for f in facets)
    assert abs(sum(f.area for f in facets) - 100.0) < 1e-6  # 10×10 正方形


def test_read_binary_stl_roundtrip(tmp_path):
    import struct
    # 手写一个二进制 STL:1 个三角形
    tri = [(0, 0, 0), (10, 0, 0), (0, 10, 0)]
    buf = bytearray(b"\x00" * 80) + struct.pack("<I", 1)
    buf += struct.pack("<3f", 0, 0, 1)
    for v in tri:
        buf += struct.pack("<3f", *v)
    buf += struct.pack("<H", 0)
    p = tmp_path / "b.stl"
    p.write_bytes(bytes(buf))
    facets = sp._read_stl(p)
    assert len(facets) == 1
    assert abs(facets[0].area - 50.0) < 1e-6


# ── gcode 注释解析 ───────────────────────────────────────────────────────────
_SAMPLE_GCODE = """\
; total layers count = 142
; filament used [mm] = 4523.18
; filament used [cm3] = 11.50
; total filament used [g] = 0.00
; enable_support = 0
; estimated printing time (normal mode) = 1h 47m 23s
G1 X0 Y0
"""


def test_parse_gcode_fields(tmp_path):
    g = tmp_path / "p.gcode"
    g.write_text(_SAMPLE_GCODE)
    r = sp.parse_gcode(g, material="PLA")
    assert r["layer_count"] == 142
    assert r["filament_mm"] == 4523.18
    assert r["filament_cm3"] == 11.50
    assert r["support_enabled"] is False
    # g 为 0 → 用 cm³×密度(PLA 1.24)兜底估
    assert r["filament_g_estimated"] is True
    assert abs(r["filament_g"] - 11.50 * 1.24) < 0.01
    assert abs(r["minutes"] - (60 + 47 + 23 / 60)) < 0.1


def test_parse_time_variants():
    assert sp._parse_time_to_min("24m 14s") == pytest.approx(24 + 14 / 60, abs=0.05)
    assert sp._parse_time_to_min("38s") == pytest.approx(38 / 60, abs=0.05)
    assert sp._parse_time_to_min("2h 0m 0s") == pytest.approx(120, abs=0.05)


# ── 端到端(不切片)──────────────────────────────────────────────────────────
def test_slice_precheck_no_slice(tmp_path):
    p = tmp_path / "sq.stl"
    p.write_text(_square_stl(10.0, facing_down=True))  # 悬空朝下面
    res = sp.slice_precheck(p, out_dir=tmp_path, do_slice=False)
    assert res["ok"] is True
    assert "overhang" in res
    assert res.get("slice") is None
    assert res["recommended_orientation"] == [0, 0, 1]


def test_missing_input_raises():
    with pytest.raises(FileNotFoundError):
        sp.slice_precheck("/nonexistent/nope.stl", do_slice=False)


def test_cli_no_slice_returns_zero(tmp_path, capsys):
    p = tmp_path / "sq.stl"
    p.write_text(_square_stl(5.0))
    code = sp.main([str(p), "--no-slice", "--json"])
    assert code == 0
    assert "overhang" in capsys.readouterr().out


# ── 真切片 e2e(slow:默认 skip;无 OrcaSlicer 也 skip)──────────────────────────
@pytest.mark.slow
def test_real_orca_slice(tmp_path):
    orca, _ = sp.locate_slicer()
    if not orca:
        pytest.skip("本机无 OrcaSlicer,跳过真切片")
    # 一个 20mm 立方体(底面贴床,无悬垂)
    import struct
    verts = []
    s = 20.0
    cube = [
        # 12 三角(6 面)— 简化:用 ASCII 更易读
    ]
    stl = tmp_path / "cube.stl"
    # ASCII 立方体
    pts = {
        "a": (0, 0, 0), "b": (s, 0, 0), "c": (s, s, 0), "d": (0, s, 0),
        "e": (0, 0, s), "f": (s, 0, s), "g": (s, s, s), "h": (0, s, s),
    }
    faces = [
        ("a", "d", "c"), ("a", "c", "b"),  # bottom
        ("e", "f", "g"), ("e", "g", "h"),  # top
        ("a", "b", "f"), ("a", "f", "e"),
        ("b", "c", "g"), ("b", "g", "f"),
        ("c", "d", "h"), ("c", "h", "g"),
        ("d", "a", "e"), ("d", "e", "h"),
    ]
    lines = ["solid c"]
    for tri in faces:
        lines.append(" facet normal 0 0 0\n  outer loop")
        for k in tri:
            v = pts[k]
            lines.append(f"   vertex {v[0]} {v[1]} {v[2]}")
        lines.append("  endloop\n endfacet")
    lines.append("endsolid c")
    stl.write_text("\n".join(lines))

    res = sp.slice_precheck(stl, out_dir=tmp_path, infill_pct=15, support="none")
    assert res["estimated_print_time_min"] and res["estimated_print_time_min"] > 0
    assert res["filament_used_g"] and res["filament_used_g"] > 0
    assert Path(res["slice"]["gcode"]).exists()
    assert res["overhang"]["overhang_face_count"] == 0  # 立方体底贴床,无悬垂

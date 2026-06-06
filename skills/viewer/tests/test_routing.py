"""router.mjs 后缀路由单测。

不依赖任何真实文件,只跑 node 子进程把 routeByExtension(path) 结果打回。
CI 在 ubuntu-latest 上要求 < 10s 全过(规格 §9)。

覆盖 03 §4.1 21 条目权威路由表(33 后缀)。
"""
import json
import subprocess
from pathlib import Path

import pytest

VIEWER_ROOT = Path(__file__).resolve().parent.parent
ROUTER = VIEWER_ROOT / "scripts" / "backend" / "router.mjs"


def _route(path: str):
    """跑 node + import router.mjs,返回路由结果(string 或 None)。"""
    script = (
        f"import {{ routeByExtension }} from {json.dumps(str(ROUTER))};"
        f"const r = routeByExtension({json.dumps(path)});"
        f"process.stdout.write(JSON.stringify({{r}}));"
    )
    out = subprocess.check_output(
        ["node", "--input-type=module", "-e", script],
        text=True,
        timeout=5,
    )
    return json.loads(out)["r"]


@pytest.mark.parametrize("path,expected", [
    # ===== cad engine(13 行 / 24 后缀)=====
    ("hip_bracket.step", "cad"),
    ("hip_bracket.STEP", "cad"),
    ("foo.stp", "cad"),
    ("body.brep", "cad"),
    ("legacy.iges", "cad"),
    ("legacy.igs", "cad"),
    ("foo.stl", "cad"),
    ("foo.glb", "cad"),
    ("foo.gltf", "cad"),
    ("mesh.obj", "cad"),
    ("foo.3mf", "cad"),
    ("native.fcstd", "cad"),
    ("robot.urdf", "cad"),
    ("robot.srdf", "cad"),
    ("robot.sdf", "cad"),
    ("path.gcode", "cad"),
    ("path.nc", "cad"),
    ("plate.dxf", "cad"),
    ("snapshot.png", "cad"),
    ("photo.jpg", "cad"),
    ("photo.JPEG", "cad"),
    ("hero.webp", "cad"),
    # ===== pcb engine =====
    ("board.kicad_pcb", "pcb"),
    ("board.gbr", "pcb"),
    ("board.ger", "pcb"),
    ("board.drl", "pcb"),
    ("BOARD.GTL", "pcb"),
    ("board.gbl", "pcb"),
    # ===== sch engine =====
    ("schematic.kicad_sch", "sch"),
    ("legacy.sch", "sch"),
    ("export.svg", "sch"),
    # ===== sim engine =====
    ("trace.csv", "sim"),
    ("clip.mp4", "sim"),
    ("rec.webm", "sim"),
    # ===== tscircuit engine(M2:.circuit.json 必须先于 .json 命中)=====
    ("led-demo.circuit.json", "tscircuit"),
    ("board.CIRCUIT.JSON", "tscircuit"),
    # ===== ambiguous(哨兵,server 据此回 409 + 提示需 ?engine= 透传)=====
    ("trajectory.json", "ambiguous"),
    ("config.JSON", "ambiguous"),
    # ===== 不支持 =====
    ("readme.md", None),
    ("noext", None),
    ("script.py", None),
])
def test_route_by_extension(path, expected):
    assert _route(path) == expected


def test_router_handles_null_input():
    script = (
        f"import {{ routeByExtension }} from {json.dumps(str(ROUTER))};"
        "process.stdout.write(JSON.stringify({"
        "n: routeByExtension(null),"
        "u: routeByExtension(undefined)"
        "}));"
    )
    out = subprocess.check_output(
        ["node", "--input-type=module", "-e", script],
        text=True, timeout=5,
    )
    data = json.loads(out)
    assert data["n"] is None
    assert data["u"] is None


def test_supported_engines_complete():
    """ENGINE_ROUTES 引用的引擎名 ⊆ SUPPORTED_ENGINES ∪ {'ambiguous' 哨兵}。"""
    script = (
        f"import {{ ENGINE_ROUTES, SUPPORTED_ENGINES }} from {json.dumps(str(ROUTER))};"
        "const seen = new Set(ENGINE_ROUTES.map(r => r.engine));"
        "process.stdout.write(JSON.stringify({"
        "engines: SUPPORTED_ENGINES,"
        "seen: Array.from(seen).sort()"
        "}));"
    )
    out = subprocess.check_output(
        ["node", "--input-type=module", "-e", script],
        text=True, timeout=5,
    )
    data = json.loads(out)
    real_engines = set(data["seen"]) - {"ambiguous"}
    assert real_engines.issubset(set(data["engines"]))
    # 5 个引擎都必须出现
    for e in ("cad", "pcb", "sch", "sim", "tscircuit"):
        assert e in data["seen"], f"engine {e} missing from ENGINE_ROUTES"


def test_supported_extensions_pinned_count():
    """SUPPORTED_EXTENSIONS 必须覆盖 03 §4.1 全部 33 个真后缀 + .yaml/.yml(配套配置)。"""
    script = (
        f"import {{ SUPPORTED_EXTENSIONS }} from {json.dumps(str(ROUTER))};"
        "process.stdout.write(JSON.stringify(SUPPORTED_EXTENSIONS));"
    )
    out = subprocess.check_output(
        ["node", "--input-type=module", "-e", script],
        text=True, timeout=5,
    )
    exts = set(json.loads(out))
    must_have = {
        ".step", ".stp", ".brep", ".iges", ".igs", ".stl", ".glb", ".gltf",
        ".obj", ".3mf", ".fcstd", ".urdf", ".srdf", ".sdf", ".gcode", ".nc",
        ".dxf", ".png", ".jpg", ".jpeg", ".webp",
        ".kicad_pcb", ".gbr", ".ger", ".drl", ".gtl", ".gbl",
        ".kicad_sch", ".sch", ".svg", ".csv", ".mp4", ".webm",
        ".circuit.json",  # M2 tscircuit engine
        ".json", ".yaml", ".yml",  # 配套配置
    }
    missing = must_have - exts
    assert not missing, f"SUPPORTED_EXTENSIONS missing: {missing}"

#!/usr/bin/env python3
"""FDM 切片预检(P1-1,build123d-cad · gcode 子技能)。

按 `05-制造出工链路 §3 / §8.1 / §8.4` 实现:STEP/STL 进来 → ①几何 overhang 预检
(自实现,直接读 STL 面法线)→ ②调 OrcaSlicer CLI 切片 → ③解析 .gcode 末尾注释
回报 估时 / 丝量 / 支撑。输出 schema 对齐 §8.4(给成本钩子 T5 消费)。

切片器策略(§8.1 决议):**OrcaSlicer 默认**,PrusaSlicer 降级备选;两者 G-code 末尾
注释字段同源(Slic3r 派生),解析逻辑共用。切片器没装 → fail loud 给 brew 命令,
**不静默降级**(SKILL.md 角色规则 4)。

设计取舍:
  - overhang 检查零依赖(纯 Python 解析 STL 二进制/ASCII + 面法线),任何 venv 可跑、
    离线可测;不依赖 build123d/trimesh。
  - STEP 输入才需 build123d(Mesher 转 STL);缺 build123d 时明确报错让传 STL。
  - OrcaSlicer 系统预设用 inherits 继承,headless 直接喂叶子可解析;但部分机型
    (Creality 等)默认相对挤出 + layer_gcode 缺 G92 E0 会校验失败 → 运行时拷机型
    预设副本、置 use_relative_e_distances=0 绕开(本机 OrcaSlicer 2.3.2 实测坑)。

命令行:
    python slice_precheck.py part.stl
    python slice_precheck.py part.stl --layer 0.2 --infill 20 --support auto
    python slice_precheck.py part.stl --no-slice          # 只跑几何 overhang 预检
    python slice_precheck.py part.stl --out output/demo --json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── 常量 ─────────────────────────────────────────────────────────────────────
# 切片器候选(§8.1:OrcaSlicer 默认,PrusaSlicer 降级)。
_ORCA_CANDIDATES = [
    "/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer",
    "orca-slicer",
    "orcaslicer",
    "OrcaSlicer",
]
_PRUSA_CANDIDATES = [
    "/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer",
    "prusa-slicer",
    "prusaslicer",
    "PrusaSlicer",
]
_ORCA_PROFILES = Path("/Applications/OrcaSlicer.app/Contents/Resources/profiles")

# 默认 OrcaSlicer 系统预设三件套(通用 0.4mm bedslinger,headless 实测可切)。
_DEFAULT_MACHINE = "Creality/machine/Creality Ender-3 0.4 nozzle.json"
_DEFAULT_PROCESS = "Creality/process/0.20mm Standard @Creality Ender3.json"
_DEFAULT_FILAMENT = "Creality/filament/Creality HF Generic PLA.json"

# 材料密度 g/cm³,用于 gcode 注释里 filament_g==0(预设没填密度)时兜底估重。
_DENSITY_G_CM3 = {"PLA": 1.24, "PETG": 1.27, "ABS": 1.04, "TPU": 1.21}

# 默认 overhang 阈值(度,从竖直方向量):有支撑可到 45°,无支撑 30°(SKILL.md 预检表)。
_OVERHANG_THRESHOLD_SUPPORTED = 45.0
_OVERHANG_THRESHOLD_NONE = 30.0

_SLICE_TIMEOUT_S = 180  # §8.1 降级触发:>120s 视超时,这里留余量


# ── STL 解析(零依赖)─────────────────────────────────────────────────────────
@dataclass
class Facet:
    """三角面片:由顶点叉乘算出的单位法线 + 面积 + z 质心(用于排除贴床面)。"""

    n: tuple[float, float, float]
    area: float
    zc: float


def _facet_from_verts(v0, v1, v2) -> Facet:
    """由三顶点算法线(右手)+ 面积 + z 质心;退化面返回零法线 0 面积。"""
    ax, ay, az = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
    bx, by, bz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]
    cx, cy, cz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
    mag = math.sqrt(cx * cx + cy * cy + cz * cz)
    zc = (v0[2] + v1[2] + v2[2]) / 3.0
    if mag < 1e-12:
        return Facet(n=(0.0, 0.0, 0.0), area=0.0, zc=zc)
    return Facet(n=(cx / mag, cy / mag, cz / mag), area=0.5 * mag, zc=zc)


def _read_stl(path: Path) -> list[Facet]:
    """读 STL(自动判二进制/ASCII),返回面片列表。法线一律由顶点重算(STL 头法线不可信)。"""
    raw = path.read_bytes()
    if not raw:
        raise ValueError(f"STL 为空:{path}")
    # ASCII 判定:以 'solid' 开头且含 'facet'(二进制可能恰好以 solid 开头,故再查 facet)。
    head = raw[:512].lstrip().lower()
    is_ascii = head.startswith(b"solid") and b"facet" in raw[:2048].lower()
    return _read_ascii_stl(raw) if is_ascii else _read_binary_stl(raw)


def _read_binary_stl(raw: bytes) -> list[Facet]:
    if len(raw) < 84:
        raise ValueError("二进制 STL 过短")
    (count,) = struct.unpack_from("<I", raw, 80)
    facets: list[Facet] = []
    off = 84
    for _ in range(count):
        if off + 50 > len(raw):
            break
        vals = struct.unpack_from("<12f", raw, off)  # 法线(忽略)+ 3 顶点
        v0, v1, v2 = vals[3:6], vals[6:9], vals[9:12]
        facets.append(_facet_from_verts(v0, v1, v2))
        off += 50
    return facets


def _read_ascii_stl(raw: bytes) -> list[Facet]:
    facets: list[Facet] = []
    verts: list[tuple[float, float, float]] = []
    for line in raw.decode("utf-8", "replace").splitlines():
        s = line.strip()
        if s.startswith("vertex"):
            parts = s.split()
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif s.startswith("endfacet"):
            if len(verts) >= 3:
                facets.append(_facet_from_verts(verts[0], verts[1], verts[2]))
            verts = []
    return facets


# ── overhang 几何预检(自实现,§8.3「法线投影 + 角度阈值」)─────────────────────
def analyze_overhang(
    facets: list[Facet], threshold_deg: float, bed_tol: float = 0.5
) -> dict[str, Any]:
    """统计朝下面片的 overhang 角(从竖直方向量:竖直壁=0°,水平天花=90°)。

    排除贴在打印床上的面(z 质心在模型最低点 + bed_tol 内,靠床自支撑,非悬垂);
    超阈值的面片计入 violations(按面积降序取前 N),并给总超限面积 + 最大角。
    """
    violations: list[dict[str, Any]] = []
    overhang_area = 0.0
    max_deg = 0.0
    n_down = 0
    z_min = min((f.zc for f in facets), default=0.0)
    for i, f in enumerate(facets):
        nz = f.n[2]
        if nz >= -1e-6:  # 只看朝下的面(法线 z 分量为负)
            continue
        if f.zc <= z_min + bed_tol:  # 贴床面,靠打印床支撑,不算悬垂
            continue
        n_down += 1
        # 从竖直方向的偏角:asin(|nz|),竖直壁(nz≈0)→0°,水平天花(nz=-1)→90°
        deg = math.degrees(math.asin(min(1.0, -nz)))
        max_deg = max(max_deg, deg)
        if deg > threshold_deg + 1e-6:
            overhang_area += f.area
            violations.append(
                {
                    "face_id": i,
                    "angle_deg": round(deg, 1),
                    "area_mm2": round(f.area, 2),
                }
            )
    violations.sort(key=lambda v: v["area_mm2"], reverse=True)
    return {
        "threshold_deg": threshold_deg,
        "max_overhang_deg": round(max_deg, 1),
        "down_facing_faces": n_down,
        "overhang_face_count": len(violations),
        "overhang_area_mm2_total": round(overhang_area, 2),
        "violations": violations[:20],  # 截前 20,避免巨网格刷屏
        "violations_truncated": len(violations) > 20,
    }


# ── STEP → STL(可选,需 build123d)────────────────────────────────────────────
def step_to_stl(step_path: Path, out_dir: Path) -> Path:
    """STEP 转 STL,走父技能 build123d(SKILL.md handoff 约定)。缺 build123d 明确报错。"""
    try:
        from build123d import Mesher, import_step  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "STEP 输入需 build123d(Mesher)。请在装了 build123d 的环境运行,"
            "或先自行转好传 STL。原始错误:%s" % exc
        ) from exc
    shape = import_step(str(step_path))
    stl_path = out_dir / (step_path.stem + ".stl")
    mesher = Mesher()
    mesher.add_shape(shape)
    mesher.write(str(stl_path))
    return stl_path


# ── 切片器定位 ───────────────────────────────────────────────────────────────
def _which(candidates: list[str]) -> str | None:
    for c in candidates:
        if os.path.isabs(c) and os.path.exists(c):
            return c
        found = shutil.which(c)
        if found:
            return found
    return None


def locate_slicer(prefer: str = "orca") -> tuple[str | None, str | None]:
    """返回 (orca_path, prusa_path)。"""
    return _which(_ORCA_CANDIDATES), _which(_PRUSA_CANDIDATES)


# ── OrcaSlicer 切片 ──────────────────────────────────────────────────────────
def _prepare_orca_profiles(
    work: Path, layer_mm: float, infill_pct: int, support: str
) -> tuple[str, str, str]:
    """拷系统预设到临时目录并按 flag override;返回 (machine, process, filament) 路径。

    - machine:置 use_relative_e_distances=0 绕开 layer_gcode G92 E0 校验坑。
    - process:override 层高 / 填充密度 / 支撑开关与类型。
    """
    def _load(rel: str) -> dict[str, Any]:
        return json.loads((_ORCA_PROFILES / rel).read_text(encoding="utf-8"))

    mach = _load(_DEFAULT_MACHINE)
    mach["use_relative_e_distances"] = "0"
    proc = _load(_DEFAULT_PROCESS)
    proc["layer_height"] = str(layer_mm)
    proc["sparse_infill_density"] = f"{infill_pct}%"
    if support == "none":
        proc["enable_support"] = "0"
    else:
        proc["enable_support"] = "1"
        proc["support_type"] = "tree(auto)" if support == "tree" else "normal(auto)"

    mp = work / "machine.json"
    pp = work / "process.json"
    fp = work / "filament.json"
    mp.write_text(json.dumps(mach), encoding="utf-8")
    pp.write_text(json.dumps(proc), encoding="utf-8")
    shutil.copyfile(_ORCA_PROFILES / _DEFAULT_FILAMENT, fp)
    return str(mp), str(pp), str(fp)


def run_orca_slice(
    orca: str, stl: Path, out_dir: Path, layer_mm: float, infill_pct: int, support: str
) -> Path:
    """调 OrcaSlicer headless 切片,返回生成的 .gcode 路径。失败抛 RuntimeError。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="orca_prof_") as td:
        mach, proc, fila = _prepare_orca_profiles(Path(td), layer_mm, infill_pct, support)
        cmd = [
            orca,
            "--load-settings", f"{mach};{proc}",
            "--load-filaments", fila,
            "--slice", "0",
            "--outputdir", str(out_dir),
            str(stl),
        ]
        try:
            proc_res = subprocess.run(
                cmd, capture_output=True, text=True, timeout=_SLICE_TIMEOUT_S
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"OrcaSlicer 切片超时(>{_SLICE_TIMEOUT_S}s)") from exc
        gcodes = sorted(out_dir.glob("*.gcode"))
        if proc_res.returncode != 0 or not gcodes:
            tail = (proc_res.stdout or "")[-800:] + (proc_res.stderr or "")[-800:]
            raise RuntimeError(
                f"OrcaSlicer 切片失败 rc={proc_res.returncode}:{tail.strip()}"
            )
        # 重命名为 <part>.gcode(OrcaSlicer 默认出 plate_1.gcode)
        target = out_dir / (stl.stem + ".gcode")
        if gcodes[0] != target:
            shutil.move(str(gcodes[0]), str(target))
        return target


# ── gcode 注释解析(OrcaSlicer / PrusaSlicer 同源字段)─────────────────────────
_TIME_RE = re.compile(r"estimated printing time.*?=\s*(.+)", re.I)
_FIL_MM_RE = re.compile(r"filament used \[mm\]\s*=\s*([\d.]+)", re.I)
_FIL_CM3_RE = re.compile(r"filament used \[cm3\]\s*=\s*([\d.]+)", re.I)
_FIL_G_RE = re.compile(r"(?:total )?filament used \[g\]\s*=\s*([\d.]+)", re.I)
_LAYERS_RE = re.compile(r"total layers? count\s*[:=]\s*(\d+)", re.I)
_SUPPORT_EN_RE = re.compile(r"enable_support\s*=\s*([01])", re.I)


def _parse_time_to_min(s: str) -> float:
    """'1h 47m 23s' / '24m 14s' / '38s' → 分钟(float)。"""
    h = re.search(r"([\d.]+)\s*h", s)
    m = re.search(r"([\d.]+)\s*m(?!s)", s)
    sec = re.search(r"([\d.]+)\s*s", s)
    total = 0.0
    if h:
        total += float(h.group(1)) * 60
    if m:
        total += float(m.group(1))
    if sec:
        total += float(sec.group(1)) / 60
    return round(total, 1)


def parse_gcode(gcode: Path, material: str = "PLA") -> dict[str, Any]:
    """解析 .gcode 注释:估时 / 丝长 / 丝重 / 层数 / 支撑开关。

    丝重为 0(预设缺密度)时,用 cm³ × 材料密度兜底估算。
    """
    text = gcode.read_text(encoding="utf-8", errors="replace")
    out: dict[str, Any] = {
        "gcode": str(gcode),
        "minutes": None,
        "filament_mm": None,
        "filament_cm3": None,
        "filament_g": None,
        "filament_g_estimated": False,
        "layer_count": None,
        "support_enabled": None,
    }
    if (mt := _TIME_RE.search(text)):
        out["minutes"] = _parse_time_to_min(mt.group(1))
    if (mm := _FIL_MM_RE.search(text)):
        out["filament_mm"] = float(mm.group(1))
    if (cm3 := _FIL_CM3_RE.search(text)):
        out["filament_cm3"] = float(cm3.group(1))
    if (g := _FIL_G_RE.search(text)):
        out["filament_g"] = float(g.group(1))
    if (lc := _LAYERS_RE.search(text)):
        out["layer_count"] = int(lc.group(1))
    if (se := _SUPPORT_EN_RE.search(text)):
        out["support_enabled"] = se.group(1) == "1"
    # 丝重兜底:g 缺失或为 0 → cm³ × 密度
    if (not out["filament_g"]) and out["filament_cm3"]:
        dens = _DENSITY_G_CM3.get(material.upper(), _DENSITY_G_CM3["PLA"])
        out["filament_g"] = round(out["filament_cm3"] * dens, 2)
        out["filament_g_estimated"] = True
    return out


# ── 主入口 ───────────────────────────────────────────────────────────────────
@dataclass
class PrecheckResult:
    input: str
    ok: bool = True
    overhang: dict[str, Any] = field(default_factory=dict)
    slice: dict[str, Any] | None = None
    # §8.4 成本钩子对齐字段(扁平,便于直接消费)
    estimated_print_time_min: float | None = None
    filament_used_g: float | None = None
    filament_used_m: float | None = None
    support_g: float | None = None
    overhang_violations: list[dict[str, Any]] = field(default_factory=list)
    recommended_orientation: list[float] = field(default_factory=lambda: [0, 0, 1])
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def slice_precheck(
    input_path: str | Path,
    out_dir: str | Path | None = None,
    layer_mm: float = 0.2,
    infill_pct: int = 20,
    support: str = "auto",
    material: str = "PLA",
    overhang_threshold: float | None = None,
    do_slice: bool = True,
) -> dict[str, Any]:
    """STEP/STL → overhang 预检 (+ 可选切片估时)。返回 §8.4 对齐的 dict。"""
    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(src)
    out = Path(out_dir).expanduser().resolve() if out_dir else src.parent
    out.mkdir(parents=True, exist_ok=True)
    res = PrecheckResult(input=str(src))

    # STEP → STL(overhang 与切片都需要网格)
    stl = src
    if src.suffix.lower() in (".step", ".stp"):
        stl = step_to_stl(src, out)
        res.notes.append(f"STEP 已转 STL:{stl.name}")

    # ① overhang 几何预检
    thr = overhang_threshold
    if thr is None:
        thr = _OVERHANG_THRESHOLD_NONE if support == "none" else _OVERHANG_THRESHOLD_SUPPORTED
    facets = _read_stl(stl)
    if not facets:
        raise ValueError(f"未解析到任何三角面:{stl}")
    res.overhang = analyze_overhang(facets, thr)
    res.overhang_violations = res.overhang["violations"]
    if res.overhang["overhang_face_count"] > 0:
        res.notes.append(
            f"overhang 超阈值面 {res.overhang['overhang_face_count']} 片"
            f"(>{thr}°,最大 {res.overhang['max_overhang_deg']}°);"
            f"建议倒角 / 改朝向 / 开支撑"
        )

    # ② 切片估时(可选)
    if do_slice:
        orca, prusa = locate_slicer()
        if not orca and not prusa:
            raise RuntimeError(
                "未找到切片器。OrcaSlicer 安装:brew install --cask orcaslicer "
                "(SKILL.md 角色规则 4:不静默降级)。或加 --no-slice 仅跑几何预检。"
            )
        if orca:
            gcode = run_orca_slice(orca, stl, out, layer_mm, infill_pct, support)
            sl = parse_gcode(gcode, material=material)
            sl["slicer"] = "OrcaSlicer"
        else:
            raise RuntimeError(
                "仅找到 PrusaSlicer,降级路径 P1 末实装(§8.1);本机请用 OrcaSlicer。"
            )
        sl["profile"] = {
            "layer_mm": layer_mm,
            "infill_pct": infill_pct,
            "support": support,
            "material": material,
        }
        res.slice = sl
        res.estimated_print_time_min = sl["minutes"]
        res.filament_used_g = sl["filament_g"]
        res.filament_used_m = round(sl["filament_mm"] / 1000, 3) if sl["filament_mm"] else None
        # support_g:支撑关 → 0;开 → 注释无法单独拆出,置 None 并说明(诚实)
        if sl["support_enabled"] is False:
            res.support_g = 0.0
        else:
            res.notes.append("支撑已开,但 gcode 注释未单列支撑丝重,support_g 暂记 null")
    else:
        res.notes.append("--no-slice:仅几何 overhang 预检,未调切片器")

    return res.to_dict()


# ── CLI ──────────────────────────────────────────────────────────────────────
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="slice_precheck.py",
        description="FDM 切片预检:overhang 几何检查 + OrcaSlicer 估时/丝量",
    )
    p.add_argument("input", help="STEP / STL 文件路径")
    p.add_argument("--out", default=None, help="输出目录(默认输入同目录)")
    p.add_argument("--layer", type=float, default=0.2, help="层高 mm(默认 0.2)")
    p.add_argument("--infill", type=int, default=20, help="填充密度 %%(默认 20)")
    p.add_argument(
        "--support", choices=["none", "auto", "tree"], default="auto", help="支撑(默认 auto)"
    )
    p.add_argument("--material", default="PLA", help="材料(PLA/PETG/ABS/TPU,默认 PLA)")
    p.add_argument(
        "--overhang-threshold", type=float, default=None,
        help="overhang 阈值角°(默认:有支撑 45 / 无支撑 30)",
    )
    p.add_argument("--no-slice", action="store_true", help="只跑几何 overhang 预检,不切片")
    p.add_argument("--json", action="store_true", help="只输出 JSON")
    return p


def _human_print(res: dict[str, Any]) -> None:
    oh = res.get("overhang", {})
    print(f"■ 输入:{res['input']}")
    print(
        f"■ overhang:朝下面 {oh.get('down_facing_faces')} 片,"
        f"超阈值({oh.get('threshold_deg')}°){oh.get('overhang_face_count')} 片,"
        f"最大 {oh.get('max_overhang_deg')}°,超限面积 {oh.get('overhang_area_mm2_total')} mm²"
    )
    for v in oh.get("violations", [])[:5]:
        print(f"    - face {v['face_id']}: {v['angle_deg']}° / {v['area_mm2']} mm²")
    if res.get("slice"):
        s = res["slice"]
        g = f"{res.get('filament_used_g')} g" + ("(估)" if s.get("filament_g_estimated") else "")
        print(
            f"■ 切片({s.get('slicer')}):{res.get('estimated_print_time_min')} min,"
            f"丝长 {res.get('filament_used_m')} m,丝重 {g},{s.get('layer_count')} 层"
        )
    for n in res.get("notes", []):
        print(f"  · {n}")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        res = slice_precheck(
            args.input,
            out_dir=args.out,
            layer_mm=args.layer,
            infill_pct=args.infill,
            support=args.support,
            material=args.material,
            overhang_threshold=args.overhang_threshold,
            do_slice=not args.no_slice,
        )
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        _human_print(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())

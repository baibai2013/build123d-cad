"""web_preview — 飞书/CI/Python 调用入口。

```
from web_preview import start, snapshot
url = start("/abs/path/to/foo.step")          # → 浏览器可点开的 URL
res = snapshot("/abs/path/to/foo.step")        # → {"tier":2,"kind":"png","path":...}
```

CLI:

```
python web_preview.py /abs/path/to/foo.step                # start，输出 URL
python web_preview.py --mode=auto     /abs/foo.step        # snapshot，三档降级
python web_preview.py --mode=snapshot /abs/foo.step        # 强制 Tier 2 PNG
python web_preview.py --probe         /abs/foo.step        # 强制 Tier 3 dimensions.json
```

设计:
- start() 仅包装 start.sh,不重复实现路由/端口/复用逻辑(避免双轨)。
- snapshot() 是 P1-5 headless 降级链(Tier 1 chromium → Tier 2 OCP/VTK PNG → Tier 3 dimensions JSON)。
  没有浏览器/GPU/桌面环境时仍能给出某种预览输出,让飞书机器人 / CI / 远程 ssh 都能用。
  完整规格见 references/headless-fallback.md 与 share/build123d-cad改造/03-viewer多引擎子技能.md §10。
- 失败语义:start() 抛 RuntimeError;snapshot(mode="auto") 逐级回落不静默,三档全挂才抛 HeadlessUnavailable。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
START_SH = SCRIPT_DIR / "start.sh"

DEFAULT_SIZE = (1024, 768)  # Tier 2 PNG 默认分辨率
DIMENSIONS_SCHEMA_VERSION = 1


class HeadlessUnavailable(RuntimeError):
    """三档降级链全部不可用(mode=web 时 Tier 1 不满足,或 mode=auto 时三档全挂)。"""


class _TierUnavailable(Exception):
    """单档内部信号:本档依赖缺失/执行失败,编排层据此回落下一档。

    携带 reason 给 tier_meta.json 的 fallback_reason 字段。
    """

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


# --------------------------------------------------------------------------- #
# Tier 1:完整交互 web viewer(浏览器可点开的 URL)                            #
# --------------------------------------------------------------------------- #

def start(file_path: str | os.PathLike, workspace: str | os.PathLike | None = None) -> str:
    """起 viewer server,返回可点开的 URL(start.sh stdout 唯一一行)。

    参数:
      file_path: 要预览的文件绝对路径
      workspace: workspace_root,缺省由 start.sh 推断(git 顶层 / 文件目录)

    异常:
      FileNotFoundError: 文件不存在(start.sh exit 3)
      ValueError: 后缀不支持(start.sh exit 2)
      RuntimeError: 端口分配失败(start.sh exit 4)或其它
    """
    file_path = str(Path(file_path).resolve())
    cmd = ["bash", str(START_SH), file_path]
    if workspace:
        cmd.append(str(Path(workspace).resolve()))

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode == 0:
        return proc.stdout.strip()

    err = (proc.stderr or "").strip()
    if proc.returncode == 3:
        raise FileNotFoundError(err or file_path)
    if proc.returncode == 2:
        raise ValueError(err or "unsupported extension or bad args")
    if proc.returncode == 4:
        raise RuntimeError(f"port allocation failed: {err}")
    raise RuntimeError(f"start.sh exit {proc.returncode}: {err}")


# --------------------------------------------------------------------------- #
# 降级链编排                                                                   #
# --------------------------------------------------------------------------- #

@dataclass
class _Ctx:
    """一次 snapshot 调用的上下文。"""
    file_path: Path
    workspace: Path | None
    base_dir: Path          # 产物根目录(out 覆盖,缺省为源文件所在目录)
    size: tuple[int, int]
    stem: str = field(init=False)
    viewer_dir: Path = field(init=False)

    def __post_init__(self):
        self.stem = self.file_path.stem
        self.viewer_dir = self.base_dir / "_viewer"


def detect_tier() -> int:
    """探测当前环境可用的最高档,返回 1/2/3。三档都不满足抛 HeadlessUnavailable。

    与 03 §10.3 一致:
      Tier 1 需 playwright 可 import 且 chromium 已装;
      Tier 2 需 OCP 或 vtk 任一可 import;
      Tier 3 需 steputils 或 OCP 任一可 import。
    """
    # Tier 1
    if importlib.util.find_spec("playwright") is not None and _chromium_installed():
        return 1

    # Tier 2
    has_ocp = importlib.util.find_spec("OCP") is not None
    has_vtk = importlib.util.find_spec("vtk") is not None
    if has_ocp or has_vtk:
        return 2

    # Tier 3
    has_step_parser = importlib.util.find_spec("steputils") is not None or has_ocp
    if has_step_parser:
        return 3

    raise HeadlessUnavailable("all tiers unavailable(无 playwright/OCP/vtk/steputils)")


def _chromium_installed() -> bool:
    """`playwright install --dry-run chromium` exit 0 视为 chromium 已装。"""
    if os.environ.get("PLAYWRIGHT_DISABLED"):
        return False
    try:
        r = subprocess.run(
            ["playwright", "install", "--dry-run", "chromium"],
            capture_output=True, timeout=20,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def snapshot(file_path, workspace=None, mode: str = "auto", out=None, size=None) -> dict:
    """headless 降级链入口。返回 tier 结果 dict,并写 _viewer/tier_meta.json 审计。

    参数:
      file_path: 要预览的文件绝对路径
      workspace: workspace_root(Tier 1 透传 start.sh,Tier 2/3 不需要)
      mode:      auto / web / snapshot / probe(见下)
      out:       产物根目录;缺省为源文件所在目录
      size:      Tier 2 PNG 分辨率 (w, h),缺省 1024×768

    mode 语义(03 §10.1):
      auto     —— Tier 1 → 2 → 3 逐级尝试,每级失败回落,三档全挂才抛 HeadlessUnavailable
      web      —— 强制 Tier 1,失败抛 HeadlessUnavailable
      snapshot —— 强制 Tier 2(跳过 Tier 1)
      probe    —— 强制 Tier 3(只解析尺寸不渲染)

    返回 dict:
      {"tier":1|2|3, "kind":"url"|"png"|"json", "path":<abs>,
       "fallback_reason":<str|None>, "duration_ms":<int>}
    """
    fp = Path(file_path).resolve()
    if not fp.exists():
        raise FileNotFoundError(str(fp))

    base = Path(out).resolve() if out else fp.parent
    ctx = _Ctx(
        file_path=fp,
        workspace=Path(workspace).resolve() if workspace else None,
        base_dir=base,
        size=tuple(size) if size else DEFAULT_SIZE,
    )

    # mode → 尝试顺序
    order = {
        "auto": [1, 2, 3],
        "web": [1],
        "snapshot": [2],
        "probe": [3],
    }.get(mode)
    if order is None:
        raise ValueError(f"未知 mode={mode!r},应为 auto/web/snapshot/probe 之一")

    tier_fns = {1: _tier1_web, 2: _tier2_png, 3: _tier3_probe}
    attempted: list[int] = []
    last_reason: str | None = None
    t0 = time.perf_counter()

    for tier in order:
        attempted.append(tier)
        try:
            kind, path, tool = tier_fns[tier](ctx)
        except _TierUnavailable as e:
            last_reason = e.reason
            continue  # 回落下一档
        duration_ms = int((time.perf_counter() - t0) * 1000)
        result = {
            "tier": tier,
            "kind": kind,
            "path": str(path),
            "fallback_reason": last_reason,
            "duration_ms": duration_ms,
        }
        _write_tier_meta(ctx, result, attempted, tool)
        return result

    # 走到这里:order 内所有档都回落了
    duration_ms = int((time.perf_counter() - t0) * 1000)
    if mode == "web":
        raise HeadlessUnavailable(f"Tier 1 不可用:{last_reason}")
    raise HeadlessUnavailable(
        f"全部档位失败(尝试 {attempted}):{last_reason}(duration {duration_ms}ms)"
    )


def _write_tier_meta(ctx: _Ctx, result: dict, attempted: list[int], tool: str) -> None:
    """写降级链审计字段到 _viewer/tier_meta.json(03 §10.4)。"""
    ctx.viewer_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "tier": result["tier"],
        "kind": result["kind"],
        "path": result["path"],
        "fallback_reason": result["fallback_reason"],
        "tier_attempted": attempted,
        "duration_ms": result["duration_ms"],
        "tool": tool,
        "ts": _now_iso(),
    }
    (ctx.viewer_dir / "tier_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# Tier 1 实现:playwright + chromium → URL(+ 可选截图)                       #
# --------------------------------------------------------------------------- #

def _tier1_web(ctx: _Ctx) -> tuple[str, Path, str]:
    """起完整 web viewer,写 preview.url;chromium 可用时附带 snapshot.png。

    主产物是 _viewer/preview.url(单行 URL 文本,飞书可直接贴链接);
    截图是可选增强,截图失败不影响主产物。
    """
    if importlib.util.find_spec("playwright") is None:
        raise _TierUnavailable("playwright not installed")
    if not _chromium_installed():
        raise _TierUnavailable("chromium not installed")

    try:
        url = start(ctx.file_path, ctx.workspace)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        raise _TierUnavailable(f"viewer server 起不来: {e}")

    ctx.viewer_dir.mkdir(parents=True, exist_ok=True)
    url_path = ctx.viewer_dir / "preview.url"
    url_path.write_text(url + "\n", encoding="utf-8")

    # 可选:playwright 截一张静态图(与用户浏览器所见 1:1)
    try:
        _playwright_screenshot(url, ctx.viewer_dir / "snapshot.png", ctx.size)
    except Exception:
        # 截图失败不致命:主产物 URL 已写好,用户仍可点开
        pass

    return "url", url_path, "playwright"


def _playwright_screenshot(url: str, out_png: Path, size: tuple[int, int]) -> None:
    """headless chromium 打开 URL,等画布就绪后截图。"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--use-gl=swiftshader", "--enable-webgl"],
        )
        try:
            page = browser.new_page(viewport={"width": size[0], "height": size[1]})
            page.goto(url, wait_until="networkidle", timeout=30000)
            # 等 Three.js canvas 出现(cad engine 渲染就绪信号)
            try:
                page.wait_for_selector("canvas", timeout=15000)
                page.wait_for_timeout(1500)  # 给一帧渲染时间
            except Exception:
                pass
            page.screenshot(path=str(out_png))
        finally:
            browser.close()


# --------------------------------------------------------------------------- #
# Tier 2 实现:OCP / VTK 离屏渲染 → PNG                                        #
# --------------------------------------------------------------------------- #

def _tier2_png(ctx: _Ctx) -> tuple[str, Path, str]:
    """离屏渲染一张 PNG,落在源文件同级 `<stem>.preview.png`(03 §10.4 sibling)。

    策略:先把模型变成三角网格(.stl 直接用;.step/.brep/.iges 等用 OCP/build123d
    转临时 STL),再用 VTK 离屏管线渲成 PNG。VTK 不可用时回落 _TierUnavailable。
    """
    out_png = ctx.base_dir / f"{ctx.stem}.preview.png"
    ctx.base_dir.mkdir(parents=True, exist_ok=True)

    has_vtk = importlib.util.find_spec("vtk") is not None
    has_ocp = importlib.util.find_spec("OCP") is not None
    if not (has_vtk or has_ocp):
        raise _TierUnavailable("无 vtk / OCP,Tier 2 不可用")

    suffix = ctx.file_path.suffix.lower()

    # 1) 准备一个 STL(VTK 能直接吃 mesh)
    if suffix == ".stl":
        stl_path = ctx.file_path
        tool = "vtk"
    else:
        # 非 mesh 格式:用 OCP/build123d 先 tessellate 成临时 STL
        if not has_ocp:
            raise _TierUnavailable(
                f"{suffix} 需要 OCP 转网格,但 OCP 不可用(只有 vtk 无法直接读 {suffix})"
            )
        stl_path = _step_to_stl(ctx.file_path)
        tool = "ocp+vtk"

    # 2) VTK 离屏渲染
    if not has_vtk:
        raise _TierUnavailable("OCP 可转网格但无 vtk 渲染后端,Tier 2 不可用")
    _render_stl_to_png_vtk(stl_path, out_png, ctx.size)

    return "png", out_png, tool


def _step_to_stl(model_path: Path) -> Path:
    """用 build123d/OCP 把 STEP/BREP/IGES 等转成临时 STL(供 VTK 加载)。"""
    try:
        from build123d import import_step, export_stl
    except ImportError as e:
        raise _TierUnavailable(f"build123d 不可用,无法转网格: {e}")

    import tempfile

    try:
        shape = import_step(str(model_path))
    except Exception as e:
        raise _TierUnavailable(f"import_step 失败: {e}")

    tmp = Path(tempfile.gettempdir()) / f"_viewer_tess_{model_path.stem}.stl"
    try:
        export_stl(shape, str(tmp))
    except Exception as e:
        raise _TierUnavailable(f"export_stl 失败: {e}")
    return tmp


def _render_stl_to_png_vtk(stl_path: Path, out_png: Path, size: tuple[int, int]) -> None:
    """VTK 离屏管线:读 STL → 三轴视角 → 渲成 PNG。"""
    import vtk

    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(stl_path))
    reader.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.75, 0.78, 0.82)  # 浅灰金属感

    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(0.12, 0.12, 0.12)  # 与 cad engine 暗底统一(#1e1e1e 近似)

    render_window = vtk.vtkRenderWindow()
    render_window.SetOffScreenRendering(1)  # 关键:无桌面环境也能渲
    render_window.AddRenderer(renderer)
    render_window.SetSize(size[0], size[1])

    # 等距视角 + 自适应取景
    renderer.GetActiveCamera().Azimuth(30)
    renderer.GetActiveCamera().Elevation(30)
    renderer.ResetCamera()
    render_window.Render()

    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(render_window)
    w2if.Update()

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out_png))
    writer.SetInputConnection(w2if.GetOutputPort())
    writer.Write()


# --------------------------------------------------------------------------- #
# Tier 3 实现:命令行尺寸 JSON(probe-only,不渲染)                            #
# --------------------------------------------------------------------------- #

def _tier3_probe(ctx: _Ctx) -> tuple[str, Path, str]:
    """只解析 STEP 元数据,写 `<stem>.dimensions.json`(03 §10.5)。

    OCP 后端能给全字段(体积/面积/拓扑);steputils 后端只能给 bbox,
    其余写 null(不瞎填 0)。
    """
    out_json = ctx.base_dir / f"{ctx.stem}.dimensions.json"
    ctx.base_dir.mkdir(parents=True, exist_ok=True)

    has_ocp = importlib.util.find_spec("OCP") is not None
    has_steputils = importlib.util.find_spec("steputils") is not None

    if has_ocp:
        dims = _probe_dimensions_ocp(ctx.file_path)
        tool = "ocp"
    elif has_steputils:
        dims = _probe_dimensions_steputils(ctx.file_path)
        tool = "steputils"
    else:
        raise _TierUnavailable("无 OCP / steputils,Tier 3 不可用")

    out_json.write_text(
        json.dumps(dims, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return "json", out_json, tool


def _probe_dimensions_ocp(model_path: Path) -> dict:
    """OCP/build123d 解析全字段尺寸(bbox/体积/面积/拓扑/质心)。"""
    try:
        from build123d import import_step
        from OCP.BRepGProp import BRepGProp
        from OCP.GProp import GProp_GProps
        from OCP.TopAbs import (
            TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_SOLID, TopAbs_SHELL,
        )
        from OCP.TopExp import TopExp_Explorer
    except ImportError as e:
        raise _TierUnavailable(f"OCP/build123d import 失败: {e}")

    try:
        shape = import_step(str(model_path))
    except Exception as e:
        raise _TierUnavailable(f"import_step 失败: {e}")

    wrapped = shape.wrapped
    bb = shape.bounding_box()

    vol_props = GProp_GProps()
    BRepGProp.VolumeProperties_s(wrapped, vol_props)
    volume = vol_props.Mass()
    com = vol_props.CentreOfMass()

    surf_props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(wrapped, surf_props)
    area = surf_props.Mass()

    def _count(topo_type) -> int:
        exp = TopExp_Explorer(wrapped, topo_type)
        n = 0
        while exp.More():
            n += 1
            exp.Next()
        return n

    return _build_dimensions(
        source_file=model_path.name,
        bbox_min=[round(bb.min.X, 4), round(bb.min.Y, 4), round(bb.min.Z, 4)],
        bbox_max=[round(bb.max.X, 4), round(bb.max.Y, 4), round(bb.max.Z, 4)],
        volume_mm3=round(volume, 4),
        surface_area_mm2=round(area, 4),
        topology={
            "solids": _count(TopAbs_SOLID),
            "shells": _count(TopAbs_SHELL),
            "faces": _count(TopAbs_FACE),
            "edges": _count(TopAbs_EDGE),
            "vertices": _count(TopAbs_VERTEX),
        },
        centroid_mm=[round(com.X(), 4), round(com.Y(), 4), round(com.Z(), 4)],
        tool="ocp",
    )


def _probe_dimensions_steputils(model_path: Path) -> dict:
    """steputils 后端:只解析 bbox(无几何核,体积/面积/拓扑给 null)。"""
    try:
        from steputils import p21  # noqa: F401
    except ImportError as e:
        raise _TierUnavailable(f"steputils import 失败: {e}")

    # steputils 只能解 STEP 文本结构,拿不到几何包围盒;
    # 这里诚实地给 null,留待 OCP 后端补全(不瞎填 0)。
    return _build_dimensions(
        source_file=model_path.name,
        bbox_min=None,
        bbox_max=None,
        volume_mm3=None,
        surface_area_mm2=None,
        topology=None,
        centroid_mm=None,
        tool="steputils",
    )


def _build_dimensions(
    *, source_file, bbox_min, bbox_max, volume_mm3, surface_area_mm2,
    topology, centroid_mm, tool,
) -> dict:
    """按 03 §10.5 schema 组装 dimensions.json(单一组装点,便于测试)。"""
    size = None
    if bbox_min is not None and bbox_max is not None:
        size = {
            "x": round(bbox_max[0] - bbox_min[0], 4),
            "y": round(bbox_max[1] - bbox_min[1], 4),
            "z": round(bbox_max[2] - bbox_min[2], 4),
        }
    return {
        "schema_version": DIMENSIONS_SCHEMA_VERSION,
        "source_file": source_file,
        "bbox_mm": ({"min": bbox_min, "max": bbox_max} if bbox_min is not None else None),
        "size_mm": size,
        "volume_mm3": volume_mm3,
        "surface_area_mm2": surface_area_mm2,
        "mass_kg": None,  # 默认 null;mechanical 提供材料后由 02 的脚本补
        "topology": topology,
        "centroid_mm": centroid_mm,
        "tool": tool,
        "ts": _now_iso(),
    }


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #

def _cli():
    parser = argparse.ArgumentParser(
        description="viewer 预览入口:start(URL) 或 snapshot(headless 降级链)"
    )
    parser.add_argument("file_path", help="要预览的文件绝对路径")
    parser.add_argument("workspace", nargs="?", default=None, help="workspace_root(可选)")
    parser.add_argument(
        "--mode",
        choices=["start", "auto", "web", "snapshot", "probe"],
        default="start",
        help="start=只起 server 返 URL(默认);auto/web/snapshot/probe=走 snapshot 降级链",
    )
    parser.add_argument("--probe", action="store_true", help="等价 --mode=probe")
    parser.add_argument("--out", default=None, help="产物根目录(缺省为源文件目录)")
    parser.add_argument("--size", default=None, help="Tier 2 PNG 分辨率,如 512x384")
    args = parser.parse_args()

    mode = "probe" if args.probe else args.mode
    size = None
    if args.size:
        try:
            w, h = args.size.lower().split("x")
            size = (int(w), int(h))
        except ValueError:
            print(f"error: 非法 --size={args.size!r},应为 WxH(如 1024x768)", file=sys.stderr)
            sys.exit(2)

    try:
        if mode == "start":
            print(start(args.file_path, args.workspace))
        else:
            res = snapshot(args.file_path, args.workspace, mode=mode, out=args.out, size=size)
            print(json.dumps(res, ensure_ascii=False))
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
    except HeadlessUnavailable as e:
        print(f"error: headless 降级链不可用: {e}", file=sys.stderr)
        sys.exit(5)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()

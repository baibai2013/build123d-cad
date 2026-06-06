#!/usr/bin/env python3
"""skidl 脚本化原理图 → netlist(P3-2,build123d-cad · pcb 子技能)。

`python sch_from_skidl.py <design.py>` → 跑用户的 skidl 设计脚本 → 出 ``<design>.net``
(KiCad 网表)。``.net`` 由 KiCad/eeschema「导入网表」一键变 ``.kicad_sch``
(GUI 步骤,无对应 kicad-cli 子命令,见 references/skidl-quickstart.md)。

**零互引用红线的解法(对应 06 §3.3a.2 待决项)**:
本脚本**不** subprocess 反向调 ``electronics-bom/lookup.py``(那会违反 08 §1
「子技能间零互引用」)。改走**文件接口**:由 agent/父 SKILL 先调 electronics-bom
把选好的料落成 ``output/<task>/electrical/library/library.json``,本脚本用
``--library`` 读它,把 part_no → footprint 映射喂给 skidl。保持文件接口、可独立测。

library.json schema(electronics-bom lookup.py 的产出约定):
    { "<part_no>": {"footprint": "Package_TO_SOT_SMD:SOT-23",
                    "lcsc_id": "C...", "value": "...", ...}, ... }

设计:skidl 缺失 → fail loud 给安装提示,不静默(对齐 gcode/slice_precheck 约定)。

命令行:
    python sch_from_skidl.py design.py
    python sch_from_skidl.py design.py --library output/m3/electrical/library/library.json
    python sch_from_skidl.py design.py --out output/m3/electrical/board.net
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pcb_common import logger, setup_logging  # noqa: E402

_SKIDL_HINT = (
    "未安装 skidl。安装(装进 CAD 环境,非 company 生产 venv):\n"
    "  pip install skidl\n"
    "skidl 是纯 Python 网表 DSL,无需 KiCad 即可出 .net;文档 references/skidl-quickstart.md"
)


class SkidlNotFound(RuntimeError):
    """skidl 缺失。fail-loud 异常,携带安装提示。"""


def _require_skidl():
    """惰性导入 skidl;缺失抛 SkidlNotFound(不静默)。"""
    try:
        import skidl  # noqa: WPS433
    except ImportError as exc:
        raise SkidlNotFound(_SKIDL_HINT) from exc
    return skidl


def load_library(library_path: str | Path | None) -> dict:
    """读 electronics-bom 产出的 library.json(文件接口,不调其代码)。

    缺省 / 文件不存在 → return {}(skidl 设计里自带 footprint 时不依赖它)。
    """
    if not library_path:
        return {}
    p = Path(library_path).expanduser()
    if not p.is_file():
        logger.warning("library.json 不存在,跳过料库映射:%s", p)
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"library.json 顶层应为 {{part_no: {{...}}}} 映射:{p}")
    logger.info("载入料库 %d 条:%s", len(data), p)
    return data


def _exec_design(design_py: Path) -> None:
    """执行用户的 skidl 设计脚本(定义电路)。脚本内用 skidl Part/Net 描述电路。"""
    spec = importlib.util.spec_from_file_location("_skidl_design", design_py)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载设计脚本:{design_py}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # 设计脚本副作用:把元件加进 skidl 默认电路


def generate(design_py: str | Path, out_net: Path, library: dict | None = None) -> Path:
    """跑 skidl 设计 → 写 KiCad 网表 .net。返回 .net 路径。"""
    skidl = _require_skidl()
    design_py = Path(design_py).expanduser()
    if not design_py.is_file():
        raise FileNotFoundError(design_py)

    # 料库映射通过环境变量交给设计脚本可选读取(文件接口,松耦合)。
    if library:
        os.environ["PCB_LIBRARY_JSON"] = json.dumps(library, ensure_ascii=False)

    skidl.reset()  # 清空默认电路,避免重复跑污染
    _exec_design(design_py)
    out_net.parent.mkdir(parents=True, exist_ok=True)
    # skidl 默认出 KiCad 网表格式。
    skidl.generate_netlist(file_=str(out_net))
    logger.info("netlist 已生成:%s", out_net)
    return out_net


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sch_from_skidl.py", description="skidl 设计脚本 → KiCad 网表 .net"
    )
    p.add_argument("design", help="skidl 设计脚本(.py),用 skidl Part/Net 描述电路")
    p.add_argument("--library", default=None, help="electronics-bom 产出的 library.json(料→封装)")
    p.add_argument("--out", default=None, help="输出 .net 路径(默认 = 设计同名 .net)")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    setup_logging(args.verbose)
    design_py = Path(args.design).expanduser()
    out_net = Path(args.out).expanduser() if args.out else design_py.with_suffix(".net")
    try:
        lib = load_library(args.library)
        generate(design_py, out_net, lib)
    except SkidlNotFound as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 127
    except (FileNotFoundError, ImportError, ValueError) as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1
    print(f"✓ netlist → {out_net}")
    print("  下一步:KiCad/eeschema「工具→从网表更新原理图」导入,或新建工程后 import")
    return 0


if __name__ == "__main__":
    sys.exit(main())

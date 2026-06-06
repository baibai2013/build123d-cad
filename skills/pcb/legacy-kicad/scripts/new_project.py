#!/usr/bin/env python3
"""起一个空白 KiCad 9.x 工程骨架(P3-1,build123d-cad · pcb 子技能)。

`python new_project.py <name>` → 写出工程三件套:
    <name>.kicad_pro   工程配置(JSON)
    <name>.kicad_pcb   空板(S-expression,含必需的 layers/setup 块)
    <name>.kicad_sch   空原理图(S-expression)

设计:**纯模板写文件,不依赖 kicad-cli**,任何环境可跑、可测。
模板对齐 KiCad 9.0 文件格式(version 时间戳为 9.0 GA 值);KiCad 打开后
可正常另存,GUI/CLI 会按需补全细节。后续 layout 走 KiCad GUI 或 batch_edit.py。

命令行:
    python new_project.py hip_driver
    python new_project.py hip_driver --task m3-demo        # 落 output/m3-demo/electrical/
    python new_project.py hip_driver --out /tmp/board
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 同目录公共工具。脚本既可 `python new_project.py` 直跑,也可被 tests import。
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pcb_common import electrical_output_dir, logger, setup_logging  # noqa: E402

# KiCad 9.0 文件格式版本时间戳(GA 值)。新工程用这套,KiCad 打开会原样接受。
_PCB_VERSION = 20241229
_SCH_VERSION = 20250114
_GENERATOR = "build123d-cad-pcb"

# ── 三件套模板 ────────────────────────────────────────────────────────────────
def _pro_template(name: str) -> str:
    """.kicad_pro:工程配置 JSON。最小可用键集,KiCad 打开后自动补默认。"""
    pro = {
        "board": {"design_settings": {}, "layer_presets": [], "viewports": []},
        "boards": [],
        "meta": {"filename": f"{name}.kicad_pro", "version": 1},
        "net_settings": {"classes": [{"name": "Default", "clearance": 0.2}]},
        "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [],
        "text_variables": {},
    }
    return json.dumps(pro, indent=2, ensure_ascii=False) + "\n"


def _pcb_template() -> str:
    """.kicad_pcb:空板。含 KiCad 必需的 general/paper/layers/setup 块。"""
    return f"""(kicad_pcb
\t(version {_PCB_VERSION})
\t(generator "{_GENERATOR}")
\t(generator_version "9.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A4")
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1")
\t\t(23 "Eco2.User" user "User.Eco2")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t)
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t)
\t(net 0 "")
)
"""


def _sch_template(name: str) -> str:
    """.kicad_sch:空原理图。skidl 出 .net 后由 KiCad import 填充元件;此处仅占位根图。"""
    return f"""(kicad_sch
\t(version {_SCH_VERSION})
\t(generator "{_GENERATOR}")
\t(generator_version "9.0")
\t(uuid "00000000-0000-0000-0000-000000000000")
\t(paper "A4")
\t(lib_symbols)
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
)
"""


def create_project(name: str, out_dir: Path) -> dict[str, Path]:
    """写三件套到 out_dir,返回 {pro, pcb, sch} 路径。已存在则报错不覆盖。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "pro": out_dir / f"{name}.kicad_pro",
        "pcb": out_dir / f"{name}.kicad_pcb",
        "sch": out_dir / f"{name}.kicad_sch",
    }
    existing = [p for p in files.values() if p.exists()]
    if existing:
        raise FileExistsError(
            f"目标已存在,拒绝覆盖:{', '.join(str(p) for p in existing)}(换 name 或清理目录)"
        )
    files["pro"].write_text(_pro_template(name), encoding="utf-8")
    files["pcb"].write_text(_pcb_template(), encoding="utf-8")
    files["sch"].write_text(_sch_template(name), encoding="utf-8")
    logger.info("已创建工程 %s 于 %s", name, out_dir)
    return files


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="new_project.py", description="起一个空白 KiCad 9.x 工程三件套"
    )
    p.add_argument("name", help="工程名(不含扩展名),如 hip_driver")
    p.add_argument("--task", default=None, help="task 名 → 落 output/<task>/electrical/")
    p.add_argument("--out", default=None, help="直接指定输出目录(覆盖 --task 逻辑)")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    setup_logging(args.verbose)
    if args.out:
        out_dir = Path(args.out).expanduser()
    else:
        out_dir = electrical_output_dir(args.task) / args.name
    try:
        files = create_project(args.name, out_dir)
    except FileExistsError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1
    print(f"✓ KiCad 工程已创建:{out_dir}")
    for kind, path in files.items():
        print(f"  {kind}: {path.name}")
    print("  下一步:KiCad GUI 打开 layout,或 sch_from_skidl.py 注入原理图")
    return 0


if __name__ == "__main__":
    sys.exit(main())

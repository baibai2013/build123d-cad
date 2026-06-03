#!/usr/bin/env python3
"""kicad-skip 批量改既有 KiCad 工程(P3-2,build123d-cad · pcb 子技能)。

`python batch_edit.py <board>.kicad_pcb --rule rules.yaml` → 按规则批量改既有工程
(换封装 / 换电源符号 / 扫元件型号),不启动 KiCad、纯 S-expression 解析。

用 kicad-skip(psychogenic/kicad-skip):轻量、可 CI、不做几何级布线,只动元数据
(选型用 skidl 走 sch_from_skidl.py;复杂插件流程才上 kicad-python IPC,见 §4.2)。

rules.yaml schema(初版,逐步扩):
    replace_footprint:           # 全局换封装
      - { from: "R_0603", to: "R_0402" }
    set_field:                   # 给匹配 refdes 的元件设字段
      - { refdes_prefix: "R", field: "Tolerance", value: "1%" }

设计:kicad-skip 缺失 → fail loud 给安装提示,不静默。dry-run 默认开,
``--write`` 才落盘(改既有工程是破坏性操作,默认只报告 diff)。

命令行:
    python batch_edit.py board.kicad_pcb --rule rules.yaml            # dry-run 报告
    python batch_edit.py board.kicad_pcb --rule rules.yaml --write    # 落盘
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pcb_common import logger, setup_logging  # noqa: E402

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("需要 PyYAML:pip install pyyaml") from exc

_SKIP_HINT = (
    "未安装 kicad-skip。安装(装进 CAD 环境,非 company 生产 venv):\n"
    "  pip install kicad-skip\n"
    "kicad-skip 纯解析 S-expression,无需 KiCad;文档 https://github.com/psychogenic/kicad-skip"
)


class KicadSkipNotFound(RuntimeError):
    """kicad-skip 缺失。fail-loud 异常。"""


def _require_skip():
    try:
        import skip  # noqa: WPS433  (kicad-skip 的导入名是 skip)
    except ImportError as exc:
        raise KicadSkipNotFound(_SKIP_HINT) from exc
    return skip


def load_rules(rules_path: str | Path) -> dict:
    p = Path(rules_path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(p)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"rules.yaml 顶层应为映射:{p}")
    return data


def apply_rules(board_path: str | Path, rules: dict, write: bool = False) -> list[str]:
    """对既有工程应用规则,返回改动报告(每条一行)。write=False 只报告不落盘。"""
    skip = _require_skip()
    board_path = Path(board_path).expanduser()
    if not board_path.is_file():
        raise FileNotFoundError(board_path)

    pcb = skip.Schematic(str(board_path)) if board_path.suffix == ".kicad_sch" \
        else skip.PCB(str(board_path))
    changes: list[str] = []

    # 换封装:遍历 footprints,把 from 命中的换成 to。
    for rule in rules.get("replace_footprint", []) or []:
        src, dst = rule.get("from"), rule.get("to")
        for fp in getattr(pcb, "footprint", []) or []:
            cur = getattr(fp, "lib_id", None) or getattr(fp, "value", None)
            if cur and src and src in str(cur):
                changes.append(f"replace_footprint: {cur} → {dst} (@{getattr(fp,'reference','?')})")
                if write:
                    fp.lib_id = dst

    # 设字段:给 refdes 前缀匹配的元件设字段值。
    for rule in rules.get("set_field", []) or []:
        prefix, field, value = rule.get("refdes_prefix"), rule.get("field"), rule.get("value")
        for sym in getattr(pcb, "symbol", []) or []:
            ref = str(getattr(sym, "reference", "") or "")
            if prefix and ref.startswith(prefix):
                changes.append(f"set_field: {ref}.{field} = {value}")
                if write:
                    sym.setProperty(field, value)

    if write and changes:
        pcb.write(str(board_path))
        logger.info("已落盘 %d 处改动:%s", len(changes), board_path)
    return changes


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batch_edit.py", description="kicad-skip 批量改既有 KiCad 工程(默认 dry-run)"
    )
    p.add_argument("board", help="既有 .kicad_pcb 或 .kicad_sch")
    p.add_argument("--rule", required=True, help="规则 rules.yaml")
    p.add_argument("--write", action="store_true", help="落盘(默认 dry-run 只报告)")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    setup_logging(args.verbose)
    try:
        rules = load_rules(args.rule)
        changes = apply_rules(args.board, rules, write=args.write)
    except KicadSkipNotFound as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 127
    except (FileNotFoundError, ValueError) as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1
    mode = "已落盘" if args.write else "dry-run(加 --write 落盘)"
    if not changes:
        print(f"○ 无匹配改动({mode})")
        return 0
    print(f"✓ {len(changes)} 处改动({mode}):")
    for c in changes:
        print(f"  - {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

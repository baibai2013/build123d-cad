#!/usr/bin/env python3
"""pcb 子技能公共工具(P3-1/P3-2,build123d-cad · pcb 子技能)。

集中三件事,供 new_project / sch_from_skidl / export_fab 等脚本与 tests 复用:

  1. ``which_kicad_cli()`` —— 定位 ``kicad-cli``(KiCad 9.x CLI),沿用 gcode
     ``slice_precheck`` 的工具检测约定:找不到 **fail loud** 给安装提示,
     **不静默降级**(SKILL.md「不做什么」+ 架构原则:降级不静默)。
  2. ``electrical_output_dir()`` —— 按 `08-shared §2.0 标准 output 约定` 拼
     ``output/<task>/electrical/``,所有产物落这里(工程三件套 + fab/)。
  3. ``setup_logging()`` —— 统一日志格式。

刻意只用 ``kicad-cli`` 命令行(稳定),**不碰 KiCad 9.x IPC Python API**
(重构期不稳,见 references/kicad-9-ipc-status.md)。
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger("pcb")

# ── kicad-cli 候选路径(跨平台)──────────────────────────────────────────────
# macOS app bundle / Homebrew / Linux 包管理 / PATH。
_KICAD_CLI_CANDIDATES = [
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",  # macOS 官方 dmg
    "kicad-cli",                                               # PATH(Linux apt / brew link)
    "kicad-cli-9.0",
    "/usr/bin/kicad-cli",
    "/usr/local/bin/kicad-cli",
]

_INSTALL_HINT = (
    "未找到 kicad-cli(KiCad 9.x)。安装:\n"
    "  macOS : brew install --cask kicad   (或官网 dmg https://www.kicad.org/download/)\n"
    "  Linux : sudo apt install kicad       (Ubuntu 24.04+ 含 9.x;旧版加 kicad PPA)\n"
    "装完确认:kicad-cli version  → 应 ≥ 9.0"
)


class KiCadNotFound(RuntimeError):
    """kicad-cli 缺失。fail-loud 异常,携带安装提示(不静默降级)。"""


def which_kicad_cli(required: bool = True) -> str | None:
    """定位 kicad-cli 可执行文件。

    required=True(默认):找不到抛 ``KiCadNotFound`` 带安装提示。
    required=False:找不到 return None(供 tests skip-if-no-kicad 判定)。
    """
    for cand in _KICAD_CLI_CANDIDATES:
        # 绝对路径直接探在不在;裸名走 PATH。
        if cand.startswith("/"):
            if Path(cand).is_file():
                return cand
        else:
            found = shutil.which(cand)
            if found:
                return found
    if required:
        raise KiCadNotFound(_INSTALL_HINT)
    return None


def kicad_available() -> bool:
    """tests / CLI 用:kicad-cli 是否就位(不抛异常)。"""
    return which_kicad_cli(required=False) is not None


def electrical_output_dir(task: str | None, base: str | Path | None = None) -> Path:
    """按 08 §2.0 拼电气产物目录。

    - task 给定 → ``<base>/output/<task>/electrical/``(base 默认当前工作区)
    - task 为空 → ``<base>/electrical/``(就地输出,便于单跑)

    只拼路径不建目录;调用方需要时自行 ``mkdir(parents=True, exist_ok=True)``。
    """
    root = Path(base).expanduser() if base else Path.cwd()
    if task:
        return root / "output" / task / "electrical"
    return root / "electrical"


def setup_logging(verbose: bool = False) -> None:
    """统一日志:默认 WARNING,-v 开 INFO。"""
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

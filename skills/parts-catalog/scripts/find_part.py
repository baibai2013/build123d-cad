#!/usr/bin/env python3
"""parts-catalog 标准件检索路由(P0-5 落地)。

按 `05-制造出工链路 §8.2` 决议实现四级优先级链,逐级回退、本级命中即截断:

    L1 本地 build123d-parts-lib  →  L2 McMaster-Carr  →  L3 step.parts  →  L4 厂商白名单(igus / Murata)

设计要点(对齐 §8.2):
  - **严格顺序、不并发**:某级有结果就 return,不再向下探。
  - **降级不静默**:某级超时 / 4xx5xx / 解析失败写日志后跳下一级;全跑完无果
    return 空候选并标 ``exhausted=True``。
  - **本地零延迟零风险**:L1 直接扫 parts-lib 各类目根 yaml(唯一尺寸源),
    不 import 重型 build123d / OCP,纯文本 + PyYAML,离线可跑。
  - **在线源 P0 默认禁用**:L2/L3/L4 抓取器属 P1(见 §8.5 行动项 A2/A3),
    本文件给出可降级桩——设 ``PARTS_CATALOG_ONLINE=1`` 才尝试,否则记日志跳过。

命令行:
    python find_part.py 608ZZ
    python find_part.py M3 --kind fastener
    python find_part.py sg90 --json
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - 环境缺 PyYAML 时给明确提示
    raise SystemExit("需要 PyYAML:pip install pyyaml") from exc

logger = logging.getLogger("parts_catalog.find_part")

# ── parts-lib 仓库定位(不 import 包,只读 yaml)──────────────────────────────
# 优先级:环境变量 BUILD123D_PARTS_LIB → 已安装包路径 → 默认本机路径。
_DEFAULT_PARTS_LIB = Path("~/work/build123d-parts-lib/build123d_parts_lib").expanduser()

# kind 同义词 → parts-lib 类目目录名(parts/<category>/)。
_KIND_TO_CATEGORY: dict[str, str] = {
    "bearing": "bearings",
    "bearings": "bearings",
    "screw": "fasteners",
    "bolt": "fasteners",
    "nut": "fasteners",
    "washer": "fasteners",
    "fastener": "fasteners",
    "fasteners": "fasteners",
    "insert": "fasteners",
    "servo": "servos",
    "servos": "servos",
    "seal": "seals",
    "oring": "seals",
    "o-ring": "seals",
    "seals": "seals",
    "pin": "pins",
    "pins": "pins",
    "retainer": "retainers",
    "ring": "retainers",
    "circlip": "retainers",
    "retainers": "retainers",
    "gear": "transmission",
    "pulley": "transmission",
    "belt": "transmission",
    "transmission": "transmission",
    "actuator": "actuators",
    "actuators": "actuators",
}

# 一个 yaml 顶层条目是「零件」的判据:value 是 dict 且含下列任一字段。
# (用来跳过 seals/contracts/*.yaml 这类非零件表——其顶层是 slug/part_class/…)
_PART_MARKERS = ("aliases", "factory", "dimensions", "thread", "common_lengths_mm", "body")


@dataclasses.dataclass
class StepCandidate:
    """检索命中候选,对接 mechanical 消费(schema 见 §8.2「返回 schema」)。"""

    src: str                       # local | mcmaster | step.parts | vendor:<...>
    model: str                     # 型号(== yaml key / SKU)
    score: int = 0                 # 匹配置信(100 精确 / 90 去分隔精确 / 70 子串)
    category: str | None = None    # parts-lib 类目(src=local)
    module: str | None = None      # 工厂函数模块路径(src=local)
    fn: str | None = None          # 工厂函数名(src=local)
    args: dict[str, Any] | None = None  # 工厂实例化参数(src=local)
    path: str | None = None        # 本地 STEP cache 路径(src=local,若存在)
    url: str | None = None         # 下载 URL(src≠local)
    source_url: str | None = None  # 原始来源 URL(license 追溯)
    license: str | None = None     # license 声明
    note: str | None = None        # 备注 / 降级原因

    def to_dict(self) -> dict[str, Any]:
        """序列化,丢掉 None / 空值,保持 JSON 干净。"""
        return {k: v for k, v in dataclasses.asdict(self).items() if v not in (None, "", {})}


# ── 工具:归一化 + 匹配打分 ───────────────────────────────────────────────────
def _norm(s: Any) -> str:
    """小写 + 去空白(保留分隔符,区分 M2.5 / M25)。"""
    return re.sub(r"\s+", "", str(s).strip().lower())


def _loose(s: Any) -> str:
    """更宽松:再去掉 - _ . / 等分隔符,用于「608-zz」≈「608zz」匹配。"""
    return re.sub(r"[-_\s./]+", "", str(s).strip().lower())


def _match_score(query: str, names: list[str]) -> int:
    """query 对一组候选名(key + aliases)的最高匹配分;0 表示不匹配。"""
    qn, ql = _norm(query), _loose(query)
    if not ql:
        return 0
    best = 0
    for name in names:
        nn, nl = _norm(name), _loose(name)
        if qn == nn:
            return 100
        if ql == nl:
            best = max(best, 90)
        elif ql in nl or nl in ql:
            best = max(best, 70)
    return best


# ── parts-lib 路径与 yaml 加载 ───────────────────────────────────────────────
def resolve_parts_lib(parts_root: str | Path | None = None) -> Path | None:
    """定位 parts-lib 包目录(含 parts/ 子目录)。找不到 return None。"""
    if parts_root:
        p = Path(parts_root).expanduser()
        return p if (p / "parts").is_dir() else None
    env = os.environ.get("BUILD123D_PARTS_LIB")
    if env:
        p = Path(env).expanduser()
        if (p / "parts").is_dir():
            return p
    try:  # 已 editable 安装时用包自身路径
        import build123d_parts_lib  # noqa: WPS433  (可选依赖)

        p = Path(build123d_parts_lib.__file__).resolve().parent
        if (p / "parts").is_dir():
            return p
    except Exception:  # noqa: BLE001 - 没装包很正常,落到默认路径
        pass
    return _DEFAULT_PARTS_LIB if (_DEFAULT_PARTS_LIB / "parts").is_dir() else None


def _iter_part_entries(parts_dir: Path):
    """遍历 parts/<category>/*.yaml,产出 (category, model_key, spec_dict)。"""
    for yaml_path in sorted(parts_dir.glob("*/*.yaml")):
        category = yaml_path.parent.name
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:  # 解析失败:记日志不中断(降级不静默)
            logger.warning("跳过无法解析的 yaml %s: %s", yaml_path, exc)
            continue
        if not isinstance(data, dict):
            continue
        for key, spec in data.items():
            if isinstance(spec, dict) and any(m in spec for m in _PART_MARKERS):
                yield category, key, spec, yaml_path


# ── L1:本地 build123d-parts-lib ─────────────────────────────────────────────
def search_local(
    query: str, kind: str | None = None, parts_root: str | Path | None = None
) -> list[StepCandidate]:
    """扫 parts-lib 各类目 yaml,按型号 / alias 匹配。结果按 score 降序。"""
    lib = resolve_parts_lib(parts_root)
    if lib is None:
        logger.warning("未找到 build123d-parts-lib(设 BUILD123D_PARTS_LIB 或装 editable),跳过 L1")
        return []

    want_cat = _KIND_TO_CATEGORY.get(_norm(kind)) if kind else None
    hits: list[StepCandidate] = []
    for category, model, spec, yaml_path in _iter_part_entries(lib / "parts"):
        if want_cat and category != want_cat:
            continue
        names = [model, *(spec.get("aliases") or [])]
        score = _match_score(query, names)
        if score <= 0:
            continue
        factory = spec.get("factory") or {}
        source = spec.get("source") or {}
        cache_rel = factory.get("cache")
        cache_abs = None
        if cache_rel:
            cand = (yaml_path.parent / cache_rel).resolve()
            cache_abs = str(cand) if cand.exists() else None
        hits.append(
            StepCandidate(
                src="local",
                model=str(model),
                score=score,
                category=category,
                module=factory.get("module"),
                fn=factory.get("fn"),
                args=factory.get("args"),
                path=cache_abs,
                source_url=source.get("primary"),
                license="MIT/LGPL(parts-lib 自管)",
                note=spec.get("notes"),
            )
        )
    hits.sort(key=lambda c: c.score, reverse=True)
    return hits


# ── L2/L3/L4:在线源(P0 可降级桩,见 §8.5 A2/A3,P1 实装)────────────────────
def _online_enabled() -> bool:
    return os.environ.get("PARTS_CATALOG_ONLINE", "").strip() not in ("", "0", "false", "False")


def search_mcmaster(query: str, kind: str | None = None) -> list[StepCandidate]:
    """L2 McMaster-Carr:需登录 cookie + 速率 ≤1req/s(§8.2.1)。P1 实装(A2)。"""
    if not _online_enabled():
        logger.info("L2 McMaster 跳过:在线源默认禁用(设 PARTS_CATALOG_ONLINE=1 开启;P1 实装)")
        return []
    logger.warning("L2 McMaster 抓取器尚未实现(P1-1 A2),降级到下一级")
    return []


def search_step_parts(query: str, kind: str | None = None) -> list[StepCandidate]:
    """L3 step.parts:公开聚合站,指数 backoff 容忍 5xx(§8.2.1)。P1 实装。"""
    if not _online_enabled():
        logger.info("L3 step.parts 跳过:在线源默认禁用;P1 实装")
        return []
    logger.warning("L3 step.parts 抓取器尚未实现(P1),降级到下一级")
    return []


def search_vendor(query: str, kind: str | None = None) -> list[StepCandidate]:
    """L4 厂商白名单兜底:首版仅 igus / Murata(§8.2.2),其余返回人工提示。P1 实装(A3)。"""
    if not _online_enabled():
        logger.info("L4 厂商兜底跳过:在线源默认禁用;P1 实装(igus/Murata)")
        return []
    logger.warning("L4 厂商抓取器尚未实现(P1-1 A3 igus/Murata),返回人工下载提示")
    return []


# ── 路由主入口 ───────────────────────────────────────────────────────────────
def find_part(
    query: str, kind: str | None = None, parts_root: str | Path | None = None
) -> dict[str, Any]:
    """四级优先级链检索。返回:

    {
      "query": ..., "kind": ...,
      "source": 命中级别 | None,
      "candidates": [StepCandidate.to_dict(), ...],
      "tried": [试探过的级别],
      "exhausted": 全跑完仍无结果时 True,
    }
    """
    result: dict[str, Any] = {
        "query": query,
        "kind": kind,
        "source": None,
        "candidates": [],
        "tried": [],
        "exhausted": False,
    }

    # 严格顺序逐级回退,本级有结果即截断(§8.2 决策)。
    levels = (
        ("local", lambda: search_local(query, kind, parts_root)),
        ("mcmaster", lambda: search_mcmaster(query, kind)),
        ("step.parts", lambda: search_step_parts(query, kind)),
        ("vendor", lambda: search_vendor(query, kind)),
    )
    for name, fn in levels:
        result["tried"].append(name)
        try:
            cands = fn()
        except Exception as exc:  # noqa: BLE001 - 降级不静默:记日志,跳下一级
            logger.warning("级别 %s 检索异常,降级:%s", name, exc)
            continue
        if cands:
            result["source"] = name
            result["candidates"] = [c.to_dict() for c in cands]
            return result

    result["exhausted"] = True
    return result


# ── CLI ──────────────────────────────────────────────────────────────────────
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="find_part.py",
        description="标准件检索:本地 parts-lib → McMaster → step.parts → 厂商白名单",
    )
    p.add_argument("query", help="型号 / 关键词,如 608ZZ、M3、sg90、LM8UU")
    p.add_argument("--kind", default=None, help="类目过滤:bearing/screw/servo/seal/pin/...")
    p.add_argument("--parts-lib", default=None, help="覆盖 parts-lib 仓库路径")
    p.add_argument("--json", action="store_true", help="只输出 JSON(便于程序消费)")
    p.add_argument("-v", "--verbose", action="store_true", help="打开 INFO 级日志")
    return p


def _human_print(res: dict[str, Any]) -> None:
    q, src = res["query"], res["source"]
    cands = res["candidates"]
    if not cands:
        print(f"✗ 「{q}」四级都没命中(tried={'/'.join(res['tried'])},exhausted)")
        print("  → 回退 L4:请人工到厂商官网下载 STEP,或 handoff mechanical 按规格书参数化建模。")
        return
    print(f"✓ 「{q}」命中 {src}({len(cands)} 候选):")
    for i, c in enumerate(cands, 1):
        if c["src"] == "local":
            head = f"  {i}. [{c.get('category')}] {c['model']}  (score={c['score']})"
            print(head)
            if c.get("module"):
                args = c.get("args") or {}
                arg_s = ", ".join(f"{k}={v!r}" for k, v in args.items())
                print(f"     from {c['module']} import {c.get('fn')}")
                print(f"     → {c.get('fn')}({arg_s})")
            if c.get("path"):
                print(f"     cache: {c['path']}")
        else:
            print(f"  {i}. [{c['src']}] {c['model']}  url={c.get('url')}")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    res = find_part(args.query, kind=args.kind, parts_root=args.parts_lib)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        _human_print(res)
    # 命中 → 0;未命中(exhausted)→ 3,便于脚本判定。
    return 0 if res["candidates"] else 3


if __name__ == "__main__":
    sys.exit(main())

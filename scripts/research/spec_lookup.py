#!/usr/bin/env python3
"""
spec_lookup.py — 标准件参数目录查询工具

用法:
    # 按零件 ID 查询（大小写不敏感 + alias 支持）
    python3 spec_lookup.py SG90
    python3 spec_lookup.py m3
    python3 spec_lookup.py 608ZZ

    # 列出某类别全部条目
    python3 spec_lookup.py --list servos

    # 列出所有类别
    python3 spec_lookup.py --list-categories

    # 只返回某字段
    python3 spec_lookup.py SG90 --field body

行为：
    - 命中条目 → 打印 YAML 片段 + source.primary + confidence + last_verified
    - 未命中   → 回落到 sources-catalog.yaml，输出该类别的权威源 + WebSearch prompt
    - last_verified 距今 > 90 天 → 额外打印 [stale] 警告
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

try:
    import yaml  # PyYAML
except ImportError:
    sys.stderr.write(
        "缺少依赖 PyYAML。请先安装：python3 -m pip install pyyaml\n"
    )
    sys.exit(2)


# 数据目录相对 skill 根的定位：scripts/research/spec_lookup.py → ../../references/data-sources
SKILL_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = SKILL_ROOT / "references" / "data-sources"
CATALOG_FILE = DATA_DIR / "sources-catalog.yaml"
STALE_DAYS = 90


def load_all_entries() -> tuple[dict, dict]:
    """返回 (entries_by_id, raw_files_by_category)。
    entries_by_id: {normalized_id: entry_dict_plus_meta}
    """
    entries: dict[str, dict] = {}
    files_by_category: dict[str, list[Path]] = {}

    for yaml_path in sorted(DATA_DIR.glob("*.yaml")):
        if yaml_path.name == CATALOG_FILE.name:
            continue
        try:
            loaded = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            sys.stderr.write(f"[warn] 解析失败 {yaml_path.name}: {e}\n")
            continue

        for part_id, body in loaded.items():
            if not isinstance(body, dict):
                continue
            category = body.get("category", yaml_path.stem)
            files_by_category.setdefault(category, []).append(yaml_path)

            ids = {part_id.lower()}
            for alias in body.get("aliases", []) or []:
                ids.add(str(alias).lower())

            for norm_id in ids:
                entries[norm_id] = {
                    "id": part_id,
                    "file": yaml_path,
                    "category": category,
                    "data": body,
                }

    return entries, files_by_category


def load_catalog() -> dict:
    if not CATALOG_FILE.exists():
        return {}
    try:
        return yaml.safe_load(CATALOG_FILE.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        sys.stderr.write(f"[warn] 解析失败 {CATALOG_FILE.name}: {e}\n")
        return {}


def stale_warning(last_verified) -> str | None:
    if not last_verified:
        return None
    try:
        if isinstance(last_verified, _dt.date):
            lv = last_verified
        else:
            lv = _dt.date.fromisoformat(str(last_verified))
    except ValueError:
        return None
    age = (_dt.date.today() - lv).days
    if age > STALE_DAYS:
        return f"[stale] last_verified={lv} ({age} 天前，> {STALE_DAYS} 天阈值)。建议本次重新核实。"
    return None


def print_hit(entry: dict, field_filter: str | None = None) -> None:
    data = entry["data"]
    src = data.get("source", {}) or {}

    print(f"[spec-hit] {entry['file'].relative_to(SKILL_ROOT)}:{entry['id']}")
    print(f"  category:      {entry['category']}")
    print(f"  confidence:    {src.get('confidence', 'N/A')} / 5")
    print(f"  primary URL:   {src.get('primary', '(未提供)')}")
    ds = src.get("datasheet")
    if ds:
        print(f"  datasheet:     {ds}")
    print(f"  last_verified: {src.get('last_verified', '(未标注)')}")
    stale = stale_warning(src.get("last_verified"))
    if stale:
        print(f"  ⚠ {stale}")
    print()

    if field_filter:
        val = data.get(field_filter)
        if val is None:
            print(f"(字段 '{field_filter}' 不存在。可用字段: {sorted(data.keys())})")
            return
        print(f"## {field_filter}")
        print(yaml.safe_dump({field_filter: val}, allow_unicode=True, sort_keys=False, indent=2))
    else:
        print("## 全部参数")
        print(yaml.safe_dump({entry["id"]: data}, allow_unicode=True, sort_keys=False, indent=2))


def print_miss(query: str, entries: dict, catalog: dict) -> None:
    print(f"[spec-miss] 未找到 '{query}'")
    print()
    print(f"已收录条目: {sorted({e['id'] for e in entries.values()})}")
    print()
    print("## 权威源建议（来自 sources-catalog.yaml）")
    print()
    if not catalog:
        print("(sources-catalog.yaml 缺失或为空)")
        return
    for category, body in catalog.items():
        if not isinstance(body, dict):
            continue
        print(f"### {category}")
        desc = body.get("description")
        if desc:
            print(f"  用途：{desc}")
        for s in body.get("priority_sources", []) or []:
            print(f"  - {s.get('name', '?')}  {s.get('url', '')}")
        prompts = body.get("websearch_prompts") or ([body.get("websearch_prompt")] if body.get("websearch_prompt") else [])
        if prompts:
            print("  WebSearch prompt 示例:")
            for p in prompts:
                print(f"    • {p}")
        print()


def list_categories(files_by_category: dict) -> None:
    print("## 已有类别")
    for cat in sorted(files_by_category):
        files = ", ".join(sorted({f.name for f in files_by_category[cat]}))
        print(f"  {cat:<20} → {files}")


def list_entries_in_category(category: str, entries: dict) -> None:
    ids = sorted({e["id"] for e in entries.values() if e["category"] == category})
    if not ids:
        print(f"[empty] 类别 '{category}' 下无条目。")
        return
    print(f"## {category} 类别条目（{len(ids)} 项）")
    for pid in ids:
        first_hit = next(e for e in entries.values() if e["id"] == pid)
        src = first_hit["data"].get("source", {}) or {}
        print(f"  {pid:<16} confidence={src.get('confidence', '?')}/5  {first_hit['file'].name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="标准件参数目录查询（SG90 / M3 / 608ZZ 等）"
    )
    parser.add_argument("query", nargs="?", help="零件 ID 或 alias")
    parser.add_argument("--field", help="只返回某个字段（如 body / mount / source）")
    parser.add_argument("--list", metavar="CATEGORY", help="列出某类别全部条目")
    parser.add_argument("--list-categories", action="store_true", help="列出所有类别")
    args = parser.parse_args(argv)

    if not DATA_DIR.exists():
        sys.stderr.write(f"[error] 数据目录不存在：{DATA_DIR}\n")
        return 2

    entries, files_by_category = load_all_entries()
    catalog = load_catalog()

    if args.list_categories:
        list_categories(files_by_category)
        return 0

    if args.list:
        list_entries_in_category(args.list, entries)
        return 0

    if not args.query:
        parser.print_help()
        return 1

    q = args.query.strip().lower()
    entry = entries.get(q)
    if entry:
        print_hit(entry, field_filter=args.field)
        return 0

    print_miss(args.query, entries, catalog)
    return 3  # 返回码 3 = 未命中（便于调用方判断）


if __name__ == "__main__":
    sys.exit(main())

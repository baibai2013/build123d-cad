#!/usr/bin/env python3
"""
code_lookup.py — 代码源目录查询工具

用途：建模前按领域查 code-sources → 得 repos + WebSearch prompts，借鉴社区代码。

用法:
    # 按领域查
    python3 code_lookup.py gears
    python3 code_lookup.py surfaces

    # 按关键词跨领域模糊搜
    python3 code_lookup.py "involute curve"

    # 仅输出 WebSearch prompt（供 AI 直接粘贴）
    python3 code_lookup.py gears --websearch

    # 管理
    python3 code_lookup.py --list-domains
    python3 code_lookup.py --cache-status
    python3 code_lookup.py gears --fresh       # 忽略 cache 强制重搜

返回码:
    0 = 命中领域 / 命中 cache
    3 = 未命中任何领域（回落到模糊搜索建议）
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("缺少依赖 PyYAML：python3 -m pip install pyyaml\n")
    sys.exit(2)


# 路径：scripts/research/code_lookup.py → ../../references/code-sources
SKILL_ROOT = Path(__file__).resolve().parents[2]
CATALOG = SKILL_ROOT / "references" / "code-sources" / "catalog.yaml"
CACHE_DIR = SKILL_ROOT / "experience" / "code-patterns" / "_cache"
CACHE_TTL_DAYS = 7


def load_catalog() -> dict:
    if not CATALOG.exists():
        sys.stderr.write(f"[error] catalog.yaml 不存在：{CATALOG}\n")
        sys.exit(2)
    try:
        return yaml.safe_load(CATALOG.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        sys.stderr.write(f"[error] catalog.yaml 解析失败：{e}\n")
        sys.exit(2)


def slugify(text: str) -> str:
    """把查询关键词转 safe filename。"""
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    s = re.sub(r"[\s_-]+", "-", s)
    return s or "query"


def cache_path(domain: str, keyword: str = "default") -> Path:
    return CACHE_DIR / domain / f"{slugify(keyword)}.md"


def cache_status(path: Path) -> tuple[str, int | None]:
    """返回 ('hit'|'stale'|'miss', age_days | None)。"""
    if not path.exists():
        return "miss", None
    try:
        content = path.read_text(encoding="utf-8")
        m = re.search(r"^last_searched:\s*([\d-]+)", content, re.MULTILINE)
        if not m:
            return "miss", None
        last = _dt.date.fromisoformat(m.group(1))
        age = (_dt.date.today() - last).days
        return ("hit" if age <= CACHE_TTL_DAYS else "stale", age)
    except (ValueError, OSError):
        return "miss", None


def print_domain(domain_name: str, domain: dict, catalog: dict, keyword: str, websearch_only: bool, fresh: bool) -> int:
    # 合并 core_repos(通用)+ domain_repos(P1-3 加,robotics/fixtures/simulation 专属)
    repos = {r["name"]: r for r in catalog.get("core_repos", []) or []}
    for r in catalog.get("domain_repos", []) or []:
        repos.setdefault(r["name"], r)

    cpath = cache_path(domain_name, keyword)
    status, age = cache_status(cpath)

    if websearch_only:
        # 仅输出 prompts 一行一个，方便粘贴
        for p in domain.get("websearch_prompts", []) or []:
            print(p)
        return 0

    # 标题
    print(f"# 代码库巡查：{domain_name}")
    desc = domain.get("description", "")
    if desc:
        print(f"\n{desc}")
    print()

    # Cache 状态
    if not fresh and status == "hit":
        print(f"## 📦 Cache 命中（{age} 天前搜过）")
        print(f"  路径：{cpath.relative_to(SKILL_ROOT)}")
        print(f"  用 --fresh 强制刷新；或直接复用 cache 里的摘要")
        print()
        print("---")
        print(cpath.read_text(encoding="utf-8"))
        return 0

    if status == "stale":
        print(f"## ⚠ Cache 过期（{age} 天 > {CACHE_TTL_DAYS} 天阈值），建议重搜\n")
    elif status == "miss":
        print(f"## ❄ Cache 未命中 → AI 应执行下方 WebSearch prompts，结果写回：\n  {cpath.relative_to(SKILL_ROOT)}\n")

    # 主力 repos
    print("## 主力 repos（优先翻阅）")
    for repo_name in domain.get("primary_repos", []) or []:
        repo = repos.get(repo_name)
        if repo:
            ls = repo.get("license_status")
            ls_tag = f" [{ls}]" if ls and ls != "verified" else ""
            print(f"  - **{repo['name']}**  (License: {repo['license']}{ls_tag})")
            print(f"    {repo['url']}")
            tc = repo.get("translate_cost", "n/a")
            conf = repo.get("confidence", "?")
            print(f"    翻译成本：{tc}  |  confidence={conf}/5")
            if repo.get("notes"):
                first_line = repo["notes"].strip().split("\n")[0]
                print(f"    {first_line}")
            if ls == "pending":
                print("    ⚠️ license_status=pending,借鉴前必须 cad-scraper 复核(红线 #5)")
        else:
            print(f"  - {repo_name}  (未在 catalog 注册,请补)")
    print()

    # Fallback
    fallback = domain.get("fallback_repos", []) or []
    if fallback:
        print("## Fallback（build123d 无对应实现时参考）")
        for repo_name in fallback:
            repo = repos.get(repo_name)
            if repo:
                ls = repo.get("license_status")
                ls_tag = f" [{ls}]" if ls and ls != "verified" else ""
                tc = repo.get("translate_cost", "n/a")
                print(f"  - {repo['name']}  (License: {repo['license']}{ls_tag}, translate_cost={tc})")
            else:
                print(f"  - {repo_name}  (外部来源，未收录 License 信息——借鉴前自查)")
        print()

    # WebSearch prompts
    print("## WebSearch prompts（执行后把摘要写入 cache）")
    for p in domain.get("websearch_prompts", []) or []:
        print(f"  • {p}")
    print()

    # Local doc
    doc = domain.get("local_doc")
    if doc:
        doc_path = SKILL_ROOT / doc if not doc.startswith("/") else Path(doc)
        if doc_path.exists():
            print(f"## 本地领域文档")
            print(f"  → {doc}  (已建，含核心技巧 + 代码片段)")
        else:
            print(f"## 本地领域文档")
            print(f"  → {doc}  (⚠ 文件不存在，可建)")
    else:
        print(f"## 本地领域文档")
        print(f"  → (本领域未建 .md 文件，搜到精华可新建)")
    print()

    # License 提醒
    policy = catalog.get("license_policy", {})
    print("## 🛡 License 纪律（借鉴前必查）")
    print(f"  🟢 安全：{', '.join(policy.get('safe', {}).get('codes', []))}")
    print(f"  🟡 谨慎：{', '.join(policy.get('caution', {}).get('codes', []))}（GPL 传染性，默认禁用）")
    print(f"  🔴 禁用：未标 License / 商业 / 自定义")
    print()

    return 0


def print_keyword_search(keyword: str, catalog: dict) -> int:
    """模糊搜索：扫所有 domain 的 description、name，返回最可能的 2 个。"""
    kw = keyword.lower()
    domains = catalog.get("domains", {}) or {}
    matches = []
    for name, body in domains.items():
        score = 0
        if kw in name.lower():
            score += 10
        desc = (body.get("description") or "").lower()
        if kw in desc:
            score += 5
        # 扫 websearch prompts
        for p in body.get("websearch_prompts", []) or []:
            if kw in p.lower():
                score += 2
        if score > 0:
            matches.append((score, name, body))
    matches.sort(key=lambda x: -x[0])

    if not matches:
        print(f"[miss] 关键词 '{keyword}' 未命中任何领域。")
        print(f"已有领域：{', '.join(domains.keys())}")
        print(f"建议：--list-domains 查看全部，或直接在 {CATALOG.relative_to(SKILL_ROOT)} 新增领域")
        return 3

    print(f"# 关键词搜索：'{keyword}'\n")
    print(f"匹配到 {len(matches)} 个领域（按相关度排序）：\n")
    for score, name, body in matches[:2]:
        print(f"## {name}  (相关度 {score})")
        print(f"  {body.get('description', '')}")
        print(f"  详情：python3 code_lookup.py {name}")
        print()
    return 0


def list_domains(catalog: dict) -> None:
    domains = catalog.get("domains", {}) or {}
    print(f"# 已登记领域（{len(domains)} 个）\n")
    for name, body in domains.items():
        doc = body.get("local_doc") or "(未建 .md)"
        print(f"  {name:<14} → {body.get('description', '')}")
        print(f"  {'':<14}   local_doc: {doc}")
    print()


def print_cache_status(catalog: dict) -> None:
    if not CACHE_DIR.exists():
        print(f"# Cache 目录不存在：{CACHE_DIR.relative_to(SKILL_ROOT)}")
        print(f"(首次查询时会自动创建)")
        return
    items = sorted(CACHE_DIR.rglob("*.md"))
    print(f"# Cache 状态（{len(items)} 条条目）\n")
    if not items:
        print("  (空)")
        return
    for f in items:
        rel = f.relative_to(CACHE_DIR)
        try:
            content = f.read_text(encoding="utf-8")
            m = re.search(r"^last_searched:\s*([\d-]+)", content, re.MULTILINE)
            if m:
                last = _dt.date.fromisoformat(m.group(1))
                age = (_dt.date.today() - last).days
                tag = "✓" if age <= CACHE_TTL_DAYS else "⚠ STALE"
                print(f"  {tag}  {rel}  (age={age}d)")
            else:
                print(f"  ?  {rel}  (无 last_searched 字段)")
        except Exception as e:
            print(f"  !  {rel}  (读失败：{e})")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="代码源目录查询：按领域/关键词拉 repos + WebSearch prompts（建模前先巡查社区）"
    )
    parser.add_argument("query", nargs="?", help="领域名（gears/surfaces/...）或模糊关键词")
    parser.add_argument("--websearch", action="store_true",
                        help="仅输出 WebSearch prompts 原文（可 copy/paste）")
    parser.add_argument("--fresh", action="store_true",
                        help="忽略 cache，强制视为 miss（输出 fresh prompts）")
    parser.add_argument("--list-domains", action="store_true",
                        help="列出所有领域")
    parser.add_argument("--cache-status", action="store_true",
                        help="查看 cache 目录状态（含过期标记）")
    args = parser.parse_args(argv)

    catalog = load_catalog()

    if args.list_domains:
        list_domains(catalog)
        return 0

    if args.cache_status:
        print_cache_status(catalog)
        return 0

    if not args.query:
        parser.print_help()
        return 1

    q = args.query.strip().lower()
    domains = catalog.get("domains", {}) or {}

    # 精确领域名命中
    if q in domains:
        return print_domain(q, domains[q], catalog, keyword=q,
                            websearch_only=args.websearch, fresh=args.fresh)

    # 否则模糊搜
    return print_keyword_search(args.query, catalog)


if __name__ == "__main__":
    sys.exit(main())

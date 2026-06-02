# scripts/validate/* 脚本最小可加载性测试
#
# 不真跑(避免依赖 build123d / OCC 大件),只验证语法 + import 顶层 OK。
# 真正的功能测试 P0-9 benchmarks 与 P1 agent-eval 承接。
import ast
from pathlib import Path

import pytest

VALIDATE_SCRIPTS = [
    "validate_part.py",
    "assembly_check.py",
    "contract_verify.py",
    "visual_compare.py",
]


@pytest.mark.parametrize("script", VALIDATE_SCRIPTS)
def test_validate_script_parses(mechanical_root, script):
    path = mechanical_root / "scripts" / "validate" / script
    assert path.is_file(), f"validate 脚本缺失: {path}"
    src = path.read_text(encoding="utf-8")
    try:
        ast.parse(src)
    except SyntaxError as exc:
        pytest.fail(f"{script} 语法错误: {exc}")


def test_assets_examples_present(mechanical_root):
    """13 个示例零件是否完整迁过来"""
    parts_dir = mechanical_root / "assets" / "parts"
    assert parts_dir.is_dir(), f"assets/parts/ 缺失: {parts_dir}"
    files = sorted(parts_dir.glob("*.py"))
    assert len(files) >= 13, f"assets/parts/ 示例零件不足 13 个,实有 {len(files)}"


def test_legacy_skill_archived(mechanical_root):
    """legacy SKILL.md 是否归档以备查询"""
    legacy = mechanical_root / "SKILL.legacy.md"
    assert legacy.is_file(), "SKILL.legacy.md 归档不存在"
    assert legacy.stat().st_size > 50_000, "legacy 文件异常小,可能没归档完整"


# ---- P1-2 / P1-3 验收 ----

import yaml as _yaml

P1_DATA_COUNTS = {"motors": 11, "connectors": 14, "mcu_boards": 8}
P1_CODE_DOCS = ["robotics.md", "fixtures.md", "simulation.md"]


@pytest.mark.parametrize("kind,min_count", P1_DATA_COUNTS.items())
def test_p1_2_data_sources_schema(mechanical_root, kind, min_count):
    """P1-2:三类 data-sources yaml 条目数 + 必填字段"""
    path = mechanical_root / "references" / "data-sources" / f"{kind}.yaml"
    assert path.is_file(), f"{kind}.yaml 不存在"
    data = _yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data.get("schema_version") == 1, f"{kind}.yaml 缺 schema_version: 1"
    assert data.get("kind"), f"{kind}.yaml 缺 kind 顶层字段"
    entries = data.get("entries") or []
    assert len(entries) >= min_count, f"{kind}.yaml 条目 {len(entries)} < {min_count}"
    for it in entries:
        assert "id" in it, f"{kind}/? 缺 id"
        assert "keywords" in it, f"{kind}/{it.get('id')} 缺 keywords"
        src = it.get("source") or {}
        assert "license" in src, f"{kind}/{it['id']} 缺 source.license"
        assert "datasheet_url" in src, f"{kind}/{it['id']} 缺 source.datasheet_url"
        assert "retrieved_at" in src, f"{kind}/{it['id']} 缺 source.retrieved_at"


@pytest.mark.parametrize("doc", P1_CODE_DOCS)
def test_p1_3_code_sources_docs(mechanical_root, doc):
    """P1-3:三篇 code-sources .md 存在 + 含 license 列"""
    path = mechanical_root / "references" / "code-sources" / doc
    assert path.is_file(), f"{doc} 不存在"
    text = path.read_text(encoding="utf-8")
    assert "license" in text.lower(), f"{doc} 缺 license 矩阵"
    assert "license_status" in text, f"{doc} 缺 license_status 字段(红线 #5)"
    assert "retrieved_at" in text, f"{doc} 缺 retrieved_at"


def test_p1_3_catalog_domain_repos(mechanical_root):
    """P1-3:catalog.yaml 含 robotics/fixtures/simulation 三域 domain_repos"""
    catalog_path = mechanical_root / "references" / "code-sources" / "catalog.yaml"
    catalog = _yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    domains = catalog.get("domains") or {}
    for d in ("robotics", "fixtures", "simulation"):
        assert d in domains, f"catalog domains 缺 {d}"
        assert domains[d].get("local_doc"), f"catalog {d}.local_doc 未填"

    domain_repos = catalog.get("domain_repos") or []
    by_domain = {}
    for r in domain_repos:
        by_domain.setdefault(r["domain"], []).append(r)
    assert len(by_domain.get("robotics", [])) >= 5, "robotics domain_repos < 5"
    assert len(by_domain.get("simulation", [])) >= 5, "simulation domain_repos < 5"
    # 每条必填 license + license_status + retrieved_at
    for r in domain_repos:
        for f in ("license", "license_status", "retrieved_at"):
            assert f in r, f"domain_repos[{r['name']}] 缺 {f}"


def test_p1_3_readme_red_lines(mechanical_root):
    """P1-3:README 是否落了 5 条借鉴红线"""
    readme = (mechanical_root / "references" / "code-sources" / "README.md").read_text(encoding="utf-8")
    assert "5 条借鉴红线" in readme, "README 缺 5 条借鉴红线段"
    # 5 条要点(关键字粗略匹配)
    for kw in ["保留原文件头 license", "GPL/AGPL", "CC-BY-SA", "proprietary", "license_status: pending"]:
        assert kw in readme, f"README 红线缺关键词: {kw}"

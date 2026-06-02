"""find_part.py 检索路由测试(P0-5)。

全部离线可跑:
  - 路由 / schema / 在线源默认禁用 / 未命中 exhausted —— 无外部依赖,标 smoke。
  - 本地命中类(608ZZ / M3 / SG90 / alias / kind 过滤)—— 依赖本机 build123d-parts-lib
    仓库,缺仓库时自动 skip(不当失败)。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# scripts/ 非包,直接挂到 sys.path 再 import(配合 pytest --import-mode=importlib)。
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import find_part  # noqa: E402


@pytest.fixture(scope="session")
def has_parts_lib() -> bool:
    return find_part.resolve_parts_lib() is not None


@pytest.fixture()
def require_parts_lib(has_parts_lib):
    if not has_parts_lib:
        pytest.skip("本机未找到 build123d-parts-lib 仓库,跳过本地命中类测试")


# ── 不依赖仓库:路由 / schema / 在线禁用 ─────────────────────────────────────
@pytest.mark.smoke
def test_module_api_present():
    for attr in ("find_part", "search_local", "StepCandidate", "resolve_parts_lib"):
        assert hasattr(find_part, attr), f"find_part 缺 {attr}"


@pytest.mark.smoke
def test_candidate_schema_drops_empty():
    c = find_part.StepCandidate(src="local", model="608ZZ", score=100, module="m", fn="f")
    d = c.to_dict()
    assert d["src"] == "local" and d["model"] == "608ZZ" and d["score"] == 100
    # None / 空字段不应出现在序列化结果里。
    assert "url" not in d and "path" not in d and "note" not in d


@pytest.mark.smoke
def test_online_sources_disabled_by_default(monkeypatch):
    """PARTS_CATALOG_ONLINE 未设时,L2/L3/L4 一律返回空(P0 不抓网)。"""
    monkeypatch.delenv("PARTS_CATALOG_ONLINE", raising=False)
    assert find_part.search_mcmaster("608ZZ") == []
    assert find_part.search_step_parts("608ZZ") == []
    assert find_part.search_vendor("608ZZ") == []


@pytest.mark.smoke
def test_miss_is_exhausted():
    """四级都没命中时 candidates 空、exhausted=True、四级都试过。"""
    res = find_part.find_part("definitely_not_a_real_part_zzz_999")
    assert res["candidates"] == []
    assert res["exhausted"] is True
    assert res["source"] is None
    assert res["tried"] == ["local", "mcmaster", "step.parts", "vendor"]


def test_match_score_levels():
    assert find_part._match_score("608ZZ", ["608ZZ"]) == 100        # 精确
    assert find_part._match_score("608-zz", ["608ZZ"]) == 90        # 去分隔精确
    assert find_part._match_score("608", ["608ZZ"]) == 70           # 子串
    assert find_part._match_score("xyz", ["608ZZ"]) == 0            # 不匹配


# ── 依赖仓库:本地命中 ───────────────────────────────────────────────────────
def test_local_hit_bearing_608(require_parts_lib):
    res = find_part.find_part("608ZZ")
    assert res["source"] == "local"
    assert res["candidates"], "608ZZ 应在 parts-lib 命中"
    top = res["candidates"][0]
    assert top["src"] == "local"
    assert top["model"] == "608ZZ"
    assert top["score"] == 100
    assert top["category"] == "bearings"
    assert top["module"].endswith("ball_bearing")
    assert top["fn"] == "make_ball_bearing"


def test_local_alias_loose_match(require_parts_lib):
    """带分隔符的写法也能命中(608-zz → 608ZZ)。"""
    hits = find_part.search_local("608-zz")
    models = [h.model for h in hits]
    assert "608ZZ" in models
    assert hits[0].score >= 90


def test_local_servo_sg90(require_parts_lib):
    res = find_part.find_part("sg90")
    assert res["source"] == "local"
    top = res["candidates"][0]
    assert top["model"] == "SG90"
    assert top["fn"] == "make_sg90"


def test_kind_filter_restricts_category(require_parts_lib):
    """kind=fastener 时只返回 fasteners 类目候选。"""
    res = find_part.find_part("M3", kind="fastener")
    assert res["source"] == "local"
    assert res["candidates"]
    assert all(c["category"] == "fasteners" for c in res["candidates"])


def test_kind_mismatch_falls_through_to_exhausted(require_parts_lib):
    """M3 限定到 bearing 类目本地无果,在线禁用 → exhausted。"""
    res = find_part.find_part("M3", kind="bearing")
    assert res["candidates"] == []
    assert res["exhausted"] is True


def test_results_sorted_by_score(require_parts_lib):
    hits = find_part.search_local("M3", kind="fastener")
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == 100  # M3_ISO4762 精确命中排第一


# ── CLI 入口 ─────────────────────────────────────────────────────────────────
def test_cli_hit_returns_zero(require_parts_lib, capsys):
    code = find_part.main(["608ZZ", "--json"])
    assert code == 0
    out = capsys.readouterr().out
    assert "608ZZ" in out


def test_cli_miss_returns_three(capsys):
    code = find_part.main(["definitely_not_a_real_part_zzz_999"])
    assert code == 3

"""srdf 子技能 smoke — 骨架 + references 命中 + fixture SRDF schema 校验。"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


@pytest.mark.smoke
def test_skill_md_exists(subskill_root: Path):
    md = subskill_root / "SKILL.md"
    assert md.exists(), f"{md} 缺失"
    assert md.stat().st_size > 0, f"{md} 为空"


@pytest.mark.smoke
def test_readme_exists(subskill_root: Path):
    readme = subskill_root / "README.md"
    assert readme.exists(), f"{readme} 缺失"


@pytest.mark.smoke
def test_subskill_dirs_present(subskill_root: Path):
    """references/ scripts/ tests/ 三个标准目录就位。"""
    for d in ("references", "scripts", "tests"):
        assert (subskill_root / d).is_dir(), f"{subskill_root}/{d} 缺失"


@pytest.mark.smoke
def test_skill_md_size_under_250(subskill_root: Path):
    """子技能 SKILL.md ≤ 250 行(08 §7 加新子技能质量门)。"""
    md = subskill_root / "SKILL.md"
    lines = md.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 250, f"SKILL.md {len(lines)} 行 > 上限 250"


@pytest.mark.smoke
def test_required_references_present(subskill_root: Path):
    """SKILL.md 引用的两份 references 必须落地。"""
    refs = subskill_root / "references"
    for name in ("srdf-spec-cheatsheet.md", "planning-groups-quadruped.md"):
        f = refs / name
        assert f.exists() and f.stat().st_size > 0, f"{f} 缺失或为空"


@pytest.mark.smoke
def test_skill_md_has_frontmatter(subskill_root: Path):
    """SKILL.md 必须有 YAML frontmatter 包含 name/description。"""
    text = (subskill_root / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), "SKILL.md 缺 frontmatter"
    assert "\nname: srdf\n" in text, "frontmatter 缺 name: srdf"
    assert "description:" in text.split("---\n", 2)[1], "frontmatter 缺 description"


@pytest.mark.smoke
def test_quadruped_fixture_is_valid_srdf(subskill_root: Path):
    """tests/fixtures/quadruped_min.srdf 必须 well-formed 且符合 SRDF 必备结构。"""
    p = subskill_root / "tests" / "fixtures" / "quadruped_min.srdf"
    assert p.exists(), f"{p} 缺失"

    tree = ET.parse(p)
    root = tree.getroot()
    assert root.tag == "robot", f"root tag 应为 <robot>,实际 <{root.tag}>"
    assert root.get("name"), "robot 缺 name 属性"

    groups = {g.get("name") for g in root.findall("group")}
    required_groups = {
        "front_left_leg", "front_right_leg",
        "rear_left_leg", "rear_right_leg",
        "all_legs",
    }
    assert required_groups <= groups, f"缺规划组: {required_groups - groups}"

    states = {s.get("name"): s.get("group") for s in root.findall("group_state")}
    assert {"home", "stand", "sit"} <= set(states), "命名虚位姿至少要含 home/stand/sit"
    for state_name, grp in states.items():
        assert grp in groups, f"group_state {state_name!r} 引用不存在的 group {grp!r}"

    vj = root.findall("virtual_joint")
    assert len(vj) == 1, "四足应有恰好 1 个 virtual_joint"
    assert vj[0].get("type") == "floating", "移动底座 virtual_joint 必须是 floating"

    # 每个 group_state 必须列 12 个关节(12-DoF 四足)
    for s in root.findall("group_state"):
        js = s.findall("joint")
        assert len(js) == 12, f"group_state {s.get('name')!r} 应有 12 个 joint,实际 {len(js)}"

    # Adjacent disable_collisions 至少 12 对(base→4 hip + 4 腿×3)
    adj = [d for d in root.findall("disable_collisions") if d.get("reason") == "Adjacent"]
    assert len(adj) >= 12, f"Adjacent disable_collisions 应 ≥12 对,实际 {len(adj)}"

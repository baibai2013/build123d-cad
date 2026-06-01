# Playbook 路由完整性回归测试
#
# 跑通条件:5 Playbook 文件就位 + 所有静态 references 引用文件存在。
# 不验证 Playbook 内容正确性(那是 SKILL.legacy.md 时代的事),只验证迁移后引用零破坏。
import re
from pathlib import Path

import pytest

PLAYBOOKS = [
    "single-part-playbook.md",
    "multi-part-playbook.md",
    "reference-product-playbook.md",
    "standard-parts-playbook.md",
]

# slug 占位符 — 这是 Playbook 在用户 cwd 下的工作产出路径,不是 SKILL 内引用
SLUG_PLACEHOLDER = re.compile(r"<slug>|\$SLUG|\$slug")
# 静态 references 引用(以 ../references/<目录>/<文件>.<扩展> 开头)
REF_PATTERN = re.compile(
    r"\.\./references/([a-z][a-z0-9_-]*/[a-z0-9_./-]+\.(?:md|yaml|yml|py|json))"
)
# 同子技能 protocols 互引(../protocols/xxx.md)
PROTO_PATTERN = re.compile(r"\.\./protocols/([a-z][a-z0-9_-]*\.md)")
# SKILL.md 自身位于 mechanical/,引用 references/ 与 protocols/ 是同层
SKILL_REF_PATTERN = re.compile(
    r"(?:^|[^/<\$])(references/[a-z][a-z0-9_-]*/[a-z0-9_./-]+\.(?:md|yaml|yml|py|json))"
)
SKILL_PROTO_PATTERN = re.compile(
    r"(?:^|[^/])(protocols/[a-z][a-z0-9_-]*\.md)"
)


def _strip_slug(line: str) -> str:
    """slug 占位符路径用真实 slug 替换,避免被静态 grep 命中"""
    return SLUG_PLACEHOLDER.sub("EXAMPLE-SLUG", line)


def test_playbook_files_exist(mechanical_root):
    proto_dir = mechanical_root / "protocols"
    assert proto_dir.is_dir(), f"protocols/ 目录不存在: {proto_dir}"
    missing = [p for p in PLAYBOOKS if not (proto_dir / p).is_file()]
    assert not missing, f"Playbook 文件缺失: {missing}"


@pytest.mark.parametrize("playbook", PLAYBOOKS)
def test_playbook_references_resolve(mechanical_root, playbook):
    proto_dir = mechanical_root / "protocols"
    text = (proto_dir / playbook).read_text(encoding="utf-8")
    text_no_slug = "\n".join(_strip_slug(l) for l in text.splitlines())

    # ../references/...
    refs = sorted(set(REF_PATTERN.findall(text_no_slug)))
    missing_refs = [r for r in refs if not (mechanical_root / "references" / r).is_file()]
    assert not missing_refs, (
        f"{playbook} 中 ../references/ 引用文件不存在: {missing_refs}"
    )

    # ../protocols/...
    protos = sorted(set(PROTO_PATTERN.findall(text_no_slug)))
    missing_protos = [p for p in protos if not (proto_dir / p).is_file()]
    assert not missing_protos, (
        f"{playbook} 中 ../protocols/ 引用文件不存在: {missing_protos}"
    )


def test_skill_md_references_resolve(mechanical_root):
    skill_md = (mechanical_root / "SKILL.md").read_text(encoding="utf-8")

    refs = sorted(set(m for m in SKILL_REF_PATTERN.findall(skill_md)))
    missing_refs = [r for r in refs if not (mechanical_root / r).is_file()]
    assert not missing_refs, f"SKILL.md 中 references/ 引用文件不存在: {missing_refs}"

    protos = sorted(set(SKILL_PROTO_PATTERN.findall(skill_md)))
    missing_protos = [p for p in protos if not (mechanical_root / p).is_file()]
    assert not missing_protos, f"SKILL.md 中 protocols/ 引用文件不存在: {missing_protos}"


def test_skill_md_size_within_budget(mechanical_root):
    """子级 SKILL.md ≤ 380 行(02 §5 验收)"""
    skill_md = mechanical_root / "SKILL.md"
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 380, f"SKILL.md 超出 380 行预算: {len(lines)}"


def test_no_legacy_protocols_path(mechanical_root):
    """protocols 不应该再出现旧路径 references/protocols/ 自引"""
    proto_dir = mechanical_root / "protocols"
    legacy = []
    for p in PLAYBOOKS:
        text = (proto_dir / p).read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if "references/protocols/" in line:
                legacy.append(f"{p}:{i}: {line.strip()[:120]}")
    assert not legacy, f"残留旧路径 references/protocols/: {legacy}"

"""pcb 子技能(tscircuit)smoke — 结构骨架 + dfm_check 本地单测(无需 tsci/key)。"""
from __future__ import annotations

from pathlib import Path

import pytest

EXPECTED_SCRIPTS = ["new_board.sh", "check_all.sh", "export_fab.sh",
                    "dfm_check.py", "jlc_order.py", "bom_price.py", "_tsci_env.sh"]
EXPECTED_REFS = ["cli-cheatsheet.md", "syntax-elements.md", "workflow-end-to-end.md",
                 "jlcpcb-mcp.md", "preview-3d.md"]


@pytest.mark.smoke
def test_skill_md_exists(subskill_root: Path):
    md = subskill_root / "SKILL.md"
    assert md.exists() and md.stat().st_size > 0, f"{md} 缺失/为空"


@pytest.mark.smoke
def test_readme_exists(subskill_root: Path):
    assert (subskill_root / "README.md").exists(), "README.md 缺失"


@pytest.mark.smoke
def test_subskill_dirs_present(subskill_root: Path):
    for d in ("references", "scripts", "tests"):
        assert (subskill_root / d).is_dir(), f"{subskill_root}/{d} 缺失"


@pytest.mark.smoke
def test_skill_md_size_under_250(subskill_root: Path):
    lines = (subskill_root / "SKILL.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 250, f"SKILL.md {len(lines)} 行 > 上限 250"


@pytest.mark.smoke
def test_expected_scripts_present(scripts_dir: Path):
    for s in EXPECTED_SCRIPTS:
        assert (scripts_dir / s).exists(), f"scripts/{s} 缺失"


@pytest.mark.smoke
def test_expected_references_present(subskill_root: Path):
    for r in EXPECTED_REFS:
        assert (subskill_root / "references" / r).exists(), f"references/{r} 缺失"


@pytest.mark.smoke
def test_legacy_kicad_archived(subskill_root: Path):
    """旧 KiCad 栈已归档到 legacy-kicad/,不参与路由/测试。"""
    assert (subskill_root / "legacy-kicad").is_dir(), "legacy-kicad/ 归档缺失"


# ---- dfm_check 单测(读 fixtures,验证本地 DFM 逻辑)----

@pytest.mark.smoke
def test_dfm_passes_on_ok_fixture(fixtures_dir: Path):
    import dfm_check
    els = dfm_check.load(str(fixtures_dir / "minimal_ok.circuit.json"))
    res = dfm_check.check(els, dfm_check.PROCESSES["jlcpcb_standard"])
    assert res["passed"], f"OK fixture 不应有 violation: {res['violations']}"
    assert res["has_board"]


@pytest.mark.smoke
def test_dfm_flags_thin_trace_and_hole(fixtures_dir: Path):
    import dfm_check
    els = dfm_check.load(str(fixtures_dir / "minimal_bad.circuit.json"))
    res = dfm_check.check(els, dfm_check.PROCESSES["jlcpcb_standard"])
    assert not res["passed"], "bad fixture 应有 violation"
    assert "线宽" in " ".join(res["violations"]), "应检出线宽过细"
    assert any("封装" in w for w in res["warnings"]), "应透传供应商封装警告"


@pytest.mark.smoke
def test_dfm_cli_exit_codes(fixtures_dir: Path):
    import dfm_check
    assert dfm_check.main([str(fixtures_dir / "minimal_ok.circuit.json")]) == 0
    assert dfm_check.main([str(fixtures_dir / "minimal_bad.circuit.json")]) == 1
    assert dfm_check.main(["/nonexistent/circuit.json"]) == 2

from __future__ import annotations

import pytest


@pytest.mark.smoke
def test_skill_files_exist(subskill_root):
    assert (subskill_root / "SKILL.md").is_file()
    assert (subskill_root / "README.md").is_file()
    assert (subskill_root / "scripts" / "check_power_budget.py").is_file()


@pytest.mark.smoke
def test_standard_dirs_present(subskill_root):
    for name in ("references", "scripts", "tests", "examples"):
        assert (subskill_root / name).is_dir()


@pytest.mark.smoke
def test_skill_md_under_250_lines(subskill_root):
    lines = (subskill_root / "SKILL.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 250

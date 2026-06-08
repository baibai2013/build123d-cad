from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.smoke
def test_skill_md_exists(subskill_root: Path):
    md = subskill_root / "SKILL.md"
    assert md.exists()
    assert md.stat().st_size > 0


@pytest.mark.smoke
def test_readme_exists(subskill_root: Path):
    assert (subskill_root / "README.md").exists()


@pytest.mark.smoke
def test_standard_dirs_present(subskill_root: Path):
    for name in ("references", "scripts", "tests", "examples"):
        assert (subskill_root / name).is_dir()


@pytest.mark.smoke
def test_skill_md_size_under_250_lines(subskill_root: Path):
    lines = (subskill_root / "SKILL.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 250

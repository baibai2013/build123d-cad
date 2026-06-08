from __future__ import annotations

from pathlib import Path


def test_skill_files_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "SKILL.md").exists()
    assert (root / "scripts" / "generate_project.py").exists()
    assert (root / "scripts" / "run_firmware_tests.py").exists()
    assert (root / "references" / "module-handoff.md").exists()

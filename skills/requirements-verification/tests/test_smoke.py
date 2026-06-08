from __future__ import annotations

import pytest


@pytest.mark.smoke
def test_skill_files_exist(subskill_root):
    assert (subskill_root / "SKILL.md").is_file()
    assert (subskill_root / "README.md").is_file()
    assert (subskill_root / "scripts" / "validate_contract.py").is_file()


@pytest.mark.smoke
def test_example_contract_exists(example_project):
    assert (example_project / "requirements.yaml").is_file()
    assert (example_project / "verification_matrix.yaml").is_file()
    assert (example_project / "architecture.yaml").is_file()
    assert (example_project / "risk_register.md").is_file()

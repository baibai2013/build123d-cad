"""new_project.py 单测 —— 不依赖 kicad-cli,常跑(P3-1)。

验证起工程三件套:文件就位 + .kicad_pro 是合法 JSON + .kicad_pcb/.kicad_sch
含必需的 S-expression 头块 + 拒绝覆盖既有。
"""
from __future__ import annotations

import json

import pytest

import new_project  # 由 conftest 把 scripts/ 加进 sys.path


def test_create_project_writes_triplet(tmp_path):
    files = new_project.create_project("hip_driver", tmp_path)
    assert set(files) == {"pro", "pcb", "sch"}
    for path in files.values():
        assert path.is_file() and path.stat().st_size > 0


def test_pro_is_valid_json(tmp_path):
    files = new_project.create_project("b", tmp_path)
    data = json.loads(files["pro"].read_text(encoding="utf-8"))
    assert data["meta"]["filename"] == "b.kicad_pro"


def test_pcb_has_required_blocks(tmp_path):
    files = new_project.create_project("b", tmp_path)
    txt = files["pcb"].read_text(encoding="utf-8")
    # KiCad 必需块:kicad_pcb 根 + version + layers + setup + Edge.Cuts 板框层。
    for token in ("(kicad_pcb", "(version", "(layers", "(setup", "Edge.Cuts"):
        assert token in txt, f"缺 {token}"


def test_sch_has_root(tmp_path):
    files = new_project.create_project("b", tmp_path)
    txt = files["sch"].read_text(encoding="utf-8")
    assert "(kicad_sch" in txt and "(lib_symbols)" in txt


def test_refuses_overwrite(tmp_path):
    new_project.create_project("b", tmp_path)
    with pytest.raises(FileExistsError):
        new_project.create_project("b", tmp_path)


def test_cli_main(tmp_path):
    rc = new_project.main(["board", "--out", str(tmp_path / "out")])
    assert rc == 0
    assert (tmp_path / "out" / "board.kicad_pcb").is_file()

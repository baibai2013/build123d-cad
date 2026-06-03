"""export_fab.sh 实跑 smoke —— 需 kicad-cli,未装自动 skip(P3-1)。

本机无 KiCad 时 skip(经 conftest 的 kicad_cli fixture)。CI 装了 KiCad 9.x 的
runner 上会真跑:起空白工程 → export_fab.sh → 断言 gerbers.zip 产出。
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import new_project


def test_export_fab_produces_gerbers(kicad_cli, scripts_dir, tmp_path):
    # 起一个空白工程(new_project 不需要 kicad)。
    files = new_project.create_project("smoke", tmp_path)
    pcb = files["pcb"]

    out = tmp_path / "fab"
    proc = subprocess.run(
        ["bash", str(scripts_dir / "export_fab.sh"), str(pcb), str(out)],
        capture_output=True, text=True, timeout=120,
    )
    # 空板可能某些导出告警,但 Gerber/zip 应产出;断言关键产物存在。
    assert (out / "smoke-gerbers.zip").is_file(), \
        f"gerbers.zip 未产出\nstdout:{proc.stdout}\nstderr:{proc.stderr}"

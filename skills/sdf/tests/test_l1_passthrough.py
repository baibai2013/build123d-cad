"""L1(earthtojake)CLI 不破:直接用 L1 source/validation 校验 L2 产物。"""
from __future__ import annotations

from pathlib import Path

import pytest


def test_l1_source_module_imports() -> None:
    from sdf import source  # noqa: F401
    assert hasattr(source, "read_sdf_source")
    assert hasattr(source, "SDF_SUFFIX")
    assert source.SDF_SUFFIX == ".sdf"


def test_l1_validates_l2_world(example_world: Path, sample_urdf: Path, out_dir: Path) -> None:
    """L2 产出的 world.sdf 必须能通过 L1 bundled validation(无 error)。"""
    pytest.importorskip("yaml")
    pytest.importorskip("jsonschema")
    import export_sdf
    from sdf.validation import validate_sdf_xml

    report = export_sdf.export(example_world, out_dir, urdf=sample_urdf, no_l1=True)
    xml = report.output_world.read_text(encoding="utf-8")
    result = validate_sdf_xml(xml, source_path=report.output_world, base_dir=report.output_world.parent)
    assert not result.errors, [f.format() for f in result.errors]


def test_l1_validates_l2_model(example_world: Path, sample_urdf: Path, out_dir: Path) -> None:
    import export_sdf
    from sdf.validation import validate_sdf_xml

    report = export_sdf.export(example_world, out_dir, urdf=sample_urdf, no_l1=True)
    xml = report.output_model.read_text(encoding="utf-8")
    result = validate_sdf_xml(xml, source_path=report.output_model, base_dir=report.output_model.parent)
    assert not result.errors, [f.format() for f in result.errors]


def test_l1_cli_passthrough_runs(example_world: Path, sample_urdf: Path, out_dir: Path) -> None:
    """完整跑 L1 CLI(`python -m sdf`)passthrough,复用 shared cadpy。"""
    pytest.importorskip("yaml")
    pytest.importorskip("jsonschema")
    import export_sdf

    report = export_sdf.export(example_world, out_dir, urdf=sample_urdf, no_l1=False)
    assert report.l1_passed, report.l1_log
    # L1 会盖 cadpy 元数据注释
    assert "cadpy:sourceHash" in report.output_world.read_text(encoding="utf-8")

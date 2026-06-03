"""pcb_common + sch_from_skidl 离线单测(不依赖 kicad-cli / skidl)。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import pcb_common
import sch_from_skidl


# ── pcb_common ───────────────────────────────────────────────────────────────
def test_which_kicad_cli_optional_no_raise():
    """required=False:无论装没装都不抛异常,返回 str|None。"""
    res = pcb_common.which_kicad_cli(required=False)
    assert res is None or isinstance(res, str)


def test_kicad_available_is_bool():
    assert isinstance(pcb_common.kicad_available(), bool)


def test_electrical_output_dir_with_task():
    d = pcb_common.electrical_output_dir("m3-demo", base="/work/x")
    assert d == Path("/work/x/output/m3-demo/electrical")


def test_electrical_output_dir_no_task():
    d = pcb_common.electrical_output_dir(None, base="/work/x")
    assert d == Path("/work/x/electrical")


# ── sch_from_skidl.load_library(文件接口,解红线)───────────────────────────
def test_load_library_none_returns_empty():
    assert sch_from_skidl.load_library(None) == {}


def test_load_library_missing_file_returns_empty(tmp_path):
    assert sch_from_skidl.load_library(tmp_path / "nope.json") == {}


def test_load_library_reads_mapping(tmp_path):
    lib = {"ESP32-WROOM-32E": {"footprint": "RF_Module:ESP32-WROOM-32", "lcsc_id": "C701332"}}
    p = tmp_path / "library.json"
    p.write_text(json.dumps(lib), encoding="utf-8")
    out = sch_from_skidl.load_library(p)
    assert out["ESP32-WROOM-32E"]["footprint"].endswith("ESP32-WROOM-32")


def test_load_library_rejects_non_mapping(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("[1,2,3]", encoding="utf-8")
    with pytest.raises(ValueError):
        sch_from_skidl.load_library(p)

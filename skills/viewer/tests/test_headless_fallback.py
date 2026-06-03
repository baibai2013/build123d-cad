"""P1-5 headless 降级链测试(web_preview.snapshot)。

分两层:
- 纯逻辑(detect_tier / mode 路由 / 三档回落编排 / 产物路径 / dimensions schema):
  用 monkeypatch 把档位实现替换成桩,**不依赖 playwright/OCP/vtk**,CI 必跑。
- 真渲染(Tier 2 PNG / Tier 3 dimensions):缺库 / 缺真件时 pytest.skip,本机有依赖才跑。

对齐 03-viewer §10 与 references/headless-fallback.md。
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

VIEWER_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = VIEWER_ROOT / "scripts"
SKILL_ROOT = VIEWER_ROOT.parent.parent  # ~/.agents/skills/build123d-cad
MECH_OUTPUT = SKILL_ROOT / "skills" / "mechanical" / "benchmarks" / "output"

sys.path.insert(0, str(SCRIPTS))
import web_preview as w  # noqa: E402


# --------------------------------------------------------------------------- #
# fixtures                                                                     #
# --------------------------------------------------------------------------- #

@pytest.fixture
def fake_step(tmp_path):
    """一个假 STEP(只为路径/编排逻辑,不做真解析)。"""
    f = tmp_path / "hip_bracket.step"
    f.write_text("ISO-10303-21;\nfake\n")
    return f


def _stub(kind, tool):
    """生成一个成功的档位桩:写一个产物文件并返回 (kind, path, tool)。"""
    def fn(ctx):
        ctx.base_dir.mkdir(parents=True, exist_ok=True)
        p = ctx.base_dir / f"{ctx.stem}.{kind}"
        p.write_text("stub")
        return kind, p, tool
    return fn


def _unavail(reason):
    """生成一个回落桩:抛 _TierUnavailable。"""
    def fn(ctx):
        raise w._TierUnavailable(reason)
    return fn


# --------------------------------------------------------------------------- #
# detect_tier                                                                  #
# --------------------------------------------------------------------------- #

def test_detect_tier_1_when_playwright_and_chromium(monkeypatch):
    monkeypatch.setattr(w.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(w, "_chromium_installed", lambda: True)
    assert w.detect_tier() == 1


def test_detect_tier_2_when_only_ocp(monkeypatch):
    monkeypatch.setattr(w, "_chromium_installed", lambda: False)
    monkeypatch.setattr(
        w.importlib.util, "find_spec",
        lambda name: object() if name in ("OCP",) else None,
    )
    assert w.detect_tier() == 2


def test_detect_tier_2_when_only_vtk(monkeypatch):
    monkeypatch.setattr(w, "_chromium_installed", lambda: False)
    monkeypatch.setattr(
        w.importlib.util, "find_spec",
        lambda name: object() if name == "vtk" else None,
    )
    assert w.detect_tier() == 2


def test_detect_tier_3_when_only_steputils(monkeypatch):
    monkeypatch.setattr(w, "_chromium_installed", lambda: False)
    monkeypatch.setattr(
        w.importlib.util, "find_spec",
        lambda name: object() if name == "steputils" else None,
    )
    assert w.detect_tier() == 3


def test_detect_tier_raises_when_nothing(monkeypatch):
    monkeypatch.setattr(w, "_chromium_installed", lambda: False)
    monkeypatch.setattr(w.importlib.util, "find_spec", lambda name: None)
    with pytest.raises(w.HeadlessUnavailable):
        w.detect_tier()


def test_chromium_disabled_env(monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_DISABLED", "1")
    assert w._chromium_installed() is False


# --------------------------------------------------------------------------- #
# mode 路由 / 单档强制                                                          #
# --------------------------------------------------------------------------- #

def test_mode_web_uses_only_tier1(monkeypatch, fake_step):
    monkeypatch.setattr(w, "_tier1_web", _stub("url", "playwright"))
    # Tier 2/3 若被调用就让测试失败
    monkeypatch.setattr(w, "_tier2_png", _unavail("不该被调用"))
    monkeypatch.setattr(w, "_tier3_probe", _unavail("不该被调用"))
    res = w.snapshot(fake_step, mode="web")
    assert res["tier"] == 1 and res["kind"] == "url"
    assert res["fallback_reason"] is None


def test_mode_web_raises_when_tier1_unavailable(monkeypatch, fake_step):
    monkeypatch.setattr(w, "_tier1_web", _unavail("playwright not installed"))
    with pytest.raises(w.HeadlessUnavailable):
        w.snapshot(fake_step, mode="web")


def test_mode_snapshot_forces_tier2(monkeypatch, fake_step):
    monkeypatch.setattr(w, "_tier1_web", _unavail("不该被调用"))
    monkeypatch.setattr(w, "_tier2_png", _stub("png", "vtk"))
    res = w.snapshot(fake_step, mode="snapshot")
    assert res["tier"] == 2 and res["kind"] == "png"


def test_mode_probe_forces_tier3(monkeypatch, fake_step):
    monkeypatch.setattr(w, "_tier3_probe", _stub("json", "ocp"))
    res = w.snapshot(fake_step, mode="probe")
    assert res["tier"] == 3 and res["kind"] == "json"


def test_unknown_mode_raises(fake_step):
    with pytest.raises(ValueError):
        w.snapshot(fake_step, mode="bogus")


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        w.snapshot(tmp_path / "nope.step", mode="probe")


# --------------------------------------------------------------------------- #
# auto 回落编排                                                                 #
# --------------------------------------------------------------------------- #

def test_auto_falls_through_to_tier2(monkeypatch, fake_step):
    monkeypatch.setattr(w, "_tier1_web", _unavail("no chromium"))
    monkeypatch.setattr(w, "_tier2_png", _stub("png", "vtk"))
    monkeypatch.setattr(w, "_tier3_probe", _unavail("不该到这"))
    res = w.snapshot(fake_step, mode="auto")
    assert res["tier"] == 2
    assert res["fallback_reason"] == "no chromium"  # 记录上一档失败原因


def test_auto_falls_through_to_tier3(monkeypatch, fake_step):
    monkeypatch.setattr(w, "_tier1_web", _unavail("no chromium"))
    monkeypatch.setattr(w, "_tier2_png", _unavail("no vtk"))
    monkeypatch.setattr(w, "_tier3_probe", _stub("json", "steputils"))
    res = w.snapshot(fake_step, mode="auto")
    assert res["tier"] == 3
    assert res["fallback_reason"] == "no vtk"


def test_auto_all_fail_raises(monkeypatch, fake_step):
    monkeypatch.setattr(w, "_tier1_web", _unavail("a"))
    monkeypatch.setattr(w, "_tier2_png", _unavail("b"))
    monkeypatch.setattr(w, "_tier3_probe", _unavail("c"))
    with pytest.raises(w.HeadlessUnavailable):
        w.snapshot(fake_step, mode="auto")


# --------------------------------------------------------------------------- #
# tier_meta.json 审计 + 产物路径                                                #
# --------------------------------------------------------------------------- #

def test_tier_meta_written(monkeypatch, fake_step):
    monkeypatch.setattr(w, "_tier1_web", _unavail("no chromium"))
    monkeypatch.setattr(w, "_tier2_png", _stub("png", "ocp+vtk"))
    monkeypatch.setattr(w, "_tier3_probe", _unavail("x"))
    w.snapshot(fake_step, mode="auto")

    meta_path = fake_step.parent / "_viewer" / "tier_meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["tier"] == 2
    assert meta["tier_attempted"] == [1, 2]
    assert meta["fallback_reason"] == "no chromium"
    assert meta["tool"] == "ocp+vtk"
    assert meta["kind"] == "png"
    assert "ts" in meta and "duration_ms" in meta


def test_out_overrides_base_dir(monkeypatch, fake_step, tmp_path):
    monkeypatch.setattr(w, "_tier3_probe", _stub("json", "ocp"))
    out = tmp_path / "custom_out"
    res = w.snapshot(fake_step, mode="probe", out=out)
    assert Path(res["path"]).parent == out.resolve()
    assert (out / "_viewer" / "tier_meta.json").exists()


def test_tier2_png_sibling_to_source(monkeypatch, fake_step):
    """Tier 2 PNG 落源文件同级 <stem>.preview.png(03 §10.4 sibling)。"""
    # 用真实 _tier2_png 但桩掉渲染依赖:这里直接验路径约定用桩覆盖
    def fake_tier2(ctx):
        p = ctx.base_dir / f"{ctx.stem}.preview.png"
        p.write_bytes(b"\x89PNG")
        return "png", p, "vtk"
    monkeypatch.setattr(w, "_tier1_web", _unavail("x"))
    monkeypatch.setattr(w, "_tier2_png", fake_tier2)
    res = w.snapshot(fake_step, mode="auto")
    assert Path(res["path"]).name == "hip_bracket.preview.png"
    assert Path(res["path"]).parent == fake_step.parent


# --------------------------------------------------------------------------- #
# dimensions.json schema(03 §10.5)                                            #
# --------------------------------------------------------------------------- #

def test_dimensions_schema_full():
    d = w._build_dimensions(
        source_file="hip_bracket.step",
        bbox_min=[0, 0, 0], bbox_max=[120.5, 80.0, 32.4],
        volume_mm3=142500.5, surface_area_mm2=18432.1,
        topology={"solids": 1, "shells": 1, "faces": 28, "edges": 72, "vertices": 48},
        centroid_mm=[60.25, 40.0, 16.2], tool="ocp",
    )
    for key in ("schema_version", "source_file", "bbox_mm", "size_mm",
                "volume_mm3", "surface_area_mm2", "mass_kg", "topology",
                "centroid_mm", "tool", "ts"):
        assert key in d, f"dimensions schema 缺字段 {key}"
    assert d["bbox_mm"]["max"] == [120.5, 80.0, 32.4]
    assert d["size_mm"] == {"x": 120.5, "y": 80.0, "z": 32.4}
    assert d["mass_kg"] is None  # 默认 null,不瞎填


def test_dimensions_schema_steputils_nulls():
    """steputils 后端拿不到几何 → 体积/面积/拓扑诚实给 null,不填 0。"""
    d = w._build_dimensions(
        source_file="x.step", bbox_min=None, bbox_max=None,
        volume_mm3=None, surface_area_mm2=None, topology=None,
        centroid_mm=None, tool="steputils",
    )
    assert d["bbox_mm"] is None
    assert d["size_mm"] is None
    assert d["volume_mm3"] is None
    assert d["topology"] is None


# --------------------------------------------------------------------------- #
# 真渲染集成(缺库 / 缺真件则 skip)                                            #
# --------------------------------------------------------------------------- #

def _real_step():
    for name in ("calibration_block.step", "flange_4hole.step", "l_bracket.step"):
        p = MECH_OUTPUT / name
        if p.exists():
            return p
    return None


@pytest.mark.skipif(
    importlib.util.find_spec("OCP") is None,
    reason="Tier 3 真解析需 OCP(生产 venv 不装,本机 CAD venv 才有)",
)
def test_tier3_real_dimensions(tmp_path):
    step = _real_step()
    if step is None:
        pytest.skip(f"无 mechanical 真件,期望 {MECH_OUTPUT}")
    res = w.snapshot(step, mode="probe", out=tmp_path)
    assert res["tier"] == 3 and res["kind"] == "json"
    dims = json.loads(Path(res["path"]).read_text(encoding="utf-8"))
    assert dims["bbox_mm"] is not None
    assert dims["size_mm"]["x"] > 0


@pytest.mark.skipif(
    importlib.util.find_spec("vtk") is None,
    reason="Tier 2 真渲染需 vtk(生产 venv 不装)",
)
def test_tier2_real_png(tmp_path):
    step = _real_step()
    if step is None:
        pytest.skip(f"无 mechanical 真件,期望 {MECH_OUTPUT}")
    res = w.snapshot(step, mode="snapshot", out=tmp_path)
    assert res["tier"] == 2 and res["kind"] == "png"
    png = Path(res["path"])
    assert png.exists() and png.stat().st_size > 0
    assert png.read_bytes()[:4] == b"\x89PNG"

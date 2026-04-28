---
domain: fasteners
pattern: standard-part-module
source:
  repo: build123d-parts-lib (internal)
  file_path: build123d_parts_lib/parts/fasteners/
  examples: [nut_hex.py, nut_cap.py, nut_flange.py, nut_wing.py, nut_square.py, nut_tslot.py,
             socket_head_screw.py, screw_button_hex.py, screw_pan_phillips.py]
license: MIT
translate_cost: low
last_verified: 2026-04-28
confidence: 5
tags: [fasteners, standard-parts, yaml-factory, parametric, NamedTuple, fallback]
---

# 标准件模块结构（YAML-driven parametric module pattern）

每一个独立标准件类型（一个 `.py` 文件）遵循统一的四层结构：
`Spec NamedTuple → _FALLBACK dict → _load_specs() → make_xxx(size) → Part`。

YAML 优先，fallback 兜底，所有外部调用只接触 `make_xxx()`。

## 使用场景

- 需要新建一类标准件（螺丝头型、螺母形状、垫圈、嵌件）
- 需要让 `rebuild_cache.py` 自动发现并批量生成 STEP
- 需要在装配脚本中 `from xxx import make_xxx` 直接使用

## 核心代码模板

```python
"""DIN XXXX <part name> / <中文名>.

Standards: DIN XXXX
License: MIT

支持规格: M3, M4, M5

几何:
- <几何描述>
- 原点底面中心，+Z 为轴方向
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align, Box, BuildPart, BuildSketch, Cylinder,
    Part, Plane, RegularPolygon, export_step, extrude,
)

from ._thread_utils import make_internal_thread


# ─── 1. Spec 数据容器 ──────────────────────────────────────────────
class MyPartSpec(NamedTuple):
    d:     float   # 螺纹大径
    pitch: float   # 粗牙螺距
    s:     float   # 对边宽 / 主尺寸
    m:     float   # 高度
    # ...其他几何参数


# ─── 2. 内置后备数据 ──────────────────────────────────────────────
_FALLBACK: dict[str, MyPartSpec] = {
    "M3": MyPartSpec(d=3.0, pitch=0.50, s=5.5, m=4.0),
    "M4": MyPartSpec(d=4.0, pitch=0.70, s=7.0, m=5.0),
    "M5": MyPartSpec(d=5.0, pitch=0.80, s=8.0, m=6.5),
}


# ─── 3. YAML 加载（优先 YAML，缺失的 key 用 fallback 补） ──────────
def _load_specs() -> dict[str, MyPartSpec]:
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, MyPartSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "my-part-type":   # ← YAML type tag
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            dims   = entry.get("dimensions", {})
            try:
                specs[size.upper()] = MyPartSpec(
                    d     = float(thread["d"]),
                    pitch = float(thread["pitch"]),
                    s     = float(dims["s"]),
                    m     = float(dims["m"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


_SPECS = _load_specs()


# ─── 4. 公开工厂函数 ────────────────────────────────────────────
def make_my_part(size: str = "M4") -> Part:
    """<中文描述>.

    Orientation: origin at bottom face centre, +Z = thread axis.

    Args:
        size: 规格字符串 e.g. "M4"
    """
    key = size.upper().strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    spec = _SPECS[key]

    # ── 建模（见 patterns.md Pattern 13/14/15）──
    r_hex = spec.s / math.sqrt(3)
    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            RegularPolygon(radius=r_hex, side_count=6)
        extrude(amount=spec.m)

    solid = bp.part

    # 内螺纹减料
    thread_sub = make_internal_thread(spec.d, spec.pitch, spec.m)
    return solid.cut(thread_sub)


# ─── 5. 独立运行导出（build cache）──────────────────────────────
if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, spec in _SPECS.items():
        part = make_my_part(size=size)
        slug = size.lower()
        out  = cache_dir / f"{slug}_<part-tag>.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
```

## YAML 对应条目模板

```yaml
M4_MY_PART:
  aliases: [M4-my-part]
  standard: "DIN XXXX"
  type: my-part-type          # ← 与 _load_specs() 里的 type 匹配

  thread:
    d: 4.0
    pitch: 0.70
    unit: mm

  dimensions:
    s: 7.0
    m: 5.0
    # ...其他字段

  factory:
    module: build123d_parts_lib.parts.fasteners.my_module
    fn: make_my_part
    args: {size: "M4"}
    cache: cache/m4_my_part.step

  source:
    primary: https://...
    confidence: 4
    last_verified: 2026-04-28
```

## 关键技巧

- **六角外接圆**：`r = s / math.sqrt(3)`（对边宽 → 顶点半径）
- **ISO 小径**：`r_minor = (d - 1.2269 * pitch) / 2`
- **分段建模**：把每一段放单独 `BuildPart`，最后 `.fuse().translate()` 合并（Pattern 13）
- **边过滤容差**：用 `0.1–0.5 mm`，不要用 `1e-3`（OCC fuse 后坐标有浮动，Pattern 14）
- **make_internal_thread**：返回含中心的完整实体，直接 `cut` 即可；贯通孔 length=总高，盲孔 length=目标深度

## 踩过的坑

- **同一 BuildPart 混用 Cylinder + RegularPolygon extrude**：OCC 布尔运算不稳定，改为两个独立 BuildPart + fuse
- **fillet 边过滤容差太小**（`tol * 10 = 0.01`）：fuse 后边的精确坐标会漂移，导致过滤结果为空，fillet 静默跳过
- **翼片/凸台 Z 位置**：DIN 315 蝶形螺母的翼片应从 `z=0` 锚定（`wing_z_center = wing_h/2`），不是顶部
- **make_internal_thread 盲孔**：depth 超过实体高度时，cut 不会报错但会穿透，须控制 `bore_depth ≤ total_h`
- **RegularPolygon `radius`**：build123d 的 `RegularPolygon(radius=r, side_count=6)` 中 `radius` 是外接圆半径（顶点距中心），不是对边距的一半

## 用过此模式的项目

- `build123d-parts-lib/parts/fasteners/` — nut_hex / nut_cap / nut_flange / nut_wing / nut_square / nut_tslot / socket_head_screw / screw_button_hex / screw_pan_* (2026-04-28)

# 手动验证清单

> 不依赖外部工具的零件和装配验证方法，直接在 build123d 代码中执行。

---

## 1. BRep 有效性检查

```python
from build123d import *

# 基本有效性
assert part.part.is_valid, "BRep 几何无效！"

# 检查实体数量
solids = part.part.solids()
print(f"实体数量: {len(solids)}")
# 单体零件应该只有 1 个 solid
# 装配体可以有多个 solid
```

---

## 2. 体积断言

```python
# 体积必须大于 0
volume = part.part.volume
assert volume > 0, f"体积为 {volume}，零件可能是空的"

# 与预期值比对（容差 1%）
expected_volume = length * width * height  # 近似预期
tolerance = 0.01
assert abs(volume - expected_volume) / expected_volume < tolerance, \
    f"体积偏差过大: 实际 {volume:.2f} vs 预期 {expected_volume:.2f}"
```

---

## 3. 包围盒断言

```python
bb = part.part.bounding_box()
print(f"尺寸: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")

# 各维度在合理范围内
assert 0 < bb.size.X < 1000, f"X 尺寸异常: {bb.size.X}"
assert 0 < bb.size.Y < 1000, f"Y 尺寸异常: {bb.size.Y}"
assert 0 < bb.size.Z < 1000, f"Z 尺寸异常: {bb.size.Z}"

# 与设计尺寸比对
assert abs(bb.size.X - design_length) < 0.1, "长度偏差"
assert abs(bb.size.Y - design_width) < 0.1, "宽度偏差"
assert abs(bb.size.Z - design_height) < 0.1, "高度偏差"
```

---

## 4. 壁厚检查

```python
# Shell 操作后检查最薄处
# 方法：计算内外面之间的最小距离
inner_faces = part.faces().filter_by(Axis.Z)[:-1]  # 根据实际选择

# 简易检查：体积 vs 包围盒体积比
bb = part.part.bounding_box()
fill_ratio = part.part.volume / (bb.size.X * bb.size.Y * bb.size.Z)
print(f"填充率: {fill_ratio:.2%}")
# 实心零件 ≈ 50-100%，薄壁零件 < 30%

# 薄壁件最小壁厚检查（与打印最小壁厚比较）
min_wall = 2.0  # 设计壁厚
min_printable = 0.8  # FDM 最小壁厚
assert min_wall >= min_printable, \
    f"壁厚 {min_wall}mm 低于打印最小壁厚 {min_printable}mm"
```

---

## 5. 碰撞检测（装配体）

```python
from build123d import *

# 检查装配体中零件是否干涉
assembly = Compound(children=[body, lid, pin])

# do_children_intersect() 返回碰撞的零件对
collisions = assembly.do_children_intersect()
if collisions:
    print("⚠️ 发现干涉:")
    for pair in collisions:
        print(f"  {pair}")
else:
    print("✅ 无干涉")
```

---

## 6. 公差验证（配合间隙）

```python
# 轴孔配合检查
shaft_r = 5.0
hole_r = 5.2
clearance = hole_r - shaft_r

# FDM 间隙配合推荐值
min_clearance = 0.15
max_clearance = 0.5

assert min_clearance <= clearance <= max_clearance, \
    f"配合间隙 {clearance}mm 不在推荐范围 [{min_clearance}, {max_clearance}]mm"
print(f"✅ 配合间隙: {clearance}mm（间隙配合）")
```

---

## 7. 质量估算

```python
# 常见材料密度 (g/mm³)
DENSITY = {
    "PLA": 1.24e-3,
    "ABS": 1.04e-3,
    "PETG": 1.27e-3,
    "Nylon": 1.01e-3,
    "Aluminum_6061": 2.70e-3,
    "Steel_Q235": 7.85e-3,
    "Copper": 8.96e-3,
}

material = "PLA"
volume_mm3 = part.part.volume
mass_g = volume_mm3 * DENSITY[material]
print(f"材料: {material}")
print(f"体积: {volume_mm3:.2f} mm³")
print(f"质量: {mass_g:.1f} g")

# 与承载要求比对
max_mass = 100  # 设计上限 (g)
assert mass_g <= max_mass, \
    f"质量 {mass_g:.1f}g 超过上限 {max_mass}g"
```

---

## 8. 导出文件验证

```python
import os

# 导出并检查文件
export_step(part.part, "output.step")

# 文件存在且非空
assert os.path.exists("output.step"), "STEP 文件未生成"
file_size = os.path.getsize("output.step")
assert file_size > 1000, f"STEP 文件过小 ({file_size} bytes)，可能为空"
print(f"✅ STEP 文件: {file_size:,} bytes")

# 重新导入验证
reimported = import_step("output.step")
assert reimported.volume > 0, "重新导入后体积为 0"
# 体积一致性（STEP 精度损失 < 0.1%）
vol_diff = abs(reimported.volume - part.part.volume) / part.part.volume
assert vol_diff < 0.001, f"导出/导入体积偏差 {vol_diff:.4%}"
print(f"✅ 导出/导入体积偏差: {vol_diff:.6%}")
```

---

## 9. 综合验证模板

```python
def validate_part(part, name="part", expected_dims=None, material="PLA"):
    """综合零件验证"""
    print(f"\n{'='*40}")
    print(f"验证: {name}")
    print(f"{'='*40}")
    
    # 1. BRep 有效性
    assert part.is_valid, "❌ BRep 无效"
    print("✅ BRep 有效")
    
    # 2. 体积
    vol = part.volume
    assert vol > 0, "❌ 体积为 0"
    print(f"✅ 体积: {vol:.2f} mm³")
    
    # 3. 包围盒
    bb = part.bounding_box()
    dims = f"{bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}"
    print(f"✅ 尺寸: {dims} mm")
    
    if expected_dims:
        for actual, expected, axis in zip(
            [bb.size.X, bb.size.Y, bb.size.Z],
            expected_dims,
            ["X", "Y", "Z"]
        ):
            assert abs(actual - expected) < 0.5, \
                f"❌ {axis} 偏差: {actual:.2f} vs {expected:.2f}"
    
    # 4. 质量估算
    DENSITY = {"PLA": 1.24e-3, "ABS": 1.04e-3, "Aluminum_6061": 2.70e-3}
    if material in DENSITY:
        mass = vol * DENSITY[material]
        print(f"✅ 质量: {mass:.1f} g ({material})")
    
    # 5. 导出测试
    export_step(part, f"{name}.step")
    print(f"✅ STEP 导出成功")
    
    print(f"{'='*40}\n")

# 使用
validate_part(bracket.part, "bracket",
              expected_dims=(60, 40, 5),
              material="PLA")
```

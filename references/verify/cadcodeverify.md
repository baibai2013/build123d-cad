# CAD 代码自动验证策略

> LLM 生成的 CAD 代码需要多层验证。本文件描述自动验证的架构和实现方法。

---

## 1. 验证架构：三层防线

```
Layer 1: 语法验证    → 代码能否执行？有无 import 错误？
Layer 2: 几何验证    → 体积 > 0？包围盒合理？BRep 有效？
Layer 3: 语义验证    → 零件形状是否符合用户描述？尺寸是否匹配？
```

### 验证流程

```python
def verify_cad_code(code: str, description: str, expected_dims: dict = None):
    """三层 CAD 代码验证"""
    
    # Layer 1: 语法验证
    try:
        exec(code)
        print("✅ Layer 1: 代码执行成功")
    except Exception as e:
        print(f"❌ Layer 1: 执行错误 — {e}")
        return False
    
    # Layer 2: 几何验证
    assert part.part is not None, "❌ part 为空"
    assert part.part.is_valid(), "❌ BRep 无效"
    assert part.part.volume > 0, "❌ 体积为 0"
    
    bb = part.part.bounding_box()
    print(f"✅ Layer 2: 体积 {part.part.volume:.1f} mm³")
    print(f"   尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}")
    
    # Layer 3: 语义验证（尺寸匹配）
    if expected_dims:
        for axis, expected in expected_dims.items():
            actual = getattr(bb.size, axis)
            error = abs(actual - expected) / expected
            assert error < 0.05, f"❌ {axis} 偏差 {error:.1%}"
        print("✅ Layer 3: 尺寸匹配")
    
    return True
```

---

## 2. 自动修复循环

当验证失败时，可以用 LLM 自动修复：

```python
def verify_and_fix(code, description, max_iterations=3):
    """验证失败时自动修复"""
    for i in range(max_iterations):
        try:
            # 执行验证
            namespace = {}
            exec(code, namespace)
            
            # 检查结果
            part = namespace.get('part') or namespace.get('result')
            if part is None:
                raise ValueError("未找到 part 变量")
            
            # 获取实际的 part 对象
            actual_part = part.part if hasattr(part, 'part') else part
            
            assert actual_part.is_valid(), "BRep 无效"
            assert actual_part.volume > 0, "体积为 0"
            
            print(f"✅ 迭代 {i+1}: 验证通过")
            return code
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 迭代 {i+1}: {error_msg}")
            
            # 用 LLM 修复代码（伪代码）
            # code = llm_fix(code, error_msg, description)
            # 实际实现需要调用 Claude API
            
            if i == max_iterations - 1:
                print("⚠️ 达到最大修复次数，返回最后版本")
    
    return code
```

---

## 3. 何时需要自动验证

| 场景 | 验证级别 | 说明 |
|------|---------|------|
| 简单零件（<5 特征） | Layer 1-2 | 手动验证即可 |
| 复杂零件（扫掠/放样） | Layer 1-3 | 推荐自动验证 |
| 批量生成零件 | Layer 1-3 + 修复循环 | 必须 |
| 精确尺寸要求 | Layer 3 深度检查 | 关键尺寸断言 |
| 生产环境 | 全部 + 导出验证 | 包含 STEP 重导入验证 |

---

## 4. OCP 视觉辅助验证

Layer 3（语义验证）最可靠的方式是视觉检查：

```python
from ocp_vscode import show, save_screenshot

# 显示零件 + 截图
show(part, reset_camera=Camera.ISO, glass=True, tools=False)
save_screenshot("verification.png")

# 截图可以：
# 1. 人工检查是否符合描述
# 2. 用多模态 LLM（如 Claude）自动比对
```

### 多模态验证（概念）

```python
# 用 Claude Vision 验证零件截图是否匹配描述
# （需要 Anthropic API）
import anthropic

client = anthropic.Anthropic()

# 截图 + 描述 → Claude 判断是否匹配
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", ...}},
            {"type": "text", "text": f"这个零件截图是否匹配描述：'{description}'？"
             "检查：1.形状是否正确 2.特征是否完整 3.比例是否合理"}
        ]
    }]
)
```

---

## 5. 快速手动验证（最实用）

不需要任何外部工具，直接在代码末尾加入：

```python
# ===== 验证 =====
# 1. BRep 有效性
assert part.part.is_valid(), "BRep 无效"

# 2. 体积和尺寸
bb = part.part.bounding_box()
print(f"尺寸: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")
print(f"体积: {part.part.volume:.2f} mm³")

# 3. 关键尺寸断言
assert abs(bb.size.X - expected_length) < 0.5, "长度偏差"

# 4. 导出 + 重导入一致性
export_step(part.part, "output.step")
reimported = import_step("output.step")
vol_diff = abs(reimported.volume - part.part.volume) / part.part.volume
assert vol_diff < 0.001, f"导出精度损失 {vol_diff:.4%}"
print("✅ 验证通过")
```

---

## 6. 装配验证补充

装配体除了单件验证，还需要：

```python
from build123d import *

# 1. 碰撞检测
assembly = Compound(children=[body, lid])
collisions = assembly.do_children_intersect()
assert not collisions, f"装配干涉: {collisions}"

# 2. 零件完整性
for child in assembly.children:
    assert child.volume > 0, f"{child.label} 体积为 0"

# 3. 装配体总体积 ≈ 各零件体积之和（无重叠时）
total_volume = sum(c.volume for c in assembly.children)
assembly_volume = assembly.volume
overlap_ratio = abs(total_volume - assembly_volume) / total_volume
if overlap_ratio > 0.01:
    print(f"⚠️ 零件重叠 {overlap_ratio:.1%}")
```

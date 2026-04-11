# CADCodeVerify 集成指引

## 项目信息

- GitHub: https://github.com/CADCodeVerify/CADCodeVerify
- 论文: arXiv:2412.12979
- 最新论文: arXiv:2506.05978（2025年6月）

## 安装

```bash
git clone https://github.com/CADCodeVerify/CADCodeVerify
cd CADCodeVerify
pip install -r requirements.txt

export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"  # 可选
```

## 三 Agent 架构

```
Code Analysis Agent    → 执行代码 + 语法/几何验证
Visual Feedback Agent  → 渲染3D截图 + 多模态语义验证
Orchestrator Agent     → 汇总报告 + 决策修复循环
```

## 何时触发 CADCodeVerify

| 场景 | 是否需要 |
|------|---------|
| 简单零件（<5个特征） | 可选，手动验证即可 |
| 复杂零件（扫掠/放样/多步布尔） | 推荐 |
| 批量生成零件 | 必须 |
| 需要精确尺寸保证 | 推荐 |
| 生产环境 | 必须 |

## 效果数据（最新，2025年6月）

| 验证器 | Pass Rate |
|--------|-----------|
| 无验证（基线） | 78.25% |
| GPT-4o | 提升 |
| **Claude Sonnet 3.7** | **84.77%（最佳）** |

## 基本使用方式

```python
# 不使用 CADCodeVerify（快速原型）
code = generate_with_claude(description)
exec(code)
export_step(part, "output.step")

# 使用 CADCodeVerify（生产质量）
from cadcodeverify import verify_and_fix

result = verify_and_fix(
    code=generated_code,
    description=user_description,
    max_iterations=3
)
if result.passed:
    exec(result.fixed_code)
```

## 手动验证替代方案（快速检查）

如果不想部署 CADCodeVerify，用以下方式手动验证：

```python
# 1. 执行代码，检查是否有报错
try:
    exec(generated_code)
except Exception as e:
    print(f"执行错误: {e}")

# 2. 检查几何有效性
from build123d import *
# 代码执行后检查 part 是否非空
assert part.part is not None
assert part.part.volume > 0

# 3. 检查尺寸（关键尺寸断言）
bb = part.part.bounding_box()
assert abs(bb.size.X - expected_length) < 0.01  # 长度误差 < 0.01mm

# 4. 导出并检查文件大小
export_step(part, "test.step")
import os
assert os.path.getsize("test.step") > 1000  # 文件不为空
```

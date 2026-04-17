# 多视图截图规范 / Multi-View Screenshot Protocol

> 跟 `layer2-visual.md` 的关系：layer2-visual.md 负责"拍照后和参考图做 AI/OpenCV 比对"；本文档负责"拍出来的照片本身要符合规范"。

## 1. 视图命名

**7 个正交视图 + 1 个 ISO**：FRONT / BACK / LEFT / RIGHT / TOP / BOTTOM / ISO

视图名 **等于** 部件语义面，**不等于**世界坐标轴。部件目录必须提供 `part_face_mapping.yaml`（template 在 `references/verify/part-face-mapping-template.yaml`），否则 `multi_view_screenshot.py` 会打印 WARNING 并按坐标轴兜底。

## 2. 何时用什么

| 场景 | 推荐 | 原因 |
|---|---|---|
| 单部件快速预览 | ISO 单张 | 省时，能一眼看出轮廓对不对 |
| 多特征全面审查 | 7 视图 + skybox | 每个面单独可看 |
| 多部件装配审查 | 7 视图 + 多个 ISO 变体 | 需要从多角度看咬合 |
| 和实拍参考图比 | 7 视图 + `--mode iso` 4 变体 | 匹配营销 3/4 角度 |

## 3. 分辨率 / 背景 / 光照

- 默认 **800×800**（OCP Viewer 默认）
- 背景 **纯白**（OCP Viewer 默认）
- **不在对比前改光照参数**——保持默认，避免两次截图差异来自光照

## 4. 模型旋转 vs 相机移动

- **7 视图**：移动相机（`Camera.FRONT` etc.），**不旋转模型**
- **skybox 6 面**：固定 `Camera.FRONT`，**旋转模型**（`FACE_ROTATIONS` 查 `skybox_unfold.py`）

为什么 skybox 用旋转模型？保证 6 张图的光照/透视完全一致。移动相机会因为相机参数差异产生偏差。

## 5. 工具入口

```bash
# 7 视图正交
python3 scripts/visual/multi_view_screenshot.py <step> --mode ortho --face-mapping part_face_mapping.yaml

# 4 个 ISO 变体
python3 scripts/visual/multi_view_screenshot.py <step> --mode iso

# 全部 10 张
python3 scripts/visual/multi_view_screenshot.py <step> --mode both

# 6 面十字展开
python3 scripts/visual/skybox_unfold.py <step>
```

## 6. 产出文件命名约定

- `{name}_{VIEW}.png` — 7 正交视图（VIEW ∈ 第 1 节命名）
- `{name}_ISO_FRONT_TOP.png` / `..._FRONT_BOTTOM` / `..._BACK_TOP` / `..._BACK_BOTTOM`
- `{name}_skybox_{FACE}.png` + `{name}_skybox_unfolded.png`

## 7. 判定阈值

见 `edge-comparison.md`。

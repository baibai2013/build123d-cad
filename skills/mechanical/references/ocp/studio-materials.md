# OCP CAD Viewer — Studio 模式与材质

> PBR 渲染、环境光照、材质系统完整参考。

---

## 1. Studio 模式参数

### StudioEnvironment 预设

```python
from ocp_vscode import show, StudioEnvironment

show(part, studio_environment=StudioEnvironment.PROCEDURAL_STUDIO)
```

| 预设 | 风格 | 适用场景 |
|------|------|---------|
| `PROCEDURAL_STUDIO` | 柔和均匀照明（默认） | 通用零件展示 |
| 自定义 HDR URL | 自定义环境贴图 | 高级渲染场景 |

支持从 [Poly Haven](https://polyhaven.com/hdris) 加载自定义 HDR：

```python
show(part,
     studio_environment="https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/suburban_garden_4k.hdr",
     studio_env_rotation=275)
```

### Studio 参数一览

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `studio_environment` | StudioEnvironment/URL | PROCEDURAL_STUDIO | 环境贴图 |
| `studio_env_intensity` | float 0-3.0 | 1.0 | 环境光强度 |
| `studio_env_rotation` | int 0-360 | 0 | 环境贴图旋转（度） |
| `studio_background` | StudioBackground | ENVIRONMENT | 背景模式 |
| `studio_tone_mapping` | StudioToneMapping | NEUTRAL | 色调映射 |
| `studio_exposure` | float 0-3.0 | 1.0 | 曝光度 |
| `studio_shadow_intensity` | float 0-1.0 | 0.5 | 阴影强度 |
| `studio_shadow_softness` | float 0-1.0 | 0.2 | 阴影柔和度 |
| `studio_ao_intensity` | float 0-3.0 | 0.5 | 环境遮蔽强度 |
| `studio_texture_mapping` | StudioTextureMapping | TRIPLANAR | 纹理映射模式 |
| `studio_4k_env_maps` | bool | False | 使用 4K 环境贴图 |

### StudioBackground 枚举

| 值 | 效果 |
|----|------|
| `ENVIRONMENT` | 使用环境贴图作为背景 |
| `TRANSPARENT` | 透明背景（适合合成） |
| `GRADIENT` | 浅色渐变 |
| `GRADIENT_DARK` | 深色渐变 |
| `WHITE` | 纯白背景 |
| `GREY` | 灰色背景 |
| `DARKGREY` | 深灰背景 |

### StudioToneMapping 枚举

| 值 | 特点 |
|----|------|
| `NEUTRAL` | 中性色调（默认） |
| `ACES` | 电影级色调映射 |
| `NONE` | 无色调映射（线性） |

---

## 2. PBR 材质系统

### 安装

```bash
pip install threejs-materials
```

### 材质来源

| 来源 | 网址 | 特点 |
|------|------|------|
| GPUOpen | matlib.gpuopen.com | AMD 维护，高质量 |
| AmbientCG | ambientcg.com | CC0 免费，种类丰富 |
| Poly Haven | polyhaven.com/textures | 高质量 4K 纹理 |
| PhysicallyBased | physicallybased.info | 科学精确的材质参数 |

### 使用方式

```python
from threejs_materials import PbrProperties

# 从 GPUOpen 加载
alu = PbrProperties.from_gpuopen("Aluminum Hexagon")

# 覆盖参数
glass = PbrProperties.from_gpuopen("Glass").override(
    transmission=0.98, thickness=0.8
)

# 缩放纹理
metal = PbrProperties.from_ambientcg("Metal 049 C").scale(2, 2)

# 从 PhysicallyBased 加载 + 改颜色
plastic = PbrProperties.from_physicallybased("Plastic (Acrylic)")
red_plastic = plastic.override(color=(1, 0, 0))
```

### 赋值材质给 CAD 对象

```python
body.material = metal
body.color = metal.interpolate_color()  # 自动推导 CAD 视图颜色

# 或手动指定 CAD 颜色
body.color = "grey"
```

### 从 glTF/glb 加载材质

```python
materials = PbrProperties.load_gltf("brass_cube.gltf")
brass = materials["Ornamental Design Embossed Brass"]
```

---

## 3. 默认渲染参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `default_color` | (232, 176, 36) | 默认网格颜色（金色） |
| `default_edgecolor` | #707070 | 默认边颜色 |
| `metalness` | 0.30 | 金属度 |
| `roughness` | 0.65 | 粗糙度 |
| `ambient_intensity` | 1.00 | 环境光强度 |
| `direct_intensity` | 1.10 | 直射光强度 |

---

## 4. 实战配置方案

### 金属质感（舵机、铝件）

```python
show(servo_body,
     metalness=0.8,
     roughness=0.3,
     default_color=(180, 180, 190),
     studio_shadow_intensity=0.7,
     studio_ao_intensity=1.0)
```

### 塑料质感（3D 打印件）

```python
show(printed_part,
     metalness=0.0,
     roughness=0.8,
     default_color=(240, 240, 240),
     studio_shadow_softness=0.5)
```

### 透明材质（亚克力盖板）

```python
show(acrylic_cover,
     transparent=True,
     default_opacity=0.3,
     default_color=(200, 220, 255))
```

### 多材质装配体

```python
# 使用 PbrProperties
body.material = PbrProperties.from_ambientcg("Metal 049 C")
body.color = "grey"

cover.material = PbrProperties.from_gpuopen("Glass").override(
    transmission=0.9, thickness=0.5
)
cover.color = cover.material.interpolate_color()

show(body, cover,
     names=["body", "cover"],
     studio_environment=StudioEnvironment.PROCEDURAL_STUDIO,
     studio_shadow_intensity=0.6)
```

### 截图导出配置

```python
from ocp_vscode import show, save_screenshot

show(part,
     glass=True,
     tools=False,
     studio_background=StudioBackground.WHITE,
     deviation=0.01,
     angular_tolerance=0.05)

# 保存截图
save_screenshot("render.png")
```

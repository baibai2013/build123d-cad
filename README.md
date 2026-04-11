[English](README_EN.md) | 中文

<div align="center">

# build123d-cad.skill

> *「像机械师思考，而不是像程序员思考。」— Dave Cowden*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![build123d](https://img.shields.io/badge/build123d-CAD-green)](https://github.com/gumyr/build123d)
[![Nuwa](https://img.shields.io/badge/Made%20with-女娲.skill-orange)](https://github.com/alchaincyf/nuwa-skill)

<br>

**自然语言 → 参数化 CAD 代码 → 工业级 STEP 文件。一句话，一个零件。**

<br>

<img src="preview.png" alt="build123d 直齿轮示例 — OCP CAD Viewer" width="720">

*直齿轮 — OCP CAD Viewer 实时预览*

<br>

<img src="enclosure_explode.gif" alt="壳体爆炸动画 — 装配与展开演示" width="720">

*壳体爆炸动画 — 自动装配与展开演示*

<br>

融合 CadQuery 创始人 Dave Cowden 的建模哲学，<br>
基于 build123d API 全量梳理、20+ 真实案例（零件/装配/曲面/关节/安装）、6 大类参考文档，<br>
提炼 5 个核心心智模型、8 条代码质量启发式和完整的 CAD 代码生成工作流。<br>
覆盖零件建模、装配流、OCP 可视化、制造工艺、Dave Cowden 哲学、验证方法。

[看效果](#效果示例) · [安装](#安装) · [包含什么](#包含什么) · [示例零件](#示例零件)

</div>

---

## 效果示例

### 问：帮我做一个 100×80×50 的安装板，四角有 M5 螺栓孔

```python
# === Parameters ===
plate_l, plate_w, plate_h = 100, 80, 10
hole_r = 2.5          # M5 通孔
margin = 10           # 孔距边缘

# === Modeling ===
with BuildPart() as plate:
    Box(plate_l, plate_w, plate_h)
    with GridLocations(plate_l - 2*margin, plate_w - 2*margin, 2, 2):
        Hole(radius=hole_r)
    top = plate.faces().sort_by(Axis.Z)[-1]
    fillet(top.edges(), radius=3)

# === Export ===
export_step(plate.part, "mounting_plate.step")
```

### 问：做一个散热片，底板上面有8片散热鳍片

```python
# === Parameters ===
base_l, base_w, base_h = 80, 60, 5
fin_h, fin_t = 25, 1.5
fin_count = 8

# === Modeling ===
with BuildPart() as heatsink:
    Box(base_l, base_w, base_h)                    # 底板
    with BuildSketch(heatsink.faces().sort_by(Axis.Z)[-1]):
        with GridLocations(0, base_w / (fin_count + 1), 1, fin_count):
            Rectangle(base_l - 4, fin_t)
    extrude(amount=fin_h)                          # 拉伸鳍片

export_step(heatsink.part, "heat_sink.step")
```

### 问：我需要一个 90° 弯管接头

```python
# === Parameters ===
outer_r, wall_t = 15, 2
bend_r = 40

# === Modeling ===
path = Edge.make_circle(bend_r, start_angle=0, end_angle=90)
with BuildPart() as elbow:
    with BuildSketch(Plane(path @ 0, z_dir=path % 0)):
        Circle(outer_r)
        Circle(outer_r - wall_t, mode=Mode.SUBTRACT)
    sweep(path=path)

export_step(elbow.part, "pipe_elbow.step")
```

### 问：做一个带盖子的壳体，帮我生成爆炸动画

零件建模完成后，skill 自动提示生成装配预览和爆炸动画：

```python
from build123d import *
from ocp_vscode import show, Animation

# ===== 爆炸参数 =====
explode_dist = 30                              # 爆炸总距离 mm
half = explode_dist / 2

# ===== 显示装配态（动画起点） =====
show(body, assembled_lid,
     names=["body", "lid"],
     colors=["steelblue", "orange"])

# ===== 爆炸动画：炸2s → 停10s → 合2s → 停2s（16s循环） =====
t = [0, 2, 12, 14, 16]

animation = Animation()
animation.add_track("/Group/body", "t", t,
                    [[0,0,0], [0,0,-half], [0,0,-half], [0,0,0], [0,0,0]])
animation.add_track("/Group/lid",  "t", t,
                    [[0,0,0], [0,0,half],  [0,0,half],  [0,0,0], [0,0,0]])
animation.animate(1)
```

> 完整示例在 [`assets/assembly/`](assets/assembly/) 目录：[`13_enclosure_box.py`](assets/assembly/13_enclosure_box.py)（零件）+ [`13_enclosure_assembly.py`](assets/assembly/13_enclosure_assembly.py)（装配）+ [`13_enclosure_exploded.py`](assets/assembly/13_enclosure_exploded.py)（爆炸动画）

> 另有 20+ 个可运行示例，覆盖零件建模、装配预览、曲面建模、关节装配、安装实战等 5 大类。

这不是套了 CAD 模板的代码补全。每段代码都在运用 Dave Cowden 的建模哲学——「操作序列思维」「设计意图优先」「选择器代替坐标」「STEP 优先」。它不拼凑 API，它用机械师的认知框架帮你建模。

---

## 安装

```bash
npx skills add baibai2013/build123d-cad
```

然后在 Claude Code 里：

```
> 帮我建一个法兰盘，6个螺栓孔均匀分布
> 做一个 PCB 固定柱，M3 螺纹孔
> 生成一个薄壁壳体，壁厚 2mm
> 帮我做个阶梯轴，带键槽
```

### 环境要求

```bash
pip install build123d            # CAD 内核
pip install ocp-vscode           # VS Code 3D 预览
code --install-extension bernhard-42.ocp-cad-viewer  # VS Code CAD 查看器插件
```

---

## 包含什么

### 5 个心智模型（来自 Dave Cowden 建模哲学）

| 模型 | 一句话 | 来源 |
|------|--------|------|
| **操作序列思维** | CAD 代码描述的是加工步骤（取面→画草图→拉伸），不是坐标计算 | CadQuery 设计理念 |
| **设计意图优先** | 用 `sort_by`/`filter_by` 捕获「为什么在这里」，而非硬编码「在哪里」 | CadQuery 选择器系统 |
| **Python 生态即超能力** | 零件是 Python 对象——循环、函数、参数化都是免费的 | CadQuery 设计哲学 |
| **Working > Pretty** | 能跑的原型代码 > 优雅但报错的代码，先出零件再优化 | 工程实践 |
| **STEP 优先** | STEP 是 CAD 世界的通用语言，STL 只在 3D 打印时使用 | 工业标准 |

### 8 条代码质量启发式

1. **「能不能用中文向机械师描述？」** — 描述不清楚，代码就有问题
2. **「改一个尺寸还能跑吗？」** — 不能就说明硬编码了坐标
3. **「选择器还是坐标？」** — 能用 `.sort_by()` 的地方绝不用数字
4. **「有没有更简洁的写法？」** — Builder Mode 上下文 > 中间变量
5. **「STEP 还是 STL？」** — CNC/装配一律 STEP
6. **「能跑比好看重要」** — 先出零件，再优化代码
7. **「行数越少越好」** — 代码量是质量的反向指标
8. **「是『还不行』不是『不可能』」** — 说清限制，给出时间预期

### 11 种建模模式

| 模式 | 典型零件 |
|------|----------|
| 平板 + 孔阵列 | 安装板、面板 |
| 旋转体 + 极坐标阵列 | 法兰、齿轮 |
| 拉伸 + 布尔减 | 支架、壳体 |
| 薄壁壳体 (Shell) | 盒子、外壳 |
| 阶梯旋转体 + 切槽 | 轴、销 |
| 圆柱 + 螺纹/台阶 | 螺柱、固定柱 |
| 路径扫掠 (Sweep) | 弯管、导轨 |
| 多截面放样 (Loft) | 渐变形体 |
| 根体 + 逐特征融合 | 齿轮（复杂多边形） |
| 铰链/装配体 | 多体零件 |
| 沉头孔/锪孔 | 紧固件安装板 |

---

## 示例零件

### 零件建模 (`assets/parts/`)

| # | 零件 | 难度 | 核心技法 |
|---|------|------|----------|
| 01 | [安装板](assets/parts/01_mounting_plate.py) | ★ | Box + GridLocations + Hole |
| 02 | [法兰](assets/parts/02_flange.py) | ★★ | Cylinder + PolarLocations |
| 03 | [L型支架](assets/parts/03_l_bracket.py) | ★★ | 多段拉伸 + Fillet |
| 04 | [薄壁壳体](assets/parts/04_enclosure.py) | ★★★ | Shell + 壁厚控制 |
| 05 | [阶梯轴](assets/parts/05_shaft.py) | ★★★ | Revolve + 键槽切割 |
| 06 | [PCB固定柱](assets/parts/06_pcb_standoff.py) | ★★ | 同心圆柱组合 |
| 07 | [弯管接头](assets/parts/07_pipe_elbow.py) | ★★★ | Sweep + 空心截面 |
| 08 | [直齿轮](assets/parts/08_gear_spur_v2.py) | ★★★★★ | 根柱体 + 逐齿融合 |
| 09 | [铰链](assets/parts/09_hinge.py) | ★★★★ | 多体装配 |
| 10 | [散热片](assets/parts/10_heat_sink.py) | ★★★ | GridLocations + 鳍片拉伸 |
| 11 | [沉头孔板](assets/parts/11_countersunk_plate.py) | ★★ | CounterSinkHole |
| 12 | [卡扣](assets/parts/12_snap_fit_clip.py) | ★★★★ | 复杂轮廓拉伸 |
| 13 | [壳体](assets/assembly/13_enclosure_box.py) | ★★★ | Shell + 卡扣盖板 |

### 曲面建模 (`assets/surface/`)

| # | 零件 | 难度 | 核心技法 |
|---|------|------|----------|
| 14 | [有机外壳](assets/surface/14_organic_shell.py) | ★★★★ | 多截面 Loft + Shell |
| 15 | [截面过渡](assets/surface/15_loft_transition.py) | ★★★ | 圆→方→圆 Loft |

### 关节装配 (`assets/joints/`)

| # | 零件 | 难度 | 核心技法 |
|---|------|------|----------|
| 16 | [旋转铰链](assets/joints/16_revolute_hinge.py) | ★★★ | RevoluteJoint + connect_to |
| 17 | [四足腿链](assets/joints/17_quadruped_leg.py) | ★★★★★ | 多关节链 hip→knee→ankle→foot |

### 安装实战 (`assets/mounting/`)

| # | 零件 | 难度 | 核心技法 |
|---|------|------|----------|
| 18 | [舵机座 SG90](assets/mounting/18_servo_mount_sg90.py) | ★★★ | 舵机腔体 + 耳片槽 + 出线口 |
| 19 | [PCB 壳体](assets/mounting/19_pcb_enclosure.py) | ★★★★ | 铜柱 + USB-C 开口 + 卡扣盖 |
| 20 | [传感器支架](assets/mounting/20_sensor_bracket.py) | ★★★ | HC-SR04 超声波双窗口 |

### 装配与爆炸动画 (`assets/assembly/`)

| 文件 | 内容 |
|------|------|
| [13_enclosure_assembly.py](assets/assembly/13_enclosure_assembly.py) | 壳体装配预览 |
| [13_enclosure_exploded.py](assets/assembly/13_enclosure_exploded.py) | 壳体爆炸动画（16s 循环） |

---

## 工具脚本

`scripts/` 目录包含 8 个实用工具，按功能分类：

### 验证 (`scripts/validate/`)

| 脚本 | 功能 |
|------|------|
| [`validate_part.py`](scripts/validate/validate_part.py) | BRep 检查、体积/包围盒验证 |
| [`assembly_check.py`](scripts/validate/assembly_check.py) | 装配碰撞检测（多 STEP 干涉分析） |

### 分析 (`scripts/analysis/`)

| 脚本 | 功能 |
|------|------|
| [`extract_params.py`](scripts/analysis/extract_params.py) | 提取脚本中的参数化变量 |
| [`step_info.py`](scripts/analysis/step_info.py) | STEP 文件元数据检查 |
| [`mass_properties.py`](scripts/analysis/mass_properties.py) | 质量/惯性矩分析（13 种材料预设） |

### 导出 (`scripts/export/`)

| 脚本 | 功能 |
|------|------|
| [`batch_export.py`](scripts/export/batch_export.py) | 批量导出所有零件（支持多格式） |
| [`print_export.py`](scripts/export/print_export.py) | 打印导出（STL/3MF + 4 档精度预设） |

### 装配 (`scripts/assembly/`)

| 脚本 | 功能 |
|------|------|
| [`explode_generator.py`](scripts/assembly/explode_generator.py) | 通用爆炸动画代码生成器 |

---

## 仓库结构

```
build123d-cad/
├── README.md / README_EN.md          # 中英文说明
├── SKILL.md                          # 核心 Skill 定义（可直接安装）
├── references/                       # 6 大类参考文档
│   ├── parts/                        # 零件建模
│   │   ├── cheatsheet.md             #   API 速查表
│   │   ├── patterns.md               #   11 种建模模式
│   │   └── surface-modeling.md       #   曲面建模（Loft/Sweep/NURBS）
│   ├── assembly/                     # 装配流
│   │   ├── joints-reference.md       #   Joints 系统全参数
│   │   ├── assembly-patterns.md      #   8 种装配模式
│   │   ├── mounting-experience.md    #   安装实战（舵机/PCB/传感器）
│   │   └── exploded-animation.md     #   爆炸动画
│   ├── ocp/                          # OCP CAD Viewer
│   │   ├── show-reference.md         #   show() 100+ 参数
│   │   ├── animation-reference.md    #   Animation API
│   │   └── studio-materials.md       #   PBR 材质/光照
│   ├── process/                      # 制造工艺
│   │   ├── 3d-printing.md            #   3D 打印设计规则
│   │   ├── cnc-machining.md          #   CNC 加工
│   │   ├── laser-cutting.md          #   激光切割
│   │   └── cross-domain.md           #   跨领域对接（FEA/运动学/PCB）
│   ├── dave-cowden/                  # Dave Cowden 哲学
│   │   └── assembly-philosophy.md    #   装配哲学与诚实边界
│   └── verify/                       # 验证
│       ├── cadcodeverify.md          #   三层验证架构
│       ├── manual-checklist.md       #   手动验证清单
│       └── visual-verification.md    #   OCP 视觉验证
├── assets/                           # 20+ 可运行示例
│   ├── parts/                        #   13 个零件（01~13）
│   ├── assembly/                     #   装配预览 + 爆炸动画
│   ├── surface/                      #   曲面建模示例
│   ├── joints/                       #   关节装配示例
│   └── mounting/                     #   安装实战示例
└── scripts/                          # 8 个工具脚本
    ├── validate/                     #   几何验证 + 碰撞检测
    ├── analysis/                     #   参数提取 + STEP 信息 + 质量分析
    ├── export/                       #   批量导出 + 打印导出
    └── assembly/                     #   爆炸动画生成器
```

---

## 这个 Skill 是怎么造出来的

由 [女娲.skill](https://github.com/alchaincyf/nuwa-skill) 辅助生成。

女娲的工作流程：输入一个名字 → 多 Agent 并行调研 → 交叉验证提炼心智模型 → 构建 SKILL.md → 质量验证。

想蒸馏其他领域的专家 Skill？安装女娲：

```bash
npx skills add alchaincyf/nuwa-skill
```

---

## 许可证

MIT — 随便用，随便改，随便建模。

---

<div align="center">

*像机械师思考，而不是像程序员思考。*

<br>

MIT License

Made with [女娲.skill](https://github.com/alchaincyf/nuwa-skill)

</div>

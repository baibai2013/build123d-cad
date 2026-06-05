[English](README_EN.md) | 中文

<div align="center">

# build123d-cad — 硬件设计 Super Skill

> *「像机械师思考，而不是像程序员思考。」 — Dave Cowden*

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![build123d](https://img.shields.io/badge/build123d-CAD-green)](https://github.com/gumyr/build123d)
[![Nuwa](https://img.shields.io/badge/Made%20with-女娲.skill-orange)](https://github.com/alchaincyf/nuwa-skill)

<br>

**一次安装，11 个子技能。机械建模 → 网页预览 → 机器人描述 → 制造出工 → 电子域全链路。**

<br>

<img src="planetary_wood.gif" alt="木纹行星减速器 — 网页预览 + 纹理 URDF 关节动画" width="420">

*木纹行星减速器 — **viewer 子技能网页预览**（浏览器，纹理 URDF + 关节联动动画，毫米级真实装配）*

<br>

<img src="preview.png" alt="build123d 直齿轮示例 — OCP CAD Viewer" width="720">

*直齿轮 — **OCP CAD Viewer 实时预览**（VS Code 内，mechanical 子技能建模即时反馈）*

<br>

<img src="enclosure_explode.gif" alt="壳体爆炸动画 — 装配与展开演示" width="720">

*壳体爆炸动画 — mechanical 子技能装配能力*

<br>

</div>

---

## 这是什么

`build123d-cad` 是一个 **Claude Code Super Skill**：一个父技能下面挂 N 个子技能（monorepo 模块化）。
一次 `npx skills add` 安装即得多技能；每个子技能独立 `SKILL.md / references / scripts / tests`，可单独 `pytest` 回归。

设计来由与对照（与 `earthtojake/text-to-cad` 的横向 sibling skills 形态相比）：
- **横向铺**——能力多但安装分散、无统一方法论；
- **纵向深**(本仓库) ——一次安装即得多技能 + 共享方法论 + 子技能可独立测试。

详细架构与决策见 [`docs/architecture.md`](docs/architecture.md) 与
`share/build123d-cad改造/00-总览与目标架构.md`（公司内部规划文档）。

### 核心亮点

- 🖥️ **OCP CAD Viewer 预览**（VS Code 内实时）：build123d 建模即时反馈，所见即所得。
- 🌐 **网页预览**（viewer 子技能）：浏览器多引擎（CAD / PCB / 原理图 / 仿真），headless 截图；**URDF 每 link 纹理 + 关节联动动画**（毫米级真实装配，见上方木纹行星减速器 GIF）。
- 📦 **标准件库**：本地 `build123d-parts-lib` 收录 **8 类 66 种** 参数化标准件（紧固件 21 · 作动器 19 · 传动 9 · 轴承 7 · 销 4 · 舵机 3 · 挡圈 2 · 密封 1），另接 McMaster-Carr / GrabCAD / TraceParts 在线源。

---

## 子技能集合（11 个）

| 子技能 | 一句话定位 | 路径 | 优先级 |
|---|---|---|---|
| **mechanical**     | build123d Python CAD 全栈：参数化建模 / 装配 / 爆炸动画 / 仿真 / Playbook 方法论 | [skills/mechanical](skills/mechanical/) | P0 根基 |
| **viewer**         | 网页多引擎预览容器（CAD / PCB / 原理图 / 仿真），headless 截图；URDF 每 link GLB 纹理渲染（关节可动、米制单位） | [skills/viewer](skills/viewer/) | P0 |
| **urdf**           | build123d → URDF 自动导出（link/joint/mesh）+ pybullet 加载 + 纹理 URDF 工作流（木纹/贴图 + 渲染自验） | [skills/urdf](skills/urdf/) | P0 |
| **parts-catalog**  | 找现成标准件：本地 **build123d-parts-lib（8 类 66 种参数化标件）** + McMaster / GrabCAD / TraceParts 在线源 | [skills/parts-catalog](skills/parts-catalog/) | P0 |
| **srdf**           | MoveIt 规划组 + 自碰撞矩阵生成 | [skills/srdf](skills/srdf/) | P1 |
| **sdf**            | Gazebo 仿真世界（SDF 格式） | [skills/sdf](skills/sdf/) | P1 |
| **gcode**          | FDM 切片预检（壁厚 / 悬臂 / 打印估时） | [skills/gcode](skills/gcode/) | P1 |
| **sendcutsend**    | 激光切割预检 + DXF 报价 + kerf 补偿 | [skills/sendcutsend](skills/sendcutsend/) | P1 |
| **bambu-labs**     | Bambu 打印机上传作业 / AMS 多色 | [skills/bambu-labs](skills/bambu-labs/) | P2 |
| pcb (WIP)          | KiCad / DRC / Gerber 自动化（P3 占位，第一个 PCB 项目落地时启动） | [skills/pcb](skills/pcb/) | P3 |
| electronics-bom (WIP) | 电子 BOM / 元件库 / JLCPCB · Octopart 接入 | [skills/electronics-bom](skills/electronics-bom/) | P3 |

---

## 安装

```bash
npx skills add baibai2013/build123d-cad
```

依赖（按用到的子技能挑装）：

```bash
# mechanical / urdf 必备
pip install build123d ocp-vscode
code --install-extension bernhard-42.ocp-cad-viewer

# viewer (P0 后期)
node --version  # 直跑 server.mjs，不用 npm install

# urdf 加 pybullet 加载验证
pip install pybullet numpy
```

---

## 用法（Claude Code 内）

父 SKILL.md 按关键词路由到子技能，进入子技能后再读细节：

```
> 帮我建一个法兰盘，6 个螺栓孔均匀分布     # → mechanical
> 把这个 STEP 在浏览器里打开看看            # → viewer
> 把这台机器人导成 URDF + 加载到 pybullet   # → urdf, viewer
> 这个支架激光切多少钱                       # → mechanical → sendcutsend
> 帮我找一个 608 轴承的 STEP 文件            # → parts-catalog → mechanical
```

---

## 架构原则（5 条）

1. **两层路由**：父 SKILL 只列关键词表（≤ 220 行）；进子技能再读详细 references。父级不展开实现。
2. **子技能自治**：每个子技能必须有 `SKILL.md + README.md`，外加 `references/ scripts/ tests/` 至少一项。
3. **零互引用**：子技能之间不直接引用彼此的 references；跨技能调用一律走 `shared/` 协议（CI grep 红线）。
4. **文件标准接口**：子技能间不做函数调用，通过约定的输出文件路径交换（如 `output/<task>/<part>.step`）。
5. **可独立测试**：`cd skills/<name> && pytest tests/` 秒级反馈；父级 `tests/` 只测跨子技能流程。

---

## 仓库结构

```
build123d-cad/
├── SKILL.md                          # 父级路由（≤ 220 行）：关键词 → 子技能
├── README.md                         # 本文件（开发者视角）
├── skills/                           # 子技能集合（11 个），每个可独立 pytest
│   ├── mechanical/                   #   build123d 建模 / 装配 / 仿真 / Playbook
│   ├── viewer/                       #   网页多引擎预览
│   │   └── scripts/engines/{cad,pcb,sch,sim}/
│   ├── urdf/  srdf/  sdf/            #   机器人描述
│   ├── gcode/  sendcutsend/  bambu-labs/  parts-catalog/   # 制造出工
│   └── pcb/  electronics-bom/        #   电子域（P3 占位）
├── shared/                           # 跨子技能协议
│   ├── handoff-protocols.md          #   文件接口 + 路径约定
│   ├── multi-skill-router.md         #   关键词 → 子技能权威映射
│   └── dependencies.md               #   依赖图与被依赖度
├── tests/                            # 父级跨子技能集成测试
└── docs/                             # 架构与扩展指南
    ├── architecture.md               #   架构说明
    ├── adding-new-subskill.md        #   加新子技能 9 步
    └── SKILL.parent.draft.md         #   父 SKILL.md 草稿（P0-2 完成后替换）
```

---

## 加一个新子技能

未来扩 PCB / 电子 / 固件等域，流程固定（详见 [`docs/adding-new-subskill.md`](docs/adding-new-subskill.md)）：

```bash
mkdir -p skills/<name>/{references,scripts,tests}
touch skills/<name>/{SKILL.md,README.md} skills/<name>/tests/conftest.py
```

然后改 3 处共享配置：父 `SKILL.md` 路由表 / `shared/multi-skill-router.md` 关键词表 /
`shared/dependencies.md` 上下游依赖。

---

## 进度

| 阶段 | 范围 | 状态 |
|---|---|---|
| P0 | 骨架 + mechanical 迁移 + viewer/urdf/parts-catalog 复刻 + tests 骨架 | 进行中（2026-06-02 ~ 06-08） |
| P1 | srdf/sdf/gcode/sendcutsend + 数据源/代码源补齐 + agent-eval | 排期中（2026-06-09 ~ 06-15） |
| P2 | bambu-labs / Playbook 治理 / AIGC case 沉淀 | 按需 |
| P3 | pcb / electronics-bom（电子域开张，需用户给第一个 PCB 项目） | 待 Gate 3 |

实施细节见公司内部规划：`share/build123d-cad改造/01-分工与排期.md`。

---

## 这个 Skill 是怎么造出来的

子技能 mechanical 由 [女娲.skill](https://github.com/alchaincyf/nuwa-skill) 辅助生成；super skill 化改造（本仓库当前形态）由仿生机器人公司 tech_lead 牵头。

想蒸馏其他领域的专家 Skill：

```bash
npx skills add alchaincyf/nuwa-skill
```

---

## 免责声明

本项目以工程探索与学习交流为目的。AI 辅助生成的设计建议须结合专业工具评审，实际制造公差请根据工艺自行调整。上游依赖库持续演进，部分示例代码可能需要适配。

---

## 许可证

Apache License 2.0 — 详见 [LICENSE](LICENSE)。

与上游 [build123d](https://github.com/gumyr/build123d)（Apache 2.0）保持一致。

---

<div align="center">

*像机械师思考，而不是像程序员思考。*

<br>

Apache License 2.0 · Made with [女娲.skill](https://github.com/alchaincyf/nuwa-skill)

</div>

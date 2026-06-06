---
name: simulation
description: |
  build123d-cad 的无头动力学仿真子技能。把 URDF/SDF 丢进 pybullet HEADLESS(p.DIRECT)跑 N 步,
  在 被动跌落 / 位置保持 / 简单步态 三种控制模式下记录时序(关节角 / 基座位姿 / 速度 / 接触)
  到 results.json,用 pybullet 自带离屏渲染器(getCameraImage + ER_TINY_RENDERER,无 GPU/无 GUI)
  出关键帧 PNG(+可选 MP4),并自验稳定性(没穿地 / 没数值爆炸 / 关节在限位 / 末态稳)
  + 出小尺寸截图给 AI 视觉复核。可进 CI。
  触发词:仿真跑一下、动力学、pybullet、跌落测试、站得稳吗、步态仿真、headless sim、
  物理引擎、会不会翻、关节限位、接触力。
  本子技能不做:MuJoCo / Gazebo 真跑(→ sdf 出世界)、GUI 交互预览(→ mechanical pybullet_preview / viewer)、
  机器人描述生成(→ urdf)、网页 3D 预览(→ viewer)、FK/IK 解析(→ mechanical)。
owner: hardware
status: active
tech: pybullet
since: 2026-06-06
---

# simulation · 无头动力学仿真

把机器人描述丢进物理引擎跑得稳不稳的入口。**纯 headless(p.DIRECT),出数据 + 图给 AI/CI 判**,
不弹 GUI、不依赖 viewer/playwright。

> 一句话:urdf 管"描述对",simulation 管"丢进物理引擎跑得稳"(跌落/站立/步态,判稳 + 截图)。
>
> 现状:本 MVP 只做 pybullet headless 闭环;MuJoCo/Gazebo 真跑、viewer 回放、完整步态优化 deferred。

---

## AI 执行准入序列

1. 收到 仿真 / 动力学 / 跑一下 / 站得稳吗 类需求 → 先读本 SKILL.md「主流程」。
2. 控制模式 / pybullet API 拿不准 → 读 `references/pybullet-headless.md` / `control-modes.md`,
   **不凭印象编 flag 或 renderer 枚举**(headless 必须 ER_TINY_RENDERER)。
3. references/ 是查询表,不当 Playbook 全量读。
4. 跨子技能走 `../../shared/handoff-protocols.md` 文件接口,不互调函数、不互引 references。
5. 判定靠 `verify_sim.py` 退出码 + AI 看 static→settled 两图,**不靠"应该没事"**。

---

## 主流程

```
[1] 取输入   urdf:output/<task>/<robot>.urdf + meshes/    sdf:output/<task>/{world,model}.sdf
        ▼
[2] 选模式   passive(跌落/穿地) | hold(位置保持/站立) | gait(stand/trot/crawl 简单步态)
        ▼
[3] 跑仿真   run_sim.py:p.DIRECT 无头 → setGravity + plane → load → POSITION_CONTROL 循环 → stepSimulation×N
        ▼
[4] 出产物   <robot>.results.json + frames/*.png(ER_TINY 离屏)+ <robot>.sim.mp4(有 imageio/cv2 才出)
        ▼
[5] 自验     verify_sim.py:断言 没穿地/没爆炸/关节限位/末态稳 → _verify/{static,settled}.png + checklist → 退出码 0/1
```

每步脚本见下「脚本索引」,参数读脚本顶部 docstring,不要凭名字猜。

---

## 控制模式速查（全表见 references/control-modes.md）

| 模式 | 测什么 | 控制 | 典型 steps |
|---|---|---|---|
| `passive` | 自由跌落:穿地 / 散架 / 数值爆炸 | 不施加控制 | 480–1200 |
| `hold` | 站得稳:伺服到限位中点保持直立 | POSITION_CONTROL → 中点 | 720–2400 |
| `gait` | 动起来会不会翻:相位正弦驱动 | 相位偏置 sin(MVP 非 Bezier+IK) | 1600–4800 |

关键 pybullet 调用(全表见 references/pybullet-headless.md):`connect(DIRECT)` → 双 `setAdditionalSearchPath` →
`setGravity/setTimeStep` → `loadURDF`(`.sdf`走`loadSDF`取`ids[0]`,不叠 plane) → `getJointInfo` →
`setJointMotorControl2(POSITION_CONTROL)` → `stepSimulation`(无 sleep) →
`getBasePositionAndOrientation`/`getBaseVelocity`/`getJointStates`/`getContactPoints` →
`getCameraImage(..., renderer=ER_TINY_RENDERER)` → `disconnect`。

---

## 脚本索引（scripts/）

| 脚本 | 职责 | 缺工具行为 |
|---|---|---|
| `run_sim.py <model> [--mode]` | p.DIRECT 跑 N 步 → `results.json` + `<robot>.trajectory.json`(cad 回放用) + `frames/` + mp4(best-effort) | 缺 pybullet → 安装提示退出 |
| `verify_sim.py <model> [--mode]` | import run_sim 跑一次 + 断言稳定性 + 出 `_verify/` 小图 + checklist | 缺 pybullet→退 3;断言挂→退 1;输入错→退 2 |
| `to_trajectory.py <results.json>` | results.json → cad 引擎原生轨迹格式 `{points:[{timeFromStartSec,positionsByNameDeg}]}`(run_sim 已顺带产出) | 输入缺→退 2 |
| `sim_render.py`（helper / 可单跑） | `getCameraImage(ER_TINY)`→PNG(PIL→imageio→.npy 兜底);mp4(imageio→cv2 否则跳过+manifest) | 缺 PIL/imageio → .npy 兜底,绝不丢帧 |

CLI 全参数读脚本顶部 docstring。常用:
`run_sim.py r.urdf --mode gait --gait trot --steps 2400 --outdir output/<task>/simulation`、
`verify_sim.py r.urdf --mode hold`(退出码即判定)。

---

## handoff（文件接口，不互引）

| 链路 | 产物 → 用途 |
|---|---|
| **urdf → simulation** | `<robot>.urdf` + `meshes/` → `loadURDF`(base 目录进 search path 解析相对 mesh) |
| **sdf → simulation** | `{world,model}.sdf` → `loadSDF` 取 `ids[0]`(世界自带地面,不叠 plane) |
| **simulation → 用户/CI** | `results.json`(判稳数据) + `frames/`/`mp4` + `_verify/`(截图 + checklist) |
| simulation → **viewer**（3D 回放,主） | `<robot>.trajectory.json` → cad 引擎加载 URDF + `?trajectory=` 时间轴回放(关节随时序动,见 docs/simulation-design.md) |
| simulation → **viewer**（数据面板,辅） | `results.json` → `?engine=sim`(曲线 + 判稳徽章 + 帧 scrubber) |

输出全落 `output/<task>/simulation/`(布局/schema 见 `references/output-contract.md`)。

---

## 角色规则（子技能本地）

1. **永远 headless**:`p.connect(p.DIRECT)`,绝不弹 GUI;离屏渲染必须 `ER_TINY_RENDERER`。
2. **不编 pybullet flag**:renderer 枚举、控制模式、loadSDF 返回形态一律查 references / 官方文档。
3. **判定靠退出码 + 看图**:`verify_sim` 退 0 才算稳;再看 static→settled 两图核对渲染/朝向/姿态。
4. **MP4 best-effort,PNG 永远出**:缺 imageio/cv2 不报错,写 `frames/manifest.json` 留 ffmpeg 命令。
5. **解耦**:描述找 urdf,世界找 sdf,网页预览找 viewer,FK/IK 解析找 mechanical,本技能只管"丢进物理引擎跑 + 判稳"。

---

## 不做什么

- ❌ MuJoCo / Gazebo 真跑(出 Gazebo 世界 → sdf)
- ❌ GUI 交互预览(→ mechanical `pybullet_preview.py` / viewer)
- ❌ 生成 URDF/SDF(→ urdf / sdf)
- ❌ 网页 3D 预览(→ viewer)
- ❌ FK/IK 解析求解(→ mechanical references/simulation)
- ❌ 高保真步态优化(MVP 只 简单相位正弦 步态)

---

## references/

- `pybullet-headless.md` — DIRECT 连接 / 双 searchpath / loadURDF vs loadSDF / 关节控制 / 离屏渲染(为何 TINY)
- `control-modes.md` — passive/hold/gait 各测什么 + 参数 + GAITS 相位表
- `stability-checks.md` — 四项断言数值定义/阈值 + AI 视觉清单(verify_sim 的大脑)
- `output-contract.md` — results.json schema + `output/<task>/simulation/` 布局 + handoff in/out

不在 references/ 的 pybullet API 先查官方 [PyBullet Quickstart](https://github.com/bulletphysics/bullet3/blob/master/docs/pybullet.md) 再补表,不凭印象写。

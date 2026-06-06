# 代码做仿真 + 3D 预览 —— 技术选型与方案

> 状态:方案设计(draft)。落地子技能:`simulation`(跑+判) + `viewer`(3D 回放)。
> 关联:README 路线图「仿真深化」;`skills/simulation/SKILL.md`;`shared/handoff-protocols.md`。

## 0. 目标

用**代码**驱动机器人仿真,并且**能在浏览器里 3D 看它真实地动**(转视角、拖时间轴、关节跟着跑),
而不是给一段录屏 MP4 / PNG 幻灯片。整条链路 headless 可复现、可进 CI、可截图自验。

---

## 1. 技术选型(决策 + 理由)

| 维度 | 选型 | 为什么(对比备选) |
|---|---|---|
| **物理引擎** | **pybullet**(headless `p.DIRECT`) | 纯 Python 装即用、URDF/SDF 原生加载、确定性 step、CPU 软渲染可 headless。MuJoCo 需额外许可/格式转换;Gazebo 重(ROS 栈、装机难),且「出 Gazebo 世界」本就归 `sdf` 子技能。**MuJoCo/Gazebo 真跑列为后续**,先用 pybullet 把闭环跑通。 |
| **仿真编排** | 代码即仿真:`run_sim.py` 三模式(passive/hold/gait) | 参数(模式/步数/步态)是 CLI flag,可复现、可回归。GUI 拖滑块的交互式调试由 `mechanical/pybullet_preview.py` 补位,不在本链路。 |
| **判定** | `verify_sim.py` 四项断言 + 退出码 | 没穿地/没爆炸/关节限位/末态稳 → 0/1。机器可判,不靠肉眼。 |
| **3D 预览渲染** | **复用 viewer 的 cad 引擎**(three.js + urdf-loader + 既有 `playUrdfTrajectory`) | cad 引擎已能渲 URDF + 有关节控制 + **已内建轨迹回放基建**(见 §3)。自造 three.js 场景=重复造轮子;扩 cad 引擎=复用全部成熟渲染,只补「喂轨迹」。 |
| **预览页面体系** | cad 引擎做 **3D 回放**(主),sim 引擎做 **数据面板**(辅:曲线+判稳徽章) | 两者互补:cad 看「它怎么动」,sim 看「数据/判稳对不对」。都在 `skills/viewer/` 下(预览归 viewer,不归 simulation)。 |
| **预览渲染管线** | 纯 three.js(WebGL),headless 走 swiftshader | `verify_urdf.py` 已证明 `--use-gl=angle --use-angle=swiftshader` 能 headless 截 WebGL(木纹行星减速器 _verify 图为证)。 |

**关键约束(守 super-skill 边界)**:`simulation` 子技能**只产数据**(results.json + 轨迹文件),
**不碰预览基建**;3D 回放整个落在 `viewer`。两者通过 `output/<task>/simulation/` 文件 handoff,不互调函数。

---

## 2. 端到端工作流

```
① 描述      urdf 子技能 → <robot>.urdf + meshes/
     ▼
② 跑仿真    simulation/run_sim.py:pybullet headless 加载 → passive/hold/gait 跑 N 步
     │       → results.json(每时刻 关节角[rad] + 基座位姿 + 速度 + 接触)
     │       → frames/*.png(离屏关键帧,数据面板用)
     │       → <robot>.trajectory.json  ★新增:cad 引擎原生轨迹格式(关节角[deg] by name)
     ▼
③ 判稳      simulation/verify_sim.py:四项断言 → 退出码 0/1 + _verify/ 截图 + checklist
     ▼
④ 3D 回放   viewer cad 引擎:加载 <robot>.urdf + ?trajectory=<robot>.trajectory.json
     │       → 时间轴 play/scrub,关节按轨迹动,可转视角  ★本方案核心
     └ 辅:viewer sim 引擎打开 results.json → 曲线 + 判稳徽章(数据视图)
```

**数据闭环点**:② 记的 `timeseries[].joint_pos` + `joints[].name` 就是「让模型动起来」的全部输入。
转成 cad 认的格式即可回放,无需 MP4。

---

## 3. 复用:cad 引擎已内建的轨迹回放(探明)

cad 引擎源码(`engines/cad/viewer-src/`)里已存在:

- `playUrdfTrajectory(fileRef, baseJointValues, trajectory, finalJointValues)`
  (`src/client/components/CadWorkspace.js` ~5027)—— `requestAnimationFrame` 按时间插值驱动关节。
- `interpolateTrajectoryJointValues(trajectory, elapsedSec, fallback)`
  (`src/client/workbench/robotMotionControls.js` ~43)—— 线性插值。
- `cancelUrdfTrajectoryPlayback()`、`urdfTrajectoryPlaybackRef`、关节→mesh 的 `applyUrdfPoseToMeshData()`。
- 关节值状态 `jointValuesByFileRef` + `setJointValuesByFileRef`(已接 UI 滑块 + mesh 更新)。

**它认的轨迹格式**:
```jsonc
{ "points": [
    { "timeFromStartSec": 0.0, "positionsByNameDeg": { "<joint>": <deg>, ... } },
    { "timeFromStartSec": 0.05, "positionsByNameDeg": { ... } }
] }
```

→ 所以 cad 侧只需:**加 `?trajectory=` 参数** → fetch 该文件 → 调既有 `playUrdfTrajectory` + 加一个时间轴 UI。
不用新写渲染/插值/驱动逻辑。

---

## 4. 落地改动(分子技能)

### simulation(只加「产轨迹文件」)
- `scripts/to_trajectory.py`(或并进 run_sim):读 `results.json` →
  对每个采样 `t`,把 `joint_pos[i]`(rad)按 `joints[]` 顺序映射到关节名、转 deg →
  写 `<robot>.trajectory.json`(§3 格式)。run_sim/verify_sim 跑完顺带产出。
- handoff/SKILL/output-contract:`output/<task>/simulation/` 增 `<robot>.trajectory.json`;
  预览提示改为「在 viewer cad 引擎开 URDF + ?trajectory=…」。
- **不动 simulation 的「不做什么」边界**(预览仍归 viewer)。

### viewer / cad 引擎(加「喂轨迹 + 时间轴」)
- `viewer-src`:解析新 URL 参数 `?trajectory=<file>`(相对 `?dir=`,经 `/files/` 取);
  加载后调既有 `playUrdfTrajectory`;在 `UrdfFileSheet.js` 加「▶ 仿真回放 / 暂停 / 时间轴 scrub / 时长」控件。
- `vite build` → 刷新 `engines/cad/dist/`(工具链已确认:node 20 + pnpm + node_modules 在)。
- start.sh:支持可选轨迹参数,把 `&trajectory=` 拼进 URL(上游只产文件路径,URL 由 viewer 拼,守 dependencies 规则)。

### sim 引擎(降为数据面板,保留)
- 已建的 `engines/sim/dist/index.html`(曲线 + 判稳徽章 + 帧 scrubber)留作**数据视图**;
  `results.json → engine=sim` 路由保留。**MP4/PNG 不再是「预览」主角**,只在数据面板里作辅助。

---

## 5. 已知缺口 / 后续

1. **浮动基座位姿**:cad 既有回放驱动**关节**;passive 跌落的基座平移/翻滚是否驱动需在 cad 侧补
   (用 `base_pos`/`base_rpy` 设 root transform)。MVP 先保证关节动,基座作为紧接的增量。
2. **MuJoCo/Gazebo 真跑**:后续;Gazebo 世界归 `sdf`。
3. **golden-diff 回归**:`results.json` 已记 `pybullet_api`,留作将来轨迹基线比对。
4. **大量关节配色/可读性**:数据面板曲线多线时的可读性。

---

## 6. 验证(端到端,headless)

```bash
VENV=~/work/build123d-parts-lib/.venv/bin/python
R2D2=$($VENV -c "import pybullet_data,os;print(os.path.join(pybullet_data.getDataPath(),'r2d2.urdf'))")
# ② 跑 + 产 results.json + trajectory.json
$VENV skills/simulation/scripts/run_sim.py "$R2D2" --mode hold --steps 1200 --base-z 0.05 \
      --outdir output/simdemo/simulation
# ④ 3D 回放(swiftshader headless 截图自证关节在动:t=0 vs t=末 两帧对比)
bash skills/viewer/scripts/start.sh <urdf> . --trajectory output/simdemo/simulation/r2d2.trajectory.json
#    playwright headless 打开 URL → 点播放/scrub → 截图 → AI 看图确认关节随时间变化
# 回归
$VENV -m pytest skills/viewer/tests skills/simulation/tests -m smoke -q
```

**通过判据**:cad 引擎加载 URDF 后出现「仿真回放」时间轴;拖动/播放时**关节角随 `trajectory.json` 改变**
(headless 两帧截图姿态不同);simulation + viewer smoke 全绿。

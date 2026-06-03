---
name: srdf
description: |
  SRDF (Semantic Robot Description Format) authoring for MoveIt2.
  Use when defining or editing planning groups, group_state named poses,
  end-effectors, virtual joints, passive joints, or disable_collisions
  matrices for an existing URDF — i.e. when MoveIt2 / OMPL motion planning,
  IK groups, allowed-collision matrix, or moveit_setup_assistant artifacts
  are involved. Use the urdf skill for kinematic / link / joint definition
  itself; use cad-viewer for joint sliders / 3D preview; use sdf for
  Gazebo world physics (independent path).
  关键词:SRDF, MoveIt, MoveIt2, planning group, group_state, 规划组,
  collision matrix, disable_collisions, 碰撞矩阵, 虚位姿, named pose,
  setup_assistant, end effector, virtual joint, passive joint。
---

# SRDF — MoveIt2 语义层

> SRDF 不是 URDF 的替代,是它的语义补丁。URDF 描述「机器人长什么样、怎么动」,
> SRDF 描述「为了规划运动,我们怎么把它分组、哪些位姿叫得出名字、哪些碰撞可以忽略」。

---

## 核心规则

1. **URDF 先稳**:SRDF 引用 URDF 中的 `link` / `joint` 名字,URDF 改名 → SRDF 同步改;
   URDF 还在改尺寸 / 关节顺序 → 不要急着写 SRDF。
2. **三大支柱**:`<group>`(规划组)、`<group_state>`(命名虚位姿)、`<disable_collisions>`
   (碰撞白名单)。其它元素 (`virtual_joint` / `end_effector` / `passive_joint`) 按需补。
3. **disable_collisions 只关四类**:
   ① `Adjacent` 相邻链接(URDF joint 直连)、② `Never` 几何上永远不可能碰、
   ③ `Always` 在所有姿态下都重叠(冗余几何)、④ `Default` 在 home 位姿下重叠。
   不要为了消 setup_assistant 红字盲关 — 删掉一对真实存在的碰撞,planner 会
   生成穿模轨迹。
4. **virtual_joint 给移动底座**:四足 / 移动机器人必须有 `virtual_joint` 把 `world`
   连到 `base_link`(`type="floating"`),否则 MoveIt 把整机当固定基座,IK / 规划群组
   全部失效。
5. **group_state 用于"调出来一个姿态"**:home / stand / sit 之类。值是关节角,
   不是 link 位姿。每个 group_state 必须显式列出该 group 内**所有**关节。
6. **链 (chain) vs 关节集 (joints)**:腿 / 臂这种串联结构用 `<chain base_link tip_link>`,
   非串联(整机、双手协同)用 `<joints>` 列举或 `<group>` 嵌套。
7. **生成顺序**:authoring 先手写关键骨架(group + group_state) → moveit_setup_assistant
   交互式补 disable_collisions(几何采样需要它) → 回头人工审 Always 类(防过松)。
8. **跨子技能边界**:URDF 是 SRDF 的**唯一上游**;不要让 SRDF 直接读 STEP / 关节
   原始数据,统一通过 URDF 的 link / joint 名字面对。

---

## SRDF vs URDF 一句话对照

| 维度 | URDF | SRDF |
|---|---|---|
| 关心 | 几何 / 惯量 / 关节物理参数 | 语义分组 / 命名位姿 / 碰撞白名单 |
| 文件根 | `<robot name>` | `<robot name>` (同名,SRDF 必须与 URDF 同名) |
| 引用关系 | 自闭包 | **引用** URDF 中的 link / joint 名字 |
| 谁消费 | RViz / robot_state_publisher / Gazebo / MoveIt | **MoveIt2 主用**(也用于 setup_assistant) |
| 改动频率 | 跟随 CAD 反求 / 标定 | 跟随规划需求(加新组、调命名位姿) |

---

## 工作流

1. **确认 URDF 已稳定**:调用 `urdf` 子技能产出 `*.urdf`,过 generation-time validation。
2. **盘点规划组**:从消费场景倒推 — 「我要让单条腿走轨迹规划吗?」「整机姿态控制?」。
   四足典型:每条腿独立 group(`<chain>`) + 整机 group(`<group><group .../></group>`
   嵌套或 `<joints>`)。详见 `references/planning-groups-quadruped.md`。
3. **定 group_state**:每个 group 至少一个 home。整机推荐 home / stand / sit 三档。
4. **声明 virtual_joint**:`world → base_link, type=floating`(移动机器人)。
5. **手写 disable_collisions 骨架**:Adjacent 全列。Never 类按结构常识列(同腿上下件
   不会与对侧腿撞)。
6. **补全 disable_collisions**:用 `moveit_setup_assistant` GUI 跑 self-collision
   sampling(默认 10000 采样),把 Default / Always 拣出来。
7. **回审**:`reason="Always"` 的对子要二次确认(可能是几何 / 惯量错误而不是真冗余)。
8. **下游 handoff**:产物 `<robot>.srdf` → MoveIt2 config package(`<robot>_moveit_config/`)
   或直接喂给 `move_group` 节点。

---

## 命令

本子技能当前**不提供独立 launcher**(SRDF 通常由 `moveit_setup_assistant` 交互式
生成或手工撰写,不像 URDF 有 Python 生成函数)。可走两条路:

### A. 交互式生成(推荐首版)

```bash
# 假设已 source ROS 2 / MoveIt2 环境
ros2 launch moveit_setup_assistant setup_assistant.launch.py
# 在 GUI 里 Load URDF → Self-Collisions → Planning Groups → Robot Poses → Generate
```

setup_assistant 会输出 `<robot>_moveit_config/` 整个 ROS 包,SRDF 在 `config/<robot>.srdf`。
把它复制回项目工作区:`~/work/<project>/domains/control/output/<task>/<robot>.srdf`。

### B. 手工撰写(版本受控,推荐增量改)

参照 `references/srdf-spec-cheatsheet.md` 直接写 XML;改动走 PR review。
样本:`tests/fixtures/quadruped_min.srdf`(最小可加载四足 SRDF)。

### 验证(无 ROS 环境也能跑)

```bash
# XML well-formed
python -c "import xml.etree.ElementTree as ET; ET.parse('out.srdf')"
# 必备元素自检 (本子技能 smoke)
pytest skills/srdf/tests/ -k smoke
```

完整离线验证(需 MoveIt2 安装):

```bash
ros2 run moveit_ros_planning moveit_planning_test --ros-args \
  -p robot_description:=/path/to/robot.urdf \
  -p robot_description_semantic:=/path/to/robot.srdf
```

---

## 四足规划组速记(详见 references/planning-groups-quadruped.md)

```xml
<robot name="quadruped">
  <virtual_joint name="floating_base" type="floating"
                 parent_frame="world" child_link="base_link"/>

  <!-- 每条腿一个 chain group -->
  <group name="front_left_leg">
    <chain base_link="base_link" tip_link="fl_foot"/>
  </group>
  <!-- fr / rl / rr 同构 -->

  <!-- 整机 = 四条腿组合 -->
  <group name="all_legs">
    <group name="front_left_leg"/>
    <group name="front_right_leg"/>
    <group name="rear_left_leg"/>
    <group name="rear_right_leg"/>
  </group>

  <!-- 命名虚位姿 -->
  <group_state name="home"  group="all_legs"> ...12 个关节角... </group_state>
  <group_state name="stand" group="all_legs"> ...站立姿态... </group_state>
  <group_state name="sit"   group="all_legs"> ...坐姿... </group_state>

  <!-- 碰撞白名单(Adjacent 必列) -->
  <disable_collisions link1="base_link" link2="fl_hip" reason="Adjacent"/>
  <!-- ... -->
</robot>
```

---

## URDF 上游 handoff

- 入口:`output/<task>/<robot>.urdf`(由 urdf 子技能产出)。
- 严格依赖 URDF 中的命名:link / joint 任一改名,SRDF 全文搜索同步改;否则 MoveIt2
  在 `loadRobotModel()` 阶段直接报 `Joint X not found in robot model`。
- 路径与 schema 协议:父级 `shared/handoff-protocols.md` 「常见 4 条」第 2 条之延伸
  (本子技能登记于父 SKILL「跨子技能依赖图」: urdf → srdf)。
- 命名位姿的关节角来源:URDF joint limits 里的 lower / upper(home 取 0 或 limits
  中点),实际站姿 / 坐姿数值由机械工程师按运动学几何标定后回填。

## cad-viewer / MoveIt2 下游 handoff

- **cad-viewer**:URDF 已走 viewer cad 引擎可视化(urdf-loader + 关节滑块)。SRDF
  **不参与** viewer 渲染,但 viewer 滑块拉出来的关节值可直接复制到 group_state。
- **MoveIt2 server**:产物 `<robot>.srdf` + `<robot>.urdf` + kinematics.yaml + ompl_planning.yaml
  → `move_group` 节点。父级编排顺序:urdf 出 .urdf → srdf 出 .srdf → MoveIt2 config
  包打包 → cad-viewer / RViz 可视化校验。
- 不要让 SRDF 子技能直接调 cad-viewer scripts,跨子技能只走 `shared/handoff-protocols.md`
  规定的文件接口。

---

## 不做什么

- ❌ 不在 SRDF 里改几何 / 惯量 / 关节限位(那是 URDF 的事)
- ❌ 不把 SRDF 当配置中心存 PID / 速度限值(走 ros2_control / kinematics.yaml)
- ❌ 不为消 setup_assistant 警告盲关 disable_collisions
- ❌ 不引用 URDF 之外的 link / joint 名(必须存在于上游 .urdf)
- ❌ 不直接读 cad-viewer / mechanical 的 references/(跨子技能红线)

---

## References

- SRDF 元素速查:`references/srdf-spec-cheatsheet.md`
- 四足规划组模板:`references/planning-groups-quadruped.md`
- 跨子技能 handoff 全协议:父级 `shared/handoff-protocols.md`
- 上游 URDF skill:`../urdf/SKILL.md`
- 下游可视化:`../viewer/SKILL.md`

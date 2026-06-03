# 四足机器狗 SRDF 规划组模板

> 适用对象:典型 12-DoF 四足(每条腿 hip_yaw + hip_pitch + knee_pitch),`base_link`
> 居中,腿命名约定 `fl/fr/rl/rr`(front-left / front-right / rear-left / rear-right)。
> 如果项目用别的命名(如 `lf/rf/lh/rh`),全文搜替换即可。

---

## URDF 命名约定(本模板假设)

```
base_link
 ├── fl_hip_yaw_link  ← fl_hip_yaw_joint
 │    └── fl_hip_pitch_link  ← fl_hip_pitch_joint
 │         └── fl_knee_link  ← fl_knee_joint
 │              └── fl_foot_link  (虚拟末端 link,fixed joint)
 ├── fr_*  (同结构)
 ├── rl_*
 └── rr_*
```

每条腿 3 个驱动关节 + 末端足 link(`*_foot_link` 通常是 fixed joint 末端,只为
IK tip 引用,不参与电机驱动)。

---

## 规划组拓扑

四足主要规划场景:① 单腿轨迹规划(摆动腿落足点)、② 整机姿态控制(站起 / 卧倒)、
③ 单腿 + base 协同(楼梯抬腿配合躯干俯仰)。对应规划组:

| group 名 | 类型 | 关节数 | 用途 |
|---|---|---|---|
| `front_left_leg`  | chain | 3 | 单腿摆动规划 / IK 落足 |
| `front_right_leg` | chain | 3 | 同上 |
| `rear_left_leg`   | chain | 3 | 同上 |
| `rear_right_leg`  | chain | 3 | 同上 |
| `all_legs`        | 嵌套 group | 12 | 整机姿态(home/stand/sit) |
| `front_legs`     | 嵌套 group | 6 | 双前腿协同(可选) |
| `rear_legs`      | 嵌套 group | 6 | 双后腿协同(可选) |

> `all_legs` 是命名虚位姿(home/stand/sit)的归属组;`front_legs` / `rear_legs` 仅在
> 项目有"前腿挥动 / 后腿坐姿"独立动作需求时加,否则**不加**(MoveIt 规划组多了反而
> 干扰 OMPL 采样)。

---

## 规划组 XML

```xml
<!-- 单腿:base_link → tip_link 之间所有非 fixed 关节自动入链 -->
<group name="front_left_leg">
  <chain base_link="base_link" tip_link="fl_foot_link"/>
</group>
<group name="front_right_leg">
  <chain base_link="base_link" tip_link="fr_foot_link"/>
</group>
<group name="rear_left_leg">
  <chain base_link="base_link" tip_link="rl_foot_link"/>
</group>
<group name="rear_right_leg">
  <chain base_link="base_link" tip_link="rr_foot_link"/>
</group>

<!-- 整机:四条腿合并,12 DoF -->
<group name="all_legs">
  <group name="front_left_leg"/>
  <group name="front_right_leg"/>
  <group name="rear_left_leg"/>
  <group name="rear_right_leg"/>
</group>
```

---

## 命名虚位姿(group_state)

四足典型三档:home(零位)、stand(站立)、sit(坐 / 卧)。所有 group_state 必须
**显式列出 12 个关节**。值是弧度(URDF revolute 关节的 lower / upper 限值是弧度)。

### home — 全部归零

```xml
<group_state name="home" group="all_legs">
  <joint name="fl_hip_yaw_joint"   value="0"/>
  <joint name="fl_hip_pitch_joint" value="0"/>
  <joint name="fl_knee_joint"      value="0"/>
  <joint name="fr_hip_yaw_joint"   value="0"/>
  <joint name="fr_hip_pitch_joint" value="0"/>
  <joint name="fr_knee_joint"      value="0"/>
  <joint name="rl_hip_yaw_joint"   value="0"/>
  <joint name="rl_hip_pitch_joint" value="0"/>
  <joint name="rl_knee_joint"      value="0"/>
  <joint name="rr_hip_yaw_joint"   value="0"/>
  <joint name="rr_hip_pitch_joint" value="0"/>
  <joint name="rr_knee_joint"      value="0"/>
</group_state>
```

> home 通常**不**是真实可站立姿态,只是「关节零位、便于校对几何」的诊断位。

### stand — 站立(典型 Mini Cheetah 风格)

机械师标定 hip_pitch / knee 的几何关系后回填。模板示意值(具体数值按你机器狗的
肢长 / 关节限值校准):

```xml
<group_state name="stand" group="all_legs">
  <joint name="fl_hip_yaw_joint"   value="0.0"/>
  <joint name="fl_hip_pitch_joint" value="-0.785"/>  <!-- -45° -->
  <joint name="fl_knee_joint"      value="1.571"/>   <!-- +90° -->
  <joint name="fr_hip_yaw_joint"   value="0.0"/>
  <joint name="fr_hip_pitch_joint" value="-0.785"/>
  <joint name="fr_knee_joint"      value="1.571"/>
  <joint name="rl_hip_yaw_joint"   value="0.0"/>
  <joint name="rl_hip_pitch_joint" value="-0.785"/>
  <joint name="rl_knee_joint"      value="1.571"/>
  <joint name="rr_hip_yaw_joint"   value="0.0"/>
  <joint name="rr_hip_pitch_joint" value="-0.785"/>
  <joint name="rr_knee_joint"      value="1.571"/>
</group_state>
```

> hip_pitch 负 45° + knee 正 90° = 大腿前伸 + 小腿垂直收回,典型站立几何。
> sign 取决于 URDF 中 `<axis>` 方向,**必须**对照 URDF 原始定义验证(同 design ledger
> 一起维护)。

### sit — 后腿弯曲坐姿

```xml
<group_state name="sit" group="all_legs">
  <joint name="fl_hip_yaw_joint"   value="0.0"/>
  <joint name="fl_hip_pitch_joint" value="-0.785"/>
  <joint name="fl_knee_joint"      value="1.571"/>
  <joint name="fr_hip_yaw_joint"   value="0.0"/>
  <joint name="fr_hip_pitch_joint" value="-0.785"/>
  <joint name="fr_knee_joint"      value="1.571"/>
  <joint name="rl_hip_yaw_joint"   value="0.0"/>
  <joint name="rl_hip_pitch_joint" value="-1.571"/> <!-- 后腿大幅蹲下 -->
  <joint name="rl_knee_joint"      value="2.094"/>  <!-- ~120° 收紧 -->
  <joint name="rr_hip_yaw_joint"   value="0.0"/>
  <joint name="rr_hip_pitch_joint" value="-1.571"/>
  <joint name="rr_knee_joint"      value="2.094"/>
</group_state>
```

---

## 虚拟关节

四足是浮动基座,**必填**:

```xml
<virtual_joint name="floating_base" type="floating"
               parent_frame="world" child_link="base_link"/>
```

`parent_frame` 也可用 `odom` / `map`,取决于 SLAM / 定位栈。这里 `world` 是 Gazebo
仿真和 RViz 的默认根。

---

## 碰撞矩阵(disable_collisions)策略

四足腿对称、关节多,disable_collisions 通常占 SRDF 80%+ 的行。**不要全手写**,
用 setup_assistant 跑采样。原则:

1. **Adjacent 必关(12 对左右)** — URDF joint 父子直连,几何上靠在一起,不关会
   永远 self-collide。
2. **同腿上下件互不撞**(`fl_hip_yaw ↔ fl_knee` 这种隔一节的) — Never 类,可关。
3. **对侧腿之间** — 看几何;若整机 stance width 足够,前左与前右、前左与后左通常
   永不接触,可关 Never;但如果有交叉步态(diagonal trot 中身体扭转较大),保留
   检测。
4. **base_link ↔ 所有 hip_yaw_link** — Adjacent,关。
5. **base_link ↔ 远端足** — 一般 Never(几何上够不到),关。
6. **足 ↔ 足** — 慎重。窄底盘机器狗(Mini Pupper 之类)的足在某些步态会靠近,
   建议**保留检测**,planner 自己规避。

### 必须关的 Adjacent 列表(12 对)

```xml
<!-- base 到 4 个 hip_yaw -->
<disable_collisions link1="base_link" link2="fl_hip_yaw_link" reason="Adjacent"/>
<disable_collisions link1="base_link" link2="fr_hip_yaw_link" reason="Adjacent"/>
<disable_collisions link1="base_link" link2="rl_hip_yaw_link" reason="Adjacent"/>
<disable_collisions link1="base_link" link2="rr_hip_yaw_link" reason="Adjacent"/>

<!-- 每条腿的 yaw → pitch、pitch → knee、knee → foot -->
<disable_collisions link1="fl_hip_yaw_link"   link2="fl_hip_pitch_link" reason="Adjacent"/>
<disable_collisions link1="fl_hip_pitch_link" link2="fl_knee_link"      reason="Adjacent"/>
<disable_collisions link1="fl_knee_link"      link2="fl_foot_link"      reason="Adjacent"/>
<!-- fr / rl / rr 同结构,共 12 对 Adjacent -->
```

### Never 类(对侧腿、远端组合,典型 30+ 对)

由 setup_assistant 采样填充,人工不写。

---

## 完整最小 SRDF 示例

见 `../tests/fixtures/quadruped_min.srdf`(可被 `xml.etree.ElementTree.parse()` 解析,
通过 SKILL.md 「验证」章节列出的离线检查)。该文件用同样的 link / joint 命名约定,
可作为 setup_assistant 「Load existing SRDF」的初始模板。

---

## 与 URDF design ledger 的耦合

每加 / 改一个 group_state 数值,都要在上游 URDF 的设计 ledger 里登记一条 "虚位姿
关节角来源"(测量? 几何推导? CAD 截图标定?),否则数值会随时间漂走没人记得为什么。
ledger 模板:`../../urdf/references/design-ledger.md` § Joint Ledger / Assumption Ledger。

---

## 相关文档

- SRDF 元素速查:`./srdf-spec-cheatsheet.md`
- 上游 URDF skill:`../../urdf/SKILL.md`
- 整机仿真(Gazebo):`../../sdf/SKILL.md`(独立路径,不依赖 SRDF)
- 关节滑块可视化:`../../viewer/SKILL.md`

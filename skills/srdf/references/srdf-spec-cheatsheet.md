# SRDF 元素速查表

> SRDF 是 MoveIt 自有格式(不是 ROS 通用 URDF spec),官方权威文档:
> [moveit.ai · SRDF tutorial](https://moveit.ai/documentation/source_code/) 与 ROS wiki
> [`srdf` package](http://wiki.ros.org/srdf)。本表只覆盖与 MoveIt2 motion planning
> 相关的元素;`disable_collisions` 与 `group_state` 是日常增量改动最频繁的两个。

## 文件骨架

```xml
<?xml version="1.0"?>
<robot name="ROBOT_NAME">
  <!-- 必须与 URDF 同名,否则 MoveIt 加载报错 -->
  ... 各元素 ...
</robot>
```

`<robot>` 是唯一根元素。MoveIt2 用 `robot_description_semantic` ROS 参数传它,
配套 `robot_description`(URDF)成对出现。

---

## 元素清单

### 1. `<group>` — 规划组

定义一组关节作为 MoveIt 的最小规划单位。三种声明方式互斥(同一 group 内只用一种):

```xml
<!-- A. 串联链:base_link 到 tip_link 之间所有关节 -->
<group name="manipulator">
  <chain base_link="shoulder_link" tip_link="wrist_link"/>
</group>

<!-- B. 关节列表:显式列举,适合非串联或跳过中间关节 -->
<group name="hand">
  <joint name="finger1_joint"/>
  <joint name="finger2_joint"/>
</group>

<!-- C. 子组聚合:把已有 group 拼成大 group -->
<group name="whole_arm">
  <group name="manipulator"/>
  <group name="hand"/>
</group>

<!-- D. link 列举(少见):只关心几何,不规划运动 -->
<group name="visual_only">
  <link name="cosmetic_shroud"/>
</group>
```

属性:`name`(必填,group 唯一 id)。

> 一个 group 可以同时含 `<chain>` + `<joint>`(MoveIt 会并集),但混用容易语义混乱,
> 建议**只用一种**。

### 2. `<group_state>` — 命名虚位姿

给一个 group 起一个姿态别名,值是关节角(弧度,prismatic 是米)。

```xml
<group_state name="home" group="manipulator">
  <joint name="shoulder_pan"  value="0"/>
  <joint name="shoulder_lift" value="-1.57"/>
  <joint name="elbow"         value="0"/>
  <joint name="wrist_1"       value="0"/>
  <joint name="wrist_2"       value="0"/>
  <joint name="wrist_3"       value="0"/>
</group_state>
```

属性:`name`、`group`(都必填)。

要点:
- 必须显式列出 group 内**所有**关节,缺一个 MoveIt 警告 "incomplete group state"。
- 多自由度 floating / planar virtual_joint 用 `<joint name="..." value="x y z qx qy qz qw"/>`
  之类多值字符串(MoveIt 解析空格分隔)。

### 3. `<end_effector>` — 末端执行器

把一个 group 标记为另一个 group 的末端,方便 `set_end_effector_link()` API 调用。

```xml
<end_effector name="gripper" parent_link="wrist_link"
              group="hand" parent_group="manipulator"/>
```

属性:`name`、`parent_link`(挂在哪个 link 上)、`group`(末端自身 group)、
`parent_group`(主臂 group,选填)。

### 4. `<virtual_joint>` — 虚拟关节

把机器人 base_link 连到 world / map / odom 等参考系。**移动机器人必填**。

```xml
<!-- 移动底座(四足、AGV、漂浮无人机):floating 6-DoF -->
<virtual_joint name="floating_base" type="floating"
               parent_frame="world" child_link="base_link"/>

<!-- 平面移动(差速 / 全向 AGV):planar 3-DoF (x, y, yaw) -->
<virtual_joint name="planar_base" type="planar"
               parent_frame="odom" child_link="base_link"/>

<!-- 固定基座(机械臂):fixed 0-DoF -->
<virtual_joint name="fixed_base" type="fixed"
               parent_frame="world" child_link="base_link"/>
```

`type` ∈ `{fixed, floating, planar}`。注意:URDF 只能描述固定基座,移动底座的
"漂浮"必须在 SRDF 里通过 virtual_joint 表达。

### 5. `<passive_joint>` — 被动关节

声明某关节由物理结构带动而不是执行器驱动,MoveIt 不会规划它,但碰撞检测仍生效。

```xml
<passive_joint name="finger_passive_1"/>
```

典型场景:平行四边形连杆、欠驱动手指。

### 6. `<disable_collisions>` — 碰撞白名单

成对关闭 self-collision check。reason 仅供人读,MoveIt 不解析。

```xml
<disable_collisions link1="A" link2="B" reason="Adjacent"/>
<disable_collisions link1="A" link2="C" reason="Never"/>
<disable_collisions link1="A" link2="D" reason="Default"/>
<disable_collisions link1="A" link2="E" reason="Always"/>
<disable_collisions link1="A" link2="F" reason="User"/>
```

reason 取值约定(setup_assistant 自动填):
| reason | 含义 | 是否安全关 |
|---|---|---|
| `Adjacent` | URDF joint 直连父子 link | ✅ 必须关(否则永远 self-collide) |
| `Never` | 采样 N 次从未碰过 | ✅ 一般安全(N 默认 10000) |
| `Default` | home 位姿下重叠 | ⚠️ 检查是不是 home 写错了 |
| `Always` | 任意采样姿态都重叠 | 🛑 几乎一定是几何 / 惯量错误,先修 URDF |
| `User` | 人工标 | — |

---

## 元素出现顺序

SRDF 没有强 schema 顺序,但社区惯例:
1. `<virtual_joint>`
2. `<group>`(从基础到组合,串联 → 嵌套)
3. `<group_state>`
4. `<end_effector>`
5. `<passive_joint>`
6. `<disable_collisions>`(常常占文件 80%+ 的行数)

---

## 常见错误

| 症状 | 根因 |
|---|---|
| `Joint X not found in robot model` | URDF 改名后 SRDF 没同步;或 SRDF 引用了 URDF 没有的 joint |
| `No kinematics solver` | `kinematics.yaml` 没配该 group 的 solver,不是 SRDF 的问题但常被误归 |
| `group state has no value for joint Y` | group_state 漏列了 group 内某个关节 |
| 规划器一直找不到无碰撞路径 | `disable_collisions` 关得太少(没关 Adjacent)或太多(把真实碰撞关了) |
| 移动机器人 IK 爆 nan | 漏写 `<virtual_joint type="floating">` |

---

## 与 URDF 的字段对照

| SRDF 元素 / 属性 | 必须对应 URDF 中的 |
|---|---|
| `<group><chain base_link tip_link>` | URDF 中可达的串联 link 链 |
| `<group><joint name>` | URDF `<joint name>` |
| `<group_state><joint name>` | URDF `<joint name>` |
| `<end_effector parent_link>` | URDF `<link name>` |
| `<virtual_joint child_link>` | URDF root `<link>`(通常 base_link) |
| `<disable_collisions link1 link2>` | URDF `<link name>` |

---

## 相关文档

- 四足规划组实战模板:`./planning-groups-quadruped.md`
- 上游 URDF 字段语义:`../../urdf/references/frame-semantics.md`
- 跨子技能 handoff:父级 `shared/handoff-protocols.md`

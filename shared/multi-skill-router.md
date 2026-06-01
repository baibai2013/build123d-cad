# 父级路由依据 (multi-skill-router)

父 `SKILL.md` 两层路由的判据。父级**不读**子技能完整内容，只按关键词分派，再 `Read skills/<name>/SKILL.md`。

## 关键词 → 子技能

| 子技能 | 触发关键词 | 状态 |
|---|---|---|
| mechanical | CAD、建模、装配、零件、外壳、支架、齿轮、反求、仿真(FK/IK/步态)、STEP/STL | 根基 |
| viewer | 预览、网页查看、分享链接、headless、看一下模型/PCB/原理图/波形 | P0 |
| urdf | URDF、机器人描述、link/joint、导出 ROS | P0 |
| srdf | MoveIt、规划组、planning group、碰撞矩阵 | P1 |
| sdf | Gazebo、SDF、仿真世界 | P1 |
| gcode | 切片、FDM、G-code 预检、打印时间估算 | P1 |
| sendcutsend | 激光切割、钣金、报价、SendCutSend | P1 |
| parts-catalog | 找现成零件、在线 STEP、标准件下载 | P0 |
| bambu-labs | Bambu 打印机、上传打印、AMS | P2 |
| pcb (WIP) | PCB、EDA、Gerber、DRC、KiCad | P3 占位 |
| electronics-bom (WIP) | 电子 BOM、元件选型、JLCPCB/Octopart | P3 占位 |

## 路由规则

1. 收到需求 → 按上表关键词匹配子技能（可命中多个 → 主子技能优先，其余走 handoff）。
2. `Read skills/<name>/SKILL.md` 后再开始答题；不要凭记忆。
3. 跨子技能数据交换走 `shared/handoff-protocols.md`，不直接互引 references。
4. 跨子技能流程（机械→viewer→urdf）由父级编排，实施落到各子技能。

## 多命中消歧

- "做个外壳并预览" → mechanical(主) + viewer(handoff)
- "把这个机器人导成 URDF 并看关节" → urdf(主) + viewer(handoff)
- "找个 608 轴承装进去" → parts-catalog(主) + mechanical(handoff)

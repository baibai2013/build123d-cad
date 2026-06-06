# 父级路由依据 (multi-skill-router)

父 `SKILL.md` 两层路由的判据。父级**不读**子技能完整内容，只按关键词分派，再 `Read skills/<name>/SKILL.md`。

## 关键词 → 子技能

> 状态：✅ 已落地可用 / 🟡 占位待开张。

| 子技能 | 触发关键词 | 状态 |
|---|---|---|
| mechanical | CAD、建模、装配、零件、外壳、支架、齿轮、反求、仿真(FK/IK/步态)、STEP/STL | ✅ 根基 |
| viewer | 预览、网页查看、分享链接、headless、看一下模型/PCB/原理图/波形 | ✅ P0 |
| urdf | URDF、机器人描述、link/joint、导出 ROS | ✅ P0 |
| srdf | MoveIt、规划组、planning group、碰撞矩阵、自碰撞 | ✅ P1 |
| sdf | Gazebo、SDF、仿真世界 | ✅ P1 |
| gcode | 切片、FDM、G-code 预检、打印时间估算、悬垂/overhang | ✅ P1 |
| sendcutsend | 激光切割、钣金、报价、SendCutSend、DXF 展开、折弯 | ✅ P1 |
| parts-catalog | 找现成零件、在线 STEP、标准件下载、轴承/螺丝/舵机型号 | ✅ P0 |
| bambu-labs | Bambu 打印机、上传打印、AMS | 🟡 P2 |
| pcb | PCB、原理图、tscircuit、代码写PCB、TSX、Gerber、出件、嘉立创、JLCPCB、下单打板、PCB 3D、DFM、EDA | ✅ P1(tscircuit) |
| electronics-bom (WIP) | 电子 BOM、元件选型、JLCPCB/Octopart | 🟡 P3 占位 |

## 路由规则

1. 收到需求 → 按上表关键词匹配子技能（可命中多个 → 主子技能优先，其余走 handoff）。
2. `Read skills/<name>/SKILL.md` 后再开始答题；不要凭记忆。
3. 跨子技能数据交换走 `shared/handoff-protocols.md`，不直接互引 references。
4. 跨子技能流程（机械→viewer→urdf）由父级编排，实施落到各子技能。

## 多命中消歧

- "做个外壳并预览" → mechanical(主) + viewer(handoff)
- "把这个机器人导成 URDF 并看关节" → urdf(主) + viewer(handoff)
- "找个 608 轴承装进去" → parts-catalog(主) + mechanical(handoff)
- "给这个机器人配 MoveIt 规划组 / 自碰撞矩阵" → urdf(前置) + srdf(主)
- "放进 Gazebo 仿真世界跑一下" → urdf(前置) + sdf(主)
- "这件能 3D 打印吗 / 估下打印时间" → mechanical(前置 STEP) + gcode(主)
- "这块钣金激光切多少钱" → mechanical(前置 STEP) + sendcutsend(主)
- "用代码写块板子并发嘉立创打样" → pcb(主,tscircuit 端到端) + viewer(预览 handoff)

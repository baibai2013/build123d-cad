<!-- 父级 SKILL.md 草稿。P0-2 迁移 mechanical 完成后，再替换仓库根的 SKILL.md。
     现在不替换：根 SKILL.md(1535行) 仍是生效的机械技能，提前替换会让技能失效。 -->

# build123d-cad — 硬件设计 Super Skill

一次安装、模块化的硬件设计技能集合。父级只做路由，详细能力在各子技能。

## 子技能集合

| 子技能 | 触发场景 | 路径 |
|---|---|---|
| mechanical | CAD 建模 / 装配 / 仿真 / 反求 | skills/mechanical/SKILL.md |
| viewer | 网页预览 / 分享链接 / headless | skills/viewer/SKILL.md |
| urdf | 机器人 URDF 描述 | skills/urdf/SKILL.md |
| srdf | MoveIt 规划组 | skills/srdf/SKILL.md |
| sdf | Gazebo 仿真世界 | skills/sdf/SKILL.md |
| gcode | FDM 切片预检 | skills/gcode/SKILL.md |
| sendcutsend | 激光切割报价 | skills/sendcutsend/SKILL.md |
| parts-catalog | 找现成 STEP 零件 | skills/parts-catalog/SKILL.md |
| bambu-labs | Bambu 打印机 | skills/bambu-labs/SKILL.md |
| pcb (WIP) | PCB / EDA / DRC | skills/pcb/SKILL.md |
| electronics-bom (WIP) | 电子 BOM | skills/electronics-bom/SKILL.md |

## 路由规则

1. 收到需求 → 按关键词匹配子技能（判据见 shared/multi-skill-router.md）。
2. `Read skills/<name>/SKILL.md` 后再开始答题，不要凭记忆。
3. 子技能之间数据交换走 shared/handoff-protocols.md（文件接口，不直接互引 references）。
4. 跨子技能流程（机械→viewer→urdf）由父级编排，实施落到子技能。

## 角色规则（7 条核心，详细在 mechanical/SKILL.md）

1. 代码优先  2. 参数化  3. 表达设计意图  4. 不编造 API
5. STEP 优先  6. 必须导出  7. 跨子技能时主动 handoff

## 跨子技能标准 handoff（常见 4 条）

- mechanical 出 STEP → viewer 显示 / urdf 转换 / gcode·sendcutsend 制造预检
- 详见 shared/handoff-protocols.md

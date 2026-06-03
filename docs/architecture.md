# 架构：硬件设计 Super Skill

## 形态

一个**父 super skill** 包含 **N 个子技能**（monorepo），一次安装、模块化、每个子技能可独立 `pytest`。

```
build123d-cad/
├── SKILL.md          # 父级路由（≤220 行）：关键词 → 子技能
├── skills/<name>/    # 每个子技能：SKILL.md + references/ + scripts/ + tests/
├── shared/           # 跨子技能：router / handoff / dependencies / test-utils
├── tests/            # 父级跨子技能集成测试
└── docs/             # 本架构说明 + 加新子技能指南
```

## 两层路由

1. 父 `SKILL.md` 按关键词命中子技能（不读子技能完整内容）。
2. `Read skills/<name>/SKILL.md` → 进子技能详细 references。

判据见 `shared/multi-skill-router.md`。

## 子技能自治原则

- 每个子技能至少有 `SKILL.md` + `README.md` + (`references/` 或 `scripts/` 或 `tests/`)。
- 子技能**不直接引用**其他子技能的 references（避免耦合）。
- 跨子技能调用走 `shared/` 协议（文件标准接口，非函数调用）。

## 测试分层

```bash
cd skills/viewer && pytest tests/     # 单子技能快速反馈
pytest                                # 整 super skill 回归
pytest tests/test_e2e_design_to_print.py  # 跨子技能集成
```

conftest 分两层：子技能级 fixture（`skills/<name>/tests/conftest.py`）+ 父级跨子技能 fixture（`tests/conftest.py`）。

## 阶段

| 阶段 | 范围 | 状态 |
|---|---|---|
| P0 | 骨架 + mechanical 迁移 + viewer/urdf/parts-catalog 复刻 + tests 骨架 | ✅ 完成（shared docs 补全收尾中） |
| P1 | srdf/sdf/gcode/sendcutsend + 数据源/代码源补齐 | ✅ 子技能全落地；agent-eval CI 注册待外部解阻 |
| P2 | bambu-labs / Playbook 治理 | 按需触发 |
| P3 | 电子域：pcb/eda/drc（用户给第一个 PCB 项目时启动） | 🟡 占位，待 Gate 3 |

## 关键决策

- 子技能是**目录**不是独立仓库 → 不用 git submodule。
- 暂留名 `build123d-cad`，多域成熟再议改名。
- viewer `dist/` 13M 直接 commit（git 限内，不用 LFS）。
- viewer 用 node 直跑 `server.mjs`，不 `npm install`。

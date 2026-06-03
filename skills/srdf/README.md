# srdf — 开发者说明

MoveIt2 语义层(规划组、命名虚位姿、碰撞白名单)。
对外能力清单与工作流见 [`SKILL.md`](./SKILL.md)。

## 目录

```
srdf/
├── SKILL.md                                # 对 AI / 用户的能力描述(≤250 行)
├── README.md                               # 本文件,开发者向
├── references/
│   ├── srdf-spec-cheatsheet.md             # SRDF XML 元素速查
│   └── planning-groups-quadruped.md        # 四足规划组实战模板
├── scripts/                                # 暂无 launcher;SRDF 走 setup_assistant 或手写
└── tests/
    ├── conftest.py                         # subskill_root fixture
    ├── test_smoke.py                       # 骨架 + fixture 校验
    └── fixtures/
        └── quadruped_min.srdf              # 最小可加载四足 SRDF
```

## 跑测试

```bash
cd /Users/liyijiang/.agents/skills/build123d-cad
pytest skills/srdf/tests/ -k smoke -v
```

## 离线 schema 校验(快速)

```bash
python3 -c "import xml.etree.ElementTree as ET; \
  ET.parse('skills/srdf/tests/fixtures/quadruped_min.srdf')"
```

## 与上下游

- 上游:`skills/urdf/`(SRDF 引用 URDF 中的 link / joint 名)
- 下游:MoveIt2 `move_group` 节点 / `moveit_setup_assistant`;`skills/viewer/` 仅消费 URDF
- 跨子技能契约:父级 `shared/handoff-protocols.md`、`shared/dependencies.md` (`urdf → srdf`)

## 维护

- 改 `references/` → 同步刷新 `SKILL.md` 「References」末节
- 加 launcher 脚本(若引入 `gen_srdf()` 生成器)→ 在 `scripts/` 下,SKILL.md「命令」补 C 选项

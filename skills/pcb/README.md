# pcb — 开发者说明

P3 占位子技能。落地触发条件 = 用户给出第一个 PCB 项目 + Gate 3 通过。

详见 [SKILL.md](SKILL.md) 与 [share/06](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md)。

## 当前状态

| 项 | 状态 |
|---|---|
| SKILL.md(占位 + 触发关键词 + 路线图) | ✅ |
| references/ | 空(P3 起填 KiCad CLI cheatsheet 等) |
| scripts/ | 空(P3 起填 new_project / sch_from_skidl / export_fab 等) |
| tests/ | placeholder smoke 一条 |
| benchmarks/ | 空(P3 起填出件耗时基准) |

## P3 启动后做什么

按 [06 §3.3a.1](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md#33a1-skillspcb--板级电气设计入口) 拆解:

```
skills/pcb/
├── SKILL.md          # 膨胀到 ≤ 350 行(模板见 06 §2.6a.1)
├── references/
│   ├── kicad-cli-cheatsheet.md
│   ├── skidl-quickstart.md
│   └── kicad-9-ipc-status.md
├── scripts/
│   ├── new_project.py
│   ├── sch_from_skidl.py
│   ├── export_fab.sh
│   ├── pcb_to_step.sh
│   ├── pcb_to_dxf.sh
│   └── batch_edit.py
├── tests/
│   ├── fixtures/minimal.kicad_pcb
│   ├── test_export_fab_smoke.py
│   ├── test_skidl_to_sch.py
│   └── test_pcb_to_step_handoff.py
└── benchmarks/
    └── b01_export_minimal.py
```

## P0 期间不要做什么

- ❌ 不要写真实 KiCad 集成(等 Gate 3)
- ❌ 不要拉 KiCad 9 toolchain 到 CI(P3 起再加 docker 镜像)
- ❌ 不要 commit `.kicad_pcb` 测试 fixture(P3 起再加,目前只 placeholder)

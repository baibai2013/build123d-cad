# pcb — 开发者说明(tscircuit 端到端造板)

板级电气设计子技能。**tech = tscircuit**(React/TS 写电路),端到端:
写 TSX → check/DRC → 统一预览 → DFM → 一键出件 → 嘉立创(经 jlcpcb-mcp)报价/下单。

详见 [SKILL.md](SKILL.md);开发方案与里程碑见
[`docs/pcb-tscircuit-dev-plan.md`](../../docs/pcb-tscircuit-dev-plan.md),
完整工作流见 [`docs/pcb-tscircuit-workflow.md`](../../docs/pcb-tscircuit-workflow.md)。

## 历史:为什么换掉 KiCad

旧栈 = KiCad-cli + skidl,硬伤是 **skidl 只能出网表 `.net`,layout 必须回 KiCad GUI 手工**,
不是代码端到端。tscircuit 一把 `tsci` 从 TSX 直接出带布局的板 + Gerber,真正闭环。
旧文件归档在 [`legacy-kicad/`](legacy-kicad/)(不参与路由/测试,需要 KiCad 兼容路线时可参考)。

## 当前状态(M1)

| 项 | 状态 |
|---|---|
| SKILL.md(tscircuit,实测语法) | ✅ ≤250 行 |
| references/(cli / syntax / workflow / jlcpcb-mcp / preview-3d) | ✅ 5 篇 |
| scripts/(new_board / check_all / export_fab / dfm_check / jlc_order + _tsci_env) | ✅ |
| tests/(结构 + dfm_check 单测 + fixtures) | ✅ 无需 tsci/key 即可 pytest |
| 工具链 | node20 + bun + `tscircuit`(bin=tsci);`bun add -g tscircuit` |
| 嘉立创 | `jlcpcb-mcp@0.3.3`;免 key 物料报价已验证,板级/下单代码就绪默认 disabled(决策①) |

## 里程碑进度

- M0 技术验证 ✅(`/tmp/pcb-spike/led-demo` 实跑通,见 dev-plan §4.1)
- M1 子技能骨架 + 裸板闭环 + DFM/一键导出 ✅(本目录)
- M2 统一预览(React 直引 RunFrame 进 viewer engine=tscircuit)✅(playwright headless 验证)
- M3 BOM+总价面板(jlcpcb-mcp 免 key,读 `<board>.bom.json` sidecar)✅
- M4 板级报价/下单(需 key,默认 disabled)— 待开
- M5 SMT 贴片 — 待开
- M6 布线算法 — 待开

## 跑测试

```bash
cd skills/pcb && pytest tests/        # 结构 + dfm_check 单测(无需 tsci/key)
```

## 本机真链路(需 bun+tsci)

```bash
bash scripts/new_board.sh demo && cd demo
# 写 index.circuit.tsx …
bash ../scripts/check_all.sh index.circuit.tsx
bash ../scripts/export_fab.sh index.circuit.tsx demo
python3 ../scripts/dfm_check.py output/demo/electrical/dist/index/circuit.json
```

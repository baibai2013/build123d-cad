# protocols/ 三大流程 Playbook 索引

本目录是 AI 执行期单一真实来源（SSOT）。SKILL.md 路由段只指向此目录，
所有流程细节（Step / Phase 定义、产出物契约、命令模板、失败模式）都在这里。

## 三个 Playbook

| 文件 | 适用场景 | Step/Phase 命名 |
|---|---|---|
| reference-product-playbook.md | 参考物建模（需求含产品型号） | R1 / R2 / R2.5 / R2.7 / R3 / R3.5 / R4 / R5 |
| single-part-playbook.md | 单部件（1 个独立实体） | S1 / S2 / S3 / S4 |
| multi-part-playbook.md | 多部件（≥2 个 / 仿真 / 装配） | P1 / P2 / P3 / P4 |

## 骨架模板（所有 Playbook 共用）

```
顶部：进入条件 + 执行契约 1~7 条
中部：Step / Phase 总表（本步产出 / 允许跳过 / 下一步）
下部：每个 Step / Phase 详细模块
  - 前置 + 本步产出 + 命令模板 + AI 回报契约（含 Quote-back 示范）
底部：常见失败模式（FM-xx，初版可为空）
```

## Quote-back 强制规则（所有 Playbook 适用）

每个 Step 产出报告**第一行**必须是：

    引自 <playbook-basename> §Step <Rn/Sn/Pn> / <小标题>：
      "<原文一行>"

锚点用标题 + 小标题（不用裸行号）。原文须与 Playbook 实际内容一致。
违规：缺 Quote-back / 引错 Step / 原文捏造 → 回补 Read + 重出产出报告。

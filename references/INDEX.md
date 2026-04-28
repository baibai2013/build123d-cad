# references/ 导航索引

## 场景路由（兜底表——SKILL.md 路由表覆盖不到时用）

| 用户想做什么 | 先 Read | 后续可能用到 |
|---|---|---|
| 做某型号配件 | protocols/reference-product-playbook.md | verify/, reference-product/ |
| 单个零件 | protocols/single-part-playbook.md | parts/ |
| 多部件 / 装配 | protocols/multi-part-playbook.md | assembly/, simulation/ |
| 曲面建模 | parts/surface-modeling.md | parts/cheatsheet.md |
| 工艺约束 | process/{3d-printing,cnc,laser}.md | — |
| 仿真 / IK | simulation/ | peter-corke/simulation-philosophy.md |

## 目录职责（一行一目录）

- protocols/          三大流程 Playbook（AI 执行期 SSOT）
- verify/             Layer 0/1/2 + 反馈闭环
- reference-product/  参考物建模子方法论（反推 / 标注 / 摄影）
- parts/              API cheatsheet + 典型建模模式（Pattern 13–15 含螺纹/多体融合/边过滤）+ 曲面建模
- process/            3D 打印 / CNC / 激光工艺
- assembly/           装配模式 + 爆炸动画
- simulation/         FK / IK / 步态 / URDF
- peter-corke/        仿真哲学
- data-sources/       标准件尺寸数据（fasteners / bearings / servos）— 含 ISO 4762/7380/7046/2009/7045/1580 + 全套螺母

## 准入原则

- 进 Playbook 是唯一合法流程入口
- 禁止从 references/<子领域>/ 自拼流程（会跳步）
- Playbook 内部引用的子文档按需 Read

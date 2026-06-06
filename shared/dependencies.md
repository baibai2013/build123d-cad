# 子技能依赖关系 (dependencies)

谁依赖谁。改动被多方依赖的子技能（viewer 尤甚）时，需跑相关方的 smoke test。

## 依赖图

```
mechanical ──STEP──▶ viewer        (机械产物预览)
mechanical ──STEP──▶ urdf          (转机器人描述)
mechanical ──STEP──▶ gcode         (FDM 切片预检)
mechanical ──STEP/DXF─▶ sendcutsend (钣金报价)
urdf       ──URDF──▶ viewer        (关节可视化)
urdf       ─────────▶ srdf         (MoveIt 规划组基于 URDF)
urdf       ─────────▶ sdf          (Gazebo 世界引用 URDF)
urdf       ──URDF──▶ simulation    (无头动力学跑 + 自验稳定性)
sdf        ──SDF───▶ simulation    (loadSDF 跑世界/模型)
simulation ──trajectory.json──▶ viewer (cad 引擎 3D 回放:URDF + ?trajectory= 时间轴)
simulation ──results.json─────▶ viewer (engine=sim 数据面板:曲线 + 判稳徽章)
parts-catalog ─STEP─▶ mechanical   (现成件并入装配)
pcb        ──circuit.json+bom.json──▶ viewer(engine=tscircuit 统一预览:PCB/原理图/3D + BOM/总价)
pcb        ──glb/svg──▶ viewer      (engine=cad/pcb/sch 单产物预览)
pcb        ──step/dxf─▶ mechanical  (外壳让位/装配间隙)
electronics-bom ─library.json─▶ pcb (选料喂 tsci import,可选上游)
```

## 被依赖度（改动需谨慎）

| 子技能 | 被依赖方 | 改动影响面 |
|---|---|---|
| **viewer** | mechanical / urdf / pcb / simulation（所有要预览的） | 高——改 router/server 跑全量 viewer 测试 |
| **mechanical** | viewer / urdf / gcode / sendcutsend | 高——是产物源头 |
| urdf | srdf / sdf / viewer | 中 |
| parts-catalog | mechanical | 低 |

## 独立（无下游）

`bambu-labs`、`gcode`、`sendcutsend`、`srdf`、`sdf` 为链路末端，改动只需自测。
（`simulation` 消费 urdf/sdf 产物，下游产 `trajectory.json`/`results.json` 给 viewer 做 3D 回放/数据面板。）

## 高扇入接口登记

### viewer URL 协议(P0-3 fullstack 2026-06-02 落地)

所有上游(mechanical / urdf / gcode / sendcutsend)只产文件路径,**不直接拼 URL**;
URL 拼装由 `skills/viewer/scripts/start.sh` / `web_preview.py` 统一生成。

```
http://127.0.0.1:<port>/?engine=<cad|pcb|sch|sim>&dir=<abs-dir>&file=<rel-file>
```

- 字段规约:见 `skills/viewer/references/url-protocol.md`
- 健康协议:`GET /__cad/server` → `app="build123d-cad/viewer" + serverApiVersion=2`
- 退出码契约:`0/2/3/4` 见 url-protocol.md §退出码

**改动须知**:viewer URL 协议 / `serverApiVersion` / `engines` 枚举 / `engineImpl` 字段任一改动,
必须在本节升级版本号 + @全员 + 跑各上游 smoke。当前版本 `serverApiVersion=2`(2026-06-02)。

### 后续登记(占位)

- joints schema(P0-4 algorithm,4 + 8)
- output 路径约定(P0-6 tech_lead,§7)
- mechanical→urdf/gcode handoff(P0-2 mechanical,见 02 §X)

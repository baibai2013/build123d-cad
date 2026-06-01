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
parts-catalog ─STEP─▶ mechanical   (现成件并入装配)
```

## 被依赖度（改动需谨慎）

| 子技能 | 被依赖方 | 改动影响面 |
|---|---|---|
| **viewer** | mechanical / urdf（所有要预览的） | 高——改 router/server 跑全量 viewer 测试 |
| **mechanical** | viewer / urdf / gcode / sendcutsend | 高——是产物源头 |
| urdf | srdf / sdf / viewer | 中 |
| parts-catalog | mechanical | 低 |

## 独立（无下游）

`bambu-labs`、`gcode`、`sendcutsend`、`srdf`、`sdf` 为链路末端，改动只需自测。

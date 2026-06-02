# #2 flange_4hole ★★

设计一个 4 孔法兰盘:外径 Φ80,内孔 Φ40 通孔,厚度 8 mm,在 PCD 60 mm 上均布 4 个 Φ6 通孔(0°/90°/180°/270°)。法兰外圆边倒 R1 圆角。导出 STEP 到 `output/flange_4hole.step`,导出顶视图 DXF 到 `output/flange_4hole.dxf`。

**验收**
- BRep + STEP reimport + solid_count=1 + manifold
- volume ≈ 29254.51 mm³ (±0.5 %)
- bbox = [80.0, 80.0, 8.0]
- 4 孔中心 (±30,0)/(0,±30) ±0.1 mm
- DXF 顶视图含 OD/ID 圆 + 4 孔

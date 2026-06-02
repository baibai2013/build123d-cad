# #1 calibration_block ★

用 build123d 设计一个校准块作为 CAD 输出基准:外形 60×40×20 mm 长方体(沿 X×Y×Z),底面 4 个角各开 1 个 Φ4 通孔(贯穿 Z 方向),孔中心距各侧外缘 5 mm。无倒角无圆角,单一 solid。导出 STEP 到 `output/calibration_block.step`。

**验收**
- BRep 通过 + STEP reimport OK + solid_count=1 + manifold
- volume ≈ 46994.69 mm³ (±0.5 %)
- bbox = [60.0, 40.0, 20.0] (±0.05 mm)
- 4 孔中心 (5,5)/(55,5)/(5,35)/(55,35)

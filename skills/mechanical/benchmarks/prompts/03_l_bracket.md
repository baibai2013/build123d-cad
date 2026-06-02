# #3 l_bracket ★★

设计一个带加强肋的 L 支架:水平翼板 50×50×5 mm(在 XY 平面),竖直翼板 50×40×5 mm(沿 +Z 方向,与水平翼板共用 X=0 边),夹角 90°。在 L 形内角处加 2 条三角加强肋:厚 3 mm,从内角沿 X 与 Z 各延伸 30 mm。每翼板各开 2 个 Φ5 安装孔。导出 STEP。

**验收**
- BRep + STEP reimport + solid_count=1 + manifold
- bbox = [50.0, 50.0, 40.0]
- 内角 boolean union 不漏接

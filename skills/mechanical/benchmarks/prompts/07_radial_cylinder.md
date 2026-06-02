# #7 radial_cylinder ★★★★

径向气缸缸体:主缸沿 Z 轴 Φ40 外径 Φ20 内孔长 80(Z=0~80)。Z=40 沿 +X 方向伸出一段 Φ12 进气管(壁厚 1.5,内孔 Φ9,长 25),进气管内孔与主缸内孔贯通。Z=80 端配 4 孔法兰:Φ60 外径 8 mm 厚,4×Φ5 PCD 45 均布。法兰与缸体一体单 solid。导出 STEP。

**验收**
- BRep + reimport + solid_count=1 + manifold
- bbox 约 [60.0, 60.0, 88.0] ±0.5
- 内通连(reimport 后内 void volume ≈ 24938 mm³ ±2 %)

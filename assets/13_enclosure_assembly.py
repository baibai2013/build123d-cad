"""
扣合壳体 — 装配预览 / Enclosure Assembly View
用途：将盒体和盖子按设计位置组合，OCP CAD Viewer 预览

依赖：先运行 13_enclosure_box.py 生成 STEP 文件
"""
from build123d import *
from ocp_vscode import show

# ===== 关键尺寸（与 13_enclosure_box.py 一致） =====
outer_h = 40
lid_thick = 3

# ===== 导入零件 =====
body = import_step("enclosure_box.step")
lid = import_step("enclosure_lid.step")

# ===== 装配定位 =====
# 盖子放到盒体顶面：盒体顶面 z = outer_h/2，盖子板底面对齐
lid_z = outer_h / 2 + lid_thick / 2
assembled_lid = Pos(0, 0, lid_z) * lid

# ===== 导出装配体 =====
assembly = Compound(children=[body, assembled_lid])
export_step(assembly, "enclosure_assembly.step")
print(f"装配体导出: enclosure_assembly.step")

# ===== OCP 预览 =====
show(body, assembled_lid,
     names=["body", "lid"],
     colors=["steelblue", "orange"])

"""
扣合壳体 / Snap-Fit Enclosure Box
用途：电子设备外壳、3D打印盒体 + 盖板，唇边台阶扣合
复杂度：★★★☆☆（抽壳 + 唇边台阶 + 盖子凸台 + 文字浮雕）

配套文件：
  13_enclosure_assembly.py  — 装配预览
  13_enclosure_exploded.py  — 爆炸动画
"""
from build123d import *

# ===== 参数 =====
# 盒体外形
outer_l, outer_w, outer_h = 80, 60, 40   # 长×宽×高 mm
wall_t = 2.5                               # 壁厚 mm
corner_r = 2                               # 外竖边圆角半径

# 扣合结构
lip_h = 3                                  # 唇边台阶高度
lip_inset = 1.2                            # 唇边台阶宽度（从内壁向内缩进）
lid_gap = 0.3                              # 单边配合间隙（3D打印公差）

# 盖子
lid_thick = 3                              # 盖子主体厚度
lid_tab_h = 2.5                            # 盖子底部凸台高度（插入台阶）

# 文字
text_str = "YOYO"
text_height = 1.0                          # 文字凸起高度

# ===== 派生尺寸 =====
inner_l = outer_l - 2 * wall_t
inner_w = outer_w - 2 * wall_t

lid_l = inner_l - lid_gap * 2
lid_w = inner_w - lid_gap * 2

tab_l = inner_l - 2 * lip_inset - lid_gap * 2
tab_w = inner_w - 2 * lip_inset - lid_gap * 2

target_text_width = lid_w / 2
text_font_size = target_text_width / 2.4

# ============================================================
# PART 1: 盒体
# 操作序列：取毛坯 → 倒竖边圆角 → 顶面抽壳 → 切台阶
# ============================================================
with BuildPart() as box:
    Box(outer_l, outer_w, outer_h)
    fillet(box.edges().filter_by(Axis.Z), radius=corner_r)
    offset(amount=-wall_t, openings=box.faces().sort_by(Axis.Z)[-1])

    top_face = box.faces().sort_by(Axis.Z)[-1]
    with BuildSketch(top_face):
        Rectangle(inner_l, inner_w)
        Rectangle(inner_l - 2 * lip_inset, inner_w - 2 * lip_inset,
                  mode=Mode.SUBTRACT)
    extrude(amount=-lip_h, mode=Mode.SUBTRACT)

# ============================================================
# PART 2: 盖子
# 操作序列：取薄板 → 倒竖边圆角 → 底部加凸台 → 顶面加文字
# ============================================================
with BuildPart() as lid:
    Box(lid_l, lid_w, lid_thick)
    fillet(lid.edges().filter_by(Axis.Z), radius=1)

    bottom_face = lid.faces().sort_by(Axis.Z)[0]
    with BuildSketch(bottom_face):
        Rectangle(tab_l, tab_w)
    extrude(amount=lid_tab_h)

    top_face = lid.faces().sort_by(Axis.Z)[-1]
    with BuildSketch(top_face):
        Text(text_str, font_size=text_font_size,
             align=(Align.CENTER, Align.CENTER))
    extrude(amount=text_height)

# ===== 验证 =====
box_bb = box.part.bounding_box()
lid_bb = lid.part.bounding_box()
print(f"盒体尺寸: {box_bb.size.X:.1f} x {box_bb.size.Y:.1f} x {box_bb.size.Z:.1f} mm")
print(f"盖子尺寸: {lid_bb.size.X:.1f} x {lid_bb.size.Y:.1f} x {lid_bb.size.Z:.1f} mm")
print(f"盒体体积: {box.part.volume:.1f} mm^3")
print(f"盖子体积: {lid.part.volume:.1f} mm^3")

# ===== 导出 =====
export_step(box.part, "enclosure_box.step")
export_step(lid.part, "enclosure_lid.step")
export_stl(box.part, "enclosure_box.stl")
export_stl(lid.part, "enclosure_lid.stl")
print("\n导出完成: enclosure_box.step/.stl, enclosure_lid.step/.stl")

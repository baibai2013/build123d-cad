"""
合页 / Hinge
用途：门铰、设备开合机构，装配体建模范例
复杂度：★★★★☆（多个零件 + 装配定位）
"""
from build123d import *

# ===== 参数 =====
leaf_l      = 60    # 合页叶片长度 mm
leaf_w      = 30    # 叶片宽度 mm
leaf_t      = 2.5   # 叶片厚度 mm
barrel_r    = 4     # 轴管外径半径 mm
barrel_n    = 3     # 轴管节数（奇数=左2右1，偶数=各半）
pin_r       = 1.5   # 轴销半径 mm
hole_r      = 2.0   # 安装孔半径（M4 通孔）
hole_n      = 2     # 每片安装孔数量

# ===== 构建单片合页 =====
def make_leaf(knuckle_count, total_knuckles):
    """
    knuckle_count: 此叶片上的轴管数
    total_knuckles: 总轴管数
    """
    barrel_seg_l = leaf_l / total_knuckles
    with BuildPart() as leaf:
        # 叶片本体
        Box(leaf_l, leaf_w, leaf_t)

        # 轴管（卷边）
        knuckle_positions = []
        idx = 0
        for k in range(total_knuckles):
            belongs_to_this = (k % 2 == 0)  # 偶数节给此叶片
            if belongs_to_this:
                knuckle_positions.append(
                    Pos(-leaf_l / 2 + barrel_seg_l * k + barrel_seg_l / 2, 0, 0)
                )

        barrel_face = leaf.faces().filter_by(Axis.Y).sort_by(Axis.Y)[-1]  # 合页折叠边
        with BuildSketch(barrel_face):
            with Locations(*knuckle_positions):
                Circle(barrel_r)
            # 去掉叶片厚度内的实心部分（内孔）
            with Locations(*knuckle_positions):
                Circle(pin_r, mode=Mode.SUBTRACT)
        extrude(amount=barrel_r * 2)

        # 安装孔
        top_face = leaf.faces().sort_by(Axis.Z)[-1]
        with BuildSketch(top_face):
            with GridLocations(leaf_l / (hole_n + 1) * hole_n, 0, hole_n, 1):
                Circle(hole_r)
        extrude(amount=-leaf_t, mode=Mode.SUBTRACT)

    return leaf.part

# ===== 建模两片合页 =====
leaf_a = make_leaf(knuckle_count=2, total_knuckles=barrel_n)
leaf_b = make_leaf(knuckle_count=1, total_knuckles=barrel_n)

# ===== 导出 =====
export_step(leaf_a, "09_hinge_leaf_a.step")
export_step(leaf_b, "09_hinge_leaf_b.step")

print("合页零件已导出（leaf_a + leaf_b，需装配）")

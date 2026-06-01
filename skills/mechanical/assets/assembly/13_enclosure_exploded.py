"""
扣合壳体 — 爆炸动画 / Enclosure Exploded Animation
用途：盒体和盖子沿 Z 轴分离展开，OCP CAD Viewer 动画预览

动画循环：炸开2s → 停留10s → 合拢2s → 停留2s（共16s）

依赖：先运行 13_enclosure_box.py 生成 STEP 文件
"""
from build123d import *
from ocp_vscode import show, Animation

# ===== 关键尺寸（与 13_enclosure_box.py 一致） =====
outer_h = 40
lid_thick = 3

# ===== 爆炸参数（默认值，实战验证） =====
explode_dist = 30                              # 爆炸总距离 mm
half = explode_dist / 2                        # 各零件移动半距

# ===== 导入零件 =====
body = import_step("enclosure_box.step")
lid = import_step("enclosure_lid.step")

# ===== 装配定位（动画起点） =====
lid_z = outer_h / 2 + lid_thick / 2
assembled_lid = Pos(0, 0, lid_z) * lid

# ===== 静态爆炸图导出 =====
exp_body = Pos(0, 0, -half) * body
exp_lid = Pos(0, 0, lid_z + half) * lid
exploded = Compound(children=[exp_body, exp_lid])
export_step(exploded, "enclosure_exploded.step")
print(f"爆炸图导出: enclosure_exploded.step (爆炸距离 {explode_dist}mm)")

# ===== OCP 显示装配态（动画起点） =====
show(body, assembled_lid,
     names=["body", "lid"],
     colors=["steelblue", "orange"])

# ===== 爆炸动画 =====
# 时间轴：炸开2s → 停留10s → 合拢2s → 停留2s（16s循环）
t = [0, 2, 12, 14, 16]                        # 关键帧时间点（秒）

animation = Animation()
animation.add_track("/Group/body", "t", t,
                    [[0,0,0], [0,0,-half], [0,0,-half], [0,0,0], [0,0,0]])
animation.add_track("/Group/lid",  "t", t,
                    [[0,0,0], [0,0,half],  [0,0,half],  [0,0,0], [0,0,0]])
animation.animate(1)                           # speed=1 正常速度

print("OCP Viewer: 爆炸动画已加载 (16s循环: 炸2s → 停10s → 合2s → 停2s)")

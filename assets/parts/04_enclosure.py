from build123d import *
import os
os.makedirs("output", exist_ok=True)

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
text_str = "baibai"
text_height = 1.0                          # 文字凸起高度

# ===== 派生尺寸 =====
inner_l = outer_l - 2 * wall_t             # 内腔长度 75
inner_w = outer_w - 2 * wall_t             # 内腔宽度 55

# 盖子外框 = 刚好搁在台阶上
lid_l = inner_l - lid_gap * 2              # 盖子长
lid_w = inner_w - lid_gap * 2              # 盖子宽

# 盖子底部凸台 = 插入台阶内侧
tab_l = inner_l - 2 * lip_inset - lid_gap * 2
tab_w = inner_w - 2 * lip_inset - lid_gap * 2

# 文字宽度 = 盖子宽度的一半
target_text_width = lid_w / 2
# Text font_size 近似：文字宽度 ≈ 盖子宽度的 70%
target_text_width = lid_w * 0.7
text_font_size = target_text_width / 3.6

# ============================================================
# PART 1: 盒体
# 操作序列：取毛坯 → 倒竖边圆角 → 顶面抽壳 → 切台阶
# ============================================================
with BuildPart() as box:
    # Step 1: 毛坯方块
    Box(outer_l, outer_w, outer_h)

    # Step 2: 竖边倒圆角（改善3D打印强度 + 外观）
    fillet(box.edges().filter_by(Axis.Z), radius=corner_r)

    # Step 3: 从顶面抽壳（移除顶面，向内挖空）
    offset(amount=-wall_t, openings=box.faces().sort_by(Axis.Z)[-1])

    # Step 4: 在内壁顶部切出台阶（唇边）
    # 在当前顶面画一圈矩形环，向下切除 lip_h
    top_face = box.faces().sort_by(Axis.Z)[-1]
    with BuildSketch(top_face):
        Rectangle(inner_l, inner_w)                                    # 外框 = 内腔尺寸
        Rectangle(inner_l - 2 * lip_inset, inner_w - 2 * lip_inset,
                  mode=Mode.SUBTRACT)                                  # 内框挖空 → 得到环形
    extrude(amount=-lip_h, mode=Mode.SUBTRACT)                        # 向下切除台阶

# ============================================================
# PART 2: 盖子
# 操作序列：取薄板 → 倒竖边圆角 → 底部加凸台 → 顶面加文字
# ============================================================
with BuildPart() as lid:
    # Step 1: 盖子主体薄板
    Box(lid_l, lid_w, lid_thick)

    # Step 2: 竖边倒圆角
    fillet(lid.edges().filter_by(Axis.Z), radius=1)

    # Step 3: 底面加凸台（插入盒体台阶）
    bottom_face = lid.faces().sort_by(Axis.Z)[0]
    with BuildSketch(bottom_face):
        Rectangle(tab_l, tab_w)
    extrude(amount=lid_tab_h)                                          # 沿底面法向量（向下）长出凸台

    # Step 4: 顶面加 "YOYO" 凸起文字
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
print(f"文字 font_size: {text_font_size:.1f} (目标宽度 ≈ {target_text_width:.1f} mm)")

# ===== 导出 =====
export_step(box.part, "output/enclosure_box.step")
export_step(lid.part, "output/enclosure_lid.step")
export_stl(box.part, "output/enclosure_box.stl")
export_stl(lid.part, "output/enclosure_lid.stl")
print("\n导出完成: output/enclosure_box.step/.stl, enclosure_lid.step/.stl")

# ============================================================
# ASSEMBLY: 装配视图
# 盖子上移到盒体顶部，凸台插入唇边台阶
# ============================================================
explode_dist = 30                                      # 爆炸距离 mm

# 盖子装配位置：盒体顶面 z = outer_h/2，盖子板底面对齐
lid_z = outer_h / 2 + lid_thick / 2                    # 盖子中心 Z 坐标

# 装配体：盒体原位 + 盖子就位
assembled_lid = Pos(0, 0, lid_z) * lid.part
assembly = Compound(children=[box.part, assembled_lid])
export_step(assembly, "output/enclosure_assembly.step")
print(f"装配体导出: output/enclosure_assembly.step")

# ============================================================
# EXPLODED VIEW: 爆炸图
# 盒体下移、盖子上移，沿 Z 轴分离展示内部结构
# ============================================================
exp_box = Pos(0, 0, -explode_dist / 2) * box.part     # 盒体下移 15mm
exp_lid = Pos(0, 0, lid_z + explode_dist / 2) * lid.part  # 盖子上移 15mm
exploded = Compound(children=[exp_box, exp_lid])
export_step(exploded, "output/enclosure_exploded.step")
print(f"爆炸图导出: output/enclosure_exploded.step (爆炸距离 {explode_dist}mm)")

# ============================================================
# OCP CAD Viewer 可视化（需安装 ocp_vscode 扩展）
# ============================================================
try:
    from ocp_vscode import show, Animation, save_screenshot

    # 显示装配态（动画起点）
    show(box.part, assembled_lid,
         names=["box_body", "lid"],
         colors=["steelblue", "orange"])

    # 爆炸动画：炸1s → 停3s → 合1s → 停3s（共8s循环）
    # times 用实际秒数，animate(speed=1) 正常速度播放
    half = explode_dist / 2
    t = [0, 1, 4, 5, 8]                       # 实际秒数关键帧

    animation = Animation()
    animation.add_track("/Group/box_body", "t", t,
                        [[0,0,0], [0,0,-half], [0,0,-half], [0,0,0], [0,0,0]])
    animation.add_track("/Group/lid", "t", t,
                        [[0,0,0], [0,0,half], [0,0,half], [0,0,0], [0,0,0]])
    animation.animate(1)                       # speed=1 正常速度
    print("OCP Viewer: 爆炸动画已加载 (8s: 炸1s-停3s-合1s-停3s)")

    # 截屏生成 GIF（手动逐帧：set_relative_time → save_screenshot → 合成）
    import time
    from PIL import Image
    import tempfile, os

    time.sleep(3)                              # 等待 Viewer 渲染就绪

    gif_fps = 10                               # 帧率
    gif_duration = 8                           # 动画总时长（秒）
    n_frames = gif_fps * gif_duration          # 80 帧
    frame_delay = round(1000 / gif_fps)        # 每帧间隔 ms

    frames = []
    tmp_path = os.path.join(tempfile.gettempdir(), "ocp_frame.png")

    print(f"GIF 截屏中 ({n_frames} 帧)...", end=" ", flush=True)
    for i in range(n_frames):
        frac = i / n_frames                    # 0.0 ~ 1.0
        animation.set_relative_time(frac)
        time.sleep(0.3)                        # 等待渲染
        save_screenshot(tmp_path)
        time.sleep(0.2)                        # 等待写入
        img = Image.open(tmp_path).convert("RGB")
        frames.append(img.copy())
        if i % 10 == 0:
            print(f"{100*i//n_frames}%", end=" ", flush=True)

    print("100%")

    # 合成 GIF（无限循环）
    frames[0].save(
        "output/enclosure_explode.gif",
        save_all=True,
        append_images=frames[1:],
        duration=frame_delay,
        loop=0,
    )
    print("GIF 导出完成: enclosure_explode.gif")
except ImportError:
    print("提示: 安装 ocp_vscode 可在 VS Code 中查看 3D 爆炸动画")

# 参考物尺寸反推方法论（5 种手段）

> 适用场景：官网未提供 STEP，GrabCAD 未收录，需要从公开资料反推尺寸。

## 1. 按置信度排序的 5 种手段

| 手段 | 输入 | 精度 | 适用场景 | 对应工具 |
|---|---|---|---|---|
| A. STEP 导入 | model.step | ★★★★★ | GrabCAD / 官网 | `import_step()` |
| B. 三视图比例反推 | 官方三视图 PNG | ★★★★ | 官网有高清产品图 | `pixel_measure.py` |
| C. 已知基准测量 | 实拍 + 已知尺寸 | ★★★ | 电商详情页实拍 | `pixel_measure.py` |
| D. 特征比例推断 | 单张正面图 | ★★ | 只有一张图 | 手动估算 |
| E. 拆解视频截帧 | 拆机视频帧 | ★★★ | iFixit / B 站 | `pixel_measure.py` |

## 2. 手段 B — 三视图比例反推（最常用）

1. 找到官方三视图 PNG（背景纯色，无透视畸变）
2. 用 `preprocess_reference.py` 裁部件 + 建 scale.json
3. 用 `pixel_measure.py` 批量测关键点
4. 换算成部件本地坐标（以中心为原点）
5. 填 `params.md` 的"摄像头模组位置"等行，**标 ★★★★ 置信度**

完整命令例：
```bash
# 1) crop
python3 scripts/visual/preprocess_reference.py official_back.jpg \
  --bbox "340,220,700,1520" --physical-length "162.0mm" --physical-axis height \
  --output-dir refs/k70/clean/

# 2) measure
python3 scripts/visual/pixel_measure.py refs/k70/clean/official_back_cropped.png \
  --scale refs/k70/clean/official_back_scale.json \
  --points "360,180;340,520;200,760" \
  --origin "center" --output refs/k70/measurements.csv
```

## 3. 手段 C — 已知基准测量

用途：官网没三视图，但电商详情页有一张"带尺子"的图。
步骤：
1. 在图上标"尺子两端"的像素坐标 → 得 mm/px
2. 用同一 mm/px 量其他特征

## 4. 手段 D — 特征比例推断（低置信度）

兜底手段。假设某一已知特征大小（如"iPhone 15 Pro 摄像头模组 ≈ 38mm × 38mm"）→ 反推整机尺寸。
**必须在 `params.md` 标 ★★ 置信度**，下游建模时要把这些尺寸标为"待验证"。

## 5. 手段 E — 拆解视频截帧

视频截帧通常有运动模糊和光照不均：
- 优先取特写帧（镜头静止 > 1 秒）
- 拿游标卡尺或已知螺丝尺寸做基准
- 结果置信度 ★★★（低于官方三视图）

## 6. 失败兜底

5 种手段全部不可用时：
- 让用户手动测量实物
- 提供测量位置清单（长/宽/厚/摄像头位置/按键位置）
- 在 `params.md` 标记"用户实测"来源

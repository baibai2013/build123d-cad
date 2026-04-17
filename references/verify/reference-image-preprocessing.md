# 参考图预处理规范 / Reference Image Preprocessing

> 核心原则：参考图是实拍/营销图，不是干净的正交视图。未经预处理的图不得进入 Layer 2 对比。

## 1. 为什么必做

- GSMArena / 官网营销图带背景、透视、阴影
- 拆机视频截帧有运动模糊
- 不裁掉背景直接对比 → Canny 会把背景边缘当部件边缘 → IoU 虚低

## 2. 最小预处理流程

```
原始参考图 ──► preprocess_reference.py
                │
                ├── 输入：图 + bbox + 物理尺寸 + 尺寸轴
                │
                ├── 输出：
                │    {stem}_cropped.png   去背景
                │    {stem}_bbox.json     原图坐标
                │    {stem}_scale.json    mm/px
                │
                └── 记录到：refs/clean/  或  references/{part}/clean/
```

## 3. bbox 怎么来

### 手动标注（推荐）
打开参考图，用 Preview 或 matplotlib ginput 点选 4 个角点：
```python
from PIL import Image
import matplotlib.pyplot as plt
img = Image.open("reference.png")
plt.imshow(img); pts = plt.ginput(2)  # 左上 + 右下
x0, y0 = map(int, pts[0]); x1, y1 = map(int, pts[1])
print(f"--bbox {x0},{y0},{x1-x0},{y1-y0}")
```

### 自动前景分割（兜底）
图像简单 + 背景纯色时可用 `rembg`（需单独安装）。否则走手动。

## 4. 物理尺寸从哪来

- **首选**：官方参数（已知手机长度 160.26 mm）
- **次选**：电商详情页标的"实拍"尺寸（置信度 ★★）
- **兜底**：特征比例推断（比如摄像头岛已知 = ? mm，反推长度，置信度 ★★）

## 5. 典型案例

### 案例 A：test 13 官方侧视图
```bash
python3 scripts/visual/preprocess_reference.py \
  references/redmi-k80-pro/images/official_03_side.jpg \
  --bbox "72,50,385,1063" \
  --physical-length "160.26mm" \
  --physical-axis height \
  --output-dir references/redmi-k80-pro/clean/
```

### 案例 B：GSMArena 背面图
```bash
python3 scripts/visual/preprocess_reference.py \
  references/redmi-k80-pro/images/gsmarena_3.jpg \
  --bbox "420,180,680,1480" \
  --physical-length "160.26mm" \
  --physical-axis height \
  --output-dir references/redmi-k80-pro/clean/
```

## 6. 产出命名

一组参考图建议都放在同一个 `clean/` 目录：
```
references/{product}/
├── images/                     # 原始图（保留）
│   ├── gsmarena_1.jpg
│   ├── official_03_side.jpg
│   └── ...
└── clean/                      # 预处理产出（入 Layer 2 比较）
    ├── official_03_side_cropped.png
    ├── official_03_side_bbox.json
    ├── official_03_side_scale.json
    └── ...
```

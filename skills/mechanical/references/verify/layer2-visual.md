# Layer 2：视觉比对验证

> Layer 0 锁参数，Layer 1 验约束，**Layer 2 回答"看起来对不对？"**
>
> 捕获无法写成约束但一眼能看出的问题：整体比例失调、特征遗漏、曲面过渡生硬。

合同规范见 `layer0-contract.md`，约束验证见 `layer1-verification.md`，反馈闭环见 `feedback-diagnosis.md`。

---

## 1. Layer 2 能捕获什么

| 问题类型 | Layer 1 | Layer 2 |
|---------|:---:|:---:|
| 尺寸/位置偏差 | ✅ | ✅ |
| 整体比例"看着就不对" | ❌ | ✅ |
| 圆角过大/过小导致外观异常 | ❌ | ✅ |
| 特征遗漏（忘开某个孔） | ❌ | ✅ |
| 曲面过渡生硬 | ❌ | ✅ |
| 特征形状类型搞错（方变圆） | ✅(ratio) | ✅ |

---

## 2. 运行模式（可插拔，自动降级）

Layer 2 有 4 种后端，按优先级自动选择：

| 优先级 | 模式 | 依赖 | 精度 | 场景 |
|:---:|------|------|:---:|------|
| 1 | **ai_vision** | Anthropic API (Vision) | 高 | API 代理支持 multimodal |
| 2 | **opencv** | OpenCV (cv2) | 中 | 无 API 但有 OpenCV |
| 3 | **manual** | OCP + PIL | 人工 | 生成并排图供目视 |
| 4 | **skip** | — | — | 无参考图 |

### 模式自动决策

```python
def decide_layer2_mode(contract, ref_images_dir):
    """自动决定 Layer 2 运行模式"""
    # 1. 有没有参考图？
    ref_images = match_ref_to_views(ref_images_dir, contract) if ref_images_dir else {}
    if not ref_images:
        return "skip"
    
    # 2. OCP Viewer 是否运行？
    try:
        from ocp_vscode.state import get_ports
        from ocp_vscode.comms import port_check
        active = next((int(p) for p in get_ports() if port_check(int(p))), None)
        if not active:
            return "manual"  # 无法截图，只能用参考图 + 人工
    except ImportError:
        return "manual"
    
    # 3. Vision API 是否可用？
    probe = probe_vision_support()
    if probe["supported"]:
        return "ai_vision"
    
    # 4. OpenCV 是否可用？
    try:
        import cv2
        return "opencv"
    except ImportError:
        return "manual"
```

### Vision API 代理兼容性探测

发送最小 vision 请求，自动检测代理是否支持 multimodal：

```python
def probe_vision_support():
    """
    探测当前 API 代理是否支持图片输入。
    发送 1x1 PNG（~68 bytes base64），不消耗有意义的 token。
    """
    import anthropic, base64
    
    # 最小 1x1 红色 PNG
    TINY_PNG_B64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
        "nGP4z8BQDwAEgAF/pooBPQAAAABJRU5ErkJggg=="
    )
    
    try:
        client = anthropic.Anthropic()  # 读 env: ANTHROPIC_BASE_URL + AUTH_TOKEN
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": TINY_PNG_B64
                    }},
                    {"type": "text", "text": "Reply with the single word OK"}
                ]
            }]
        )
        return {"supported": True, "model": "claude-sonnet-4-20250514"}
    except Exception as e:
        return {"supported": False, "reason": str(e)}
```

---

## 3. Stage V1：多角度截图生成

用 OCP CAD Viewer 自动截 7 个标准视角：

```python
STANDARD_VIEWS = {
    "ISO":    Camera.ISO,
    "FRONT":  Camera.FRONT,     # +Y 正面/屏幕面
    "BACK":   Camera.BACK,      # -Y 背面/摄像头面
    "TOP":    Camera.TOP,       # +Z 俯视
    "BOTTOM": Camera.BOTTOM,    # -Z 仰视/底壳
    "RIGHT":  Camera.RIGHT,     # +X 右侧/按键面
    "LEFT":   Camera.LEFT,      # -X 左侧
}

def generate_screenshots(solid, output_dir, prefix="model"):
    """生成 7 个标准视角截图"""
    from ocp_vscode import show, set_port, Camera, save_screenshot
    from ocp_vscode.comms import port_check
    from ocp_vscode.state import get_ports
    import time, os

    active_port = next((int(p) for p in get_ports() if port_check(int(p))), None)
    if not active_port:
        return {"status": "SKIP", "reason": "OCP Viewer not running"}
    
    set_port(active_port)
    screenshots = {}
    
    for view_name, cam in STANDARD_VIEWS.items():
        show(solid, names=[prefix], reset_camera=cam)
        time.sleep(0.8)
        path = os.path.join(output_dir, f"{prefix}_{view_name}.png")
        save_screenshot(path)
        screenshots[view_name] = path
    
    return {"status": "OK", "screenshots": screenshots}
```

---

## 4. Stage V2：参考图 ↔ 模型比对

### 参考图匹配

```python
def match_ref_to_views(ref_dir, contract):
    """将参考图按文件名关键词匹配到标准视角"""
    keywords = {
        "BACK":   ["back", "rear", "behind", "背面"],
        "FRONT":  ["front", "screen", "正面", "屏幕"],
        "RIGHT":  ["right", "side", "右侧"],
        "LEFT":   ["left", "左侧"],
        "BOTTOM": ["bottom", "port", "底部", "usb"],
        "TOP":    ["top", "顶部"],
        "ISO":    ["iso", "angle", "3d", "全景"],
    }
    matches = {}
    for img_file in os.listdir(ref_dir):
        if not img_file.lower().endswith((".jpg", ".png", ".jpeg")):
            continue
        name_lower = img_file.lower()
        for view, kws in keywords.items():
            if any(kw in name_lower for kw in kws):
                matches[view] = os.path.join(ref_dir, img_file)
                break
    return matches
```

### 模式 A：AI Vision 比对

```python
def visual_compare_ai(ref_path, model_path, view_name, contract):
    """用多模态 LLM 比对参考图和模型截图"""
    import anthropic, base64, json
    
    def encode_image(path):
        with open(path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    
    feature_list = "\n".join(
        f"- {f['name']}: {f['type']} on {f['face']} face"
        for f in contract.get("features", [])
    )
    
    prompt = f"""你是 CAD 模型质量检查员。对比两张图：
- 图 1：参考图（真实产品照片，{view_name} 视角）
- 图 2：CAD 模型截图（同视角）

产品：{contract['meta']['product']}
特征清单：
{feature_list}

输出 JSON：
{{
  "view": "{view_name}",
  "overall_match": "good|fair|poor",
  "overall_score": 0-100,
  "checks": [
    {{
      "feature": "name",
      "visible": true/false,
      "shape_match": "good|fair|poor",
      "position_match": "good|fair|poor",
      "size_match": "good|fair|poor",
      "issue": "具体问题或 null"
    }}
  ],
  "missing_features": ["模型中缺失的特征"],
  "extra_features": ["模型中多余的特征"],
  "proportion_issues": ["整体比例问题"],
  "suggestions": ["修正建议"]
}}

只关注几何形状和比例，忽略颜色/材质/光影。"""

    ref_b64 = encode_image(ref_path)
    model_b64 = encode_image(model_path)
    ext_ref = os.path.splitext(ref_path)[1].lstrip(".")
    ext_model = os.path.splitext(model_path)[1].lstrip(".")
    media_ref = f"image/{ext_ref}" if ext_ref != "jpg" else "image/jpeg"
    media_model = f"image/{ext_model}" if ext_model != "jpg" else "image/jpeg"

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_ref, "data": ref_b64}},
                {"type": "image", "source": {"type": "base64", "media_type": media_model, "data": model_b64}},
                {"type": "text", "text": prompt}
            ]
        }]
    )
    
    text = response.content[0].text
    start, end = text.find("{"), text.rfind("}") + 1
    return json.loads(text[start:end])
```

### 模式 B：OpenCV 纯算法比对

```python
def visual_compare_opencv(ref_path, model_path, view_name):
    """
    纯 OpenCV 轮廓比对，不需要任何 LLM API。
    指标：面积比 + Hu 矩形状匹配 + 质心偏移 + 特征数量。
    """
    import cv2
    import numpy as np
    
    ref = cv2.imread(ref_path, cv2.IMREAD_GRAYSCALE)
    model = cv2.imread(model_path, cv2.IMREAD_GRAYSCALE)
    
    h = max(ref.shape[0], model.shape[0])
    w = max(ref.shape[1], model.shape[1])
    ref = cv2.resize(ref, (w, h))
    model = cv2.resize(model, (w, h))
    
    ref_edges = cv2.Canny(ref, 50, 150)
    model_edges = cv2.Canny(model, 50, 150)
    
    ref_contours, _ = cv2.findContours(ref_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    model_contours, _ = cv2.findContours(model_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    ref_sorted = sorted(ref_contours, key=cv2.contourArea, reverse=True)[:10]
    model_sorted = sorted(model_contours, key=cv2.contourArea, reverse=True)[:10]
    
    # 面积比
    ref_area = cv2.contourArea(ref_sorted[0]) if ref_sorted else 0
    model_area = cv2.contourArea(model_sorted[0]) if model_sorted else 0
    area_ratio = min(ref_area, model_area) / max(ref_area, model_area) if max(ref_area, model_area) > 0 else 0
    
    # Hu 矩形状匹配
    shape_score = 0
    if ref_sorted and model_sorted:
        match_val = cv2.matchShapes(ref_sorted[0], model_sorted[0], cv2.CONTOURS_MATCH_I2, 0)
        shape_score = max(0, 1.0 - match_val)
    
    # 质心偏移
    def centroid(contour):
        M = cv2.moments(contour)
        if M["m00"] == 0: return (0, 0)
        return (M["m10"] / M["m00"], M["m01"] / M["m00"])
    
    ref_c = centroid(ref_sorted[0]) if ref_sorted else (w/2, h/2)
    model_c = centroid(model_sorted[0]) if model_sorted else (w/2, h/2)
    center_ratio = np.sqrt((ref_c[0]-model_c[0])**2 + (ref_c[1]-model_c[1])**2) / np.sqrt(w**2 + h**2)
    
    # 特征数量
    min_area = w * h * 0.01
    ref_n = len([c for c in ref_sorted if cv2.contourArea(c) > min_area])
    model_n = len([c for c in model_sorted if cv2.contourArea(c) > min_area])
    feat_match = min(ref_n, model_n) / max(ref_n, model_n) if max(ref_n, model_n) > 0 else 1
    
    score = area_ratio * 25 + shape_score * 35 + (1 - center_ratio) * 20 + feat_match * 20
    
    suggestions = []
    if area_ratio < 0.7: suggestions.append("主轮廓面积差异大，检查整体尺寸参数")
    if shape_score < 0.6: suggestions.append("主轮廓形状差异大，检查圆角/比例参数")
    if center_ratio > 0.1: suggestions.append("主轮廓质心偏移明显，检查特征位置参数")
    if feat_match < 0.7: suggestions.append("特征数量不匹配，可能遗漏或多余特征")
    
    return {
        "view": view_name,
        "overall_score": round(score, 1),
        "overall_match": "good" if score >= 80 else "fair" if score >= 60 else "poor",
        "metrics": {
            "area_ratio": round(area_ratio, 3),
            "shape_score": round(shape_score, 3),
            "center_offset_ratio": round(center_ratio, 4),
            "feature_count": {"ref": ref_n, "model": model_n},
        },
        "suggestions": suggestions
    }
```

### 模式 C：人工并排对比

```python
def visual_compare_manual(ref_path, model_path, view_name, output_dir):
    """生成并排对比图供人工目视检查"""
    from PIL import Image, ImageDraw
    
    ref = Image.open(ref_path)
    model = Image.open(model_path)
    
    target_h = max(ref.height, model.height)
    ref = ref.resize((int(ref.width * target_h / ref.height), target_h))
    model = model.resize((int(model.width * target_h / model.height), target_h))
    
    gap = 40
    canvas = Image.new("RGB", (ref.width + gap + model.width, target_h + 60), "white")
    canvas.paste(ref, (0, 60))
    canvas.paste(model, (ref.width + gap, 60))
    
    draw = ImageDraw.Draw(canvas)
    draw.text((ref.width // 2 - 30, 10), "Reference", fill="blue")
    draw.text((ref.width + gap + model.width // 2 - 20, 10), "Model", fill="red")
    draw.text((canvas.width // 2 - 40, 30), f"View: {view_name}", fill="black")
    
    path = os.path.join(output_dir, f"compare_{view_name}.png")
    canvas.save(path)
    return path
```

---

## 5. Stage V3：特征核验清单

按视角分配特征可见性（合同中可选配置）：

```yaml
# 可选：在合同中指定视角-特征可见性映射
visibility_map:
  BACK:   [camera_cutout]
  FRONT:  []
  RIGHT:  [volume_btn, power_btn]
  LEFT:   []
  BOTTOM: [usb_c, speaker, sim_tray]
  TOP:    [ir_blaster]
  ISO:    [camera_cutout, volume_btn, power_btn]
```

---

## 6. Stage V4：偏差报告

```python
def generate_visual_report(comparisons, contract):
    """汇总多视角比对结果"""
    scores = [c.get("overall_score", 100) for c in comparisons]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    all_issues = []
    for comp in comparisons:
        for check in comp.get("checks", []):
            if check.get("issue"):
                all_issues.append({
                    "view": comp["view"],
                    "feature": check["feature"],
                    "issue": check["issue"],
                })
        for mf in comp.get("missing_features", []):
            all_issues.append({
                "view": comp["view"],
                "feature": mf,
                "issue": "模型中缺失",
                "severity": "HIGH"
            })
    
    return {
        "avg_score": round(avg_score, 1),
        "verdict": "PASS" if avg_score >= 80 else "WARN" if avg_score >= 60 else "FAIL",
        "n_issues": len(all_issues),
        "issues": all_issues,
        "suggestions": [s for c in comparisons for s in c.get("suggestions", [])]
    }
```

---

## 7. 判定阈值

| avg_score | 判定 | 动作 |
|-----------|------|------|
| ≥ 80 | **PASS** | 进入变体选择 |
| 60 ~ 79 | **WARN** | 列出问题清单，用户决定是否接受 |
| < 60 | **FAIL** | 触发反馈闭环（见 `feedback-diagnosis.md`） |

---

## 8. Layer 2 主流程

```python
def layer2_verify(solid, contract, ref_images_dir, output_dir, mode="auto"):
    """Layer 2 视觉比对主流程"""
    
    if mode == "auto":
        mode = decide_layer2_mode(contract, ref_images_dir)
    
    if mode == "skip":
        return {"verdict": "SKIP", "reason": "无参考图"}
    
    # V1: 截图
    screenshots = generate_screenshots(solid, output_dir)
    if screenshots["status"] == "SKIP":
        if mode in ("ai_vision", "opencv"):
            mode = "manual"  # 无法截图则降级
    
    # 收集参考图
    ref_images = match_ref_to_views(ref_images_dir, contract)
    
    if mode == "ai_vision":
        comparisons = []
        for view, ref_path in ref_images.items():
            if view in screenshots.get("screenshots", {}):
                r = visual_compare_ai(ref_path, screenshots["screenshots"][view], view, contract)
                comparisons.append(r)
        return generate_visual_report(comparisons, contract)
    
    elif mode == "opencv":
        comparisons = []
        for view, ref_path in ref_images.items():
            if view in screenshots.get("screenshots", {}):
                r = visual_compare_opencv(ref_path, screenshots["screenshots"][view], view)
                comparisons.append(r)
        return generate_visual_report(comparisons, contract)
    
    elif mode == "manual":
        compare_images = []
        for view, ref_path in ref_images.items():
            model_path = screenshots.get("screenshots", {}).get(view)
            if model_path:
                path = visual_compare_manual(ref_path, model_path, view, output_dir)
                compare_images.append(path)
        return {
            "verdict": "MANUAL_REVIEW",
            "compare_images": compare_images,
            "message": "并排对比图已生成，请目视检查"
        }
```

---

## 9. 报告格式

```
╔══════════════════════════════════════════╗
║     Layer 2 Visual Verification Report   ║
║     Redmi K70 Case — V2_standard         ║
╠══════════════════════════════════════════╣
║  Mode: ai_vision (Claude Sonnet)         ║
║  Views checked: 4/7                      ║
║    BACK:   92/100  ✅                    ║
║    RIGHT:  88/100  ✅                    ║
║    BOTTOM: 85/100  ✅                    ║
║    ISO:    90/100  ✅                    ║
║  (FRONT/LEFT/TOP: no reference image)    ║
╠══════════════════════════════════════════╣
║  Features: 7/7 checked                   ║
║  Issues: 0                               ║
║  Missing features: 0                     ║
║  Avg score: 88.8                         ║
╠══════════════════════════════════════════╣
║  Verdict: ✅ PASS                        ║
╚══════════════════════════════════════════╝
```

---

## 10. 三层验证完整流程

```
建模代码
    ↓
╔═ Layer 1 (参数验证) ════════╗
║ Stage A: BRep + 单体 + bbox  ║
║ Stage B: 尺寸指纹            ║
║ Stage C: 空间约束 (≥3/特征)  ║
║ Stage D: STEP 精度           ║
╚═════════════════════════════╝
    ↓ PASS
╔═ Layer 2 (视觉验证) ════════╗
║ V1: 多角度截图 (7视角)       ║
║ V2: 参考图 ↔ 模型比对       ║
║ V3: 特征逐项核验            ║
║ V4: 偏差报告                ║
╚═════════════════════════════╝
    ↓ PASS
用户选择变体 → 导出 STEP
```

验证失败时的反馈闭环见 `feedback-diagnosis.md`。

验证脚本见 `scripts/validate/visual_compare.py`。

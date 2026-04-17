#!/usr/bin/env python3
"""
DEPRECATED: This module is superseded by the cad-vision-verify skill.
Use: /Users/liyijiang/.agents/skills/cad-vision-verify/scripts/compare.py
This file is kept for backward compatibility.

Layer 2 Visual Comparison Tool
Layer 2 视觉比对验证工具

Compares CAD model screenshots against reference images using pluggable backends.
用可插拔后端比对 CAD 模型截图与参考图。

Backends (auto-degradation):
  1. ai_vision  — Anthropic Vision API (highest accuracy)
  2. opencv     — OpenCV contour matching (no API needed)
  3. manual     — Side-by-side comparison images for human review
  4. skip       — No reference images available

Usage:
  # Auto-detect mode, compare all matched views
  python3 visual_compare.py --contract contract.yaml --ref-dir references/xiaomi-k70/images --output-dir output/

  # Force specific mode
  python3 visual_compare.py --contract contract.yaml --ref-dir refs/ --output-dir out/ --mode opencv

  # Just generate model screenshots (no comparison)
  python3 visual_compare.py --contract contract.yaml --output-dir out/ --screenshots-only

Spec: references/verify/layer2-visual.md
"""

import os
import sys
import json
import argparse
from pathlib import Path

# ──────────────────────────────────────────────
# 1. Vision API Probe / Vision API 代理兼容性探测
# ──────────────────────────────────────────────

def probe_vision_support():
    """
    Probe whether the current API proxy supports image input.
    Sends a minimal 1x1 PNG (~68 bytes base64), consuming negligible tokens.
    探测当前 API 代理是否支持图片输入。
    """
    try:
        import anthropic
        import base64
    except ImportError:
        return {"supported": False, "reason": "anthropic SDK not installed"}

    # Minimal 1x1 red PNG / 最小 1x1 红色 PNG
    TINY_PNG_B64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
        "nGP4z8BQDwAEgAF/pooBPQAAAABJRU5ErkJggg=="
    )

    try:
        client = anthropic.Anthropic()  # reads ANTHROPIC_BASE_URL + ANTHROPIC_API_KEY from env
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


# ──────────────────────────────────────────────
# 2. Mode Decision / 模式自动决策
# ──────────────────────────────────────────────

def match_ref_to_views(ref_dir, contract=None):
    """
    Match reference images to standard views by filename keywords.
    按文件名关键词将参考图匹配到标准视角。
    """
    if not ref_dir or not os.path.isdir(ref_dir):
        return {}

    keywords = {
        "BACK":   ["back", "rear", "behind", "背面", "摄像头"],
        "FRONT":  ["front", "screen", "正面", "屏幕"],
        "RIGHT":  ["right", "side", "右侧", "按键"],
        "LEFT":   ["left", "左侧"],
        "BOTTOM": ["bottom", "port", "底部", "usb", "充电"],
        "TOP":    ["top", "顶部"],
        "ISO":    ["iso", "angle", "3d", "全景", "立体"],
    }

    matches = {}
    for img_file in os.listdir(ref_dir):
        if not img_file.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):
            continue
        name_lower = img_file.lower()
        for view, kws in keywords.items():
            if any(kw in name_lower for kw in kws):
                matches[view] = os.path.join(ref_dir, img_file)
                break

    return matches


def decide_layer2_mode(contract, ref_images_dir):
    """
    Auto-decide Layer 2 run mode based on available tools.
    根据可用工具自动决定 Layer 2 运行模式。
    """
    # 1. Any reference images? / 有没有参考图？
    ref_images = match_ref_to_views(ref_images_dir, contract) if ref_images_dir else {}
    if not ref_images:
        return "skip"

    # 2. OCP Viewer running? / OCP Viewer 是否运行？
    ocp_available = False
    try:
        from ocp_vscode.state import get_ports
        from ocp_vscode.comms import port_check
        active = next((int(p) for p in get_ports() if port_check(int(p))), None)
        ocp_available = active is not None
    except ImportError:
        pass

    if not ocp_available:
        # Can't take screenshots, manual mode only / 无法截图，只能人工模式
        return "manual"

    # 3. Vision API available? / Vision API 是否可用？
    probe = probe_vision_support()
    if probe["supported"]:
        return "ai_vision"

    # 4. OpenCV available? / OpenCV 是否可用？
    try:
        import cv2
        return "opencv"
    except ImportError:
        return "manual"


# ──────────────────────────────────────────────
# 3. Screenshot Generation / 多角度截图生成
# ──────────────────────────────────────────────

# Standard 7 views / 7个标准视角
STANDARD_VIEWS = {
    "ISO":    "Camera.ISO",
    "FRONT":  "Camera.FRONT",
    "BACK":   "Camera.BACK",
    "TOP":    "Camera.TOP",
    "BOTTOM": "Camera.BOTTOM",
    "RIGHT":  "Camera.RIGHT",
    "LEFT":   "Camera.LEFT",
}


def generate_screenshots(solid, output_dir, prefix="model"):
    """
    Generate 7 standard-view screenshots via OCP CAD Viewer.
    用 OCP CAD Viewer 自动截 7 个标准视角截图。
    """
    try:
        from ocp_vscode import show, set_port, Camera, save_screenshot
        from ocp_vscode.comms import port_check
        from ocp_vscode.state import get_ports
    except ImportError:
        return {"status": "SKIP", "reason": "ocp_vscode not available"}

    import time

    active_port = next((int(p) for p in get_ports() if port_check(int(p))), None)
    if not active_port:
        return {"status": "SKIP", "reason": "OCP Viewer not running"}

    set_port(active_port)
    os.makedirs(output_dir, exist_ok=True)

    cam_map = {
        "ISO":    Camera.ISO,
        "FRONT":  Camera.FRONT,
        "BACK":   Camera.BACK,
        "TOP":    Camera.TOP,
        "BOTTOM": Camera.BOTTOM,
        "RIGHT":  Camera.RIGHT,
        "LEFT":   Camera.LEFT,
    }

    screenshots = {}
    for view_name, cam in cam_map.items():
        show(solid, names=[prefix], reset_camera=cam)
        time.sleep(0.8)  # wait for render / 等待渲染
        path = os.path.join(output_dir, f"{prefix}_{view_name}.png")
        save_screenshot(path)
        screenshots[view_name] = path

    return {"status": "OK", "screenshots": screenshots}


# ──────────────────────────────────────────────
# 4. Mode A: AI Vision Comparison / AI 视觉比对
# ──────────────────────────────────────────────

def visual_compare_ai(ref_path, model_path, view_name, contract):
    """
    Compare reference image vs model screenshot using Claude Vision.
    用多模态 LLM 比对参考图和模型截图。
    """
    import anthropic
    import base64

    def encode_image(path):
        with open(path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")

    feature_list = "\n".join(
        f"- {f['name']}: {f['type']} on {f['face']} face"
        for f in contract.get("features", [])
    )

    prompt = f"""You are a CAD model quality inspector. Compare two images:
- Image 1: Reference (real product photo, {view_name} view)
- Image 2: CAD model screenshot (same view)

Product: {contract.get('meta', {}).get('product', 'unknown')}
Feature list:
{feature_list}

Output JSON:
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
      "issue": "specific issue or null"
    }}
  ],
  "missing_features": ["features in reference but not in model"],
  "extra_features": ["features in model but not in reference"],
  "proportion_issues": ["overall proportion issues"],
  "suggestions": ["fix suggestions"]
}}

Focus only on geometry and proportion, ignore color/material/lighting."""

    ref_b64 = encode_image(ref_path)
    model_b64 = encode_image(model_path)

    ext_ref = os.path.splitext(ref_path)[1].lstrip(".").lower()
    ext_model = os.path.splitext(model_path)[1].lstrip(".").lower()
    media_ref = "image/jpeg" if ext_ref in ("jpg", "jpeg") else f"image/{ext_ref}"
    media_model = "image/jpeg" if ext_model in ("jpg", "jpeg") else f"image/{ext_model}"

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
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    return {"view": view_name, "overall_match": "poor", "overall_score": 0,
            "suggestions": ["Failed to parse Vision API response"]}


# ──────────────────────────────────────────────
# 5. Mode B: OpenCV Contour Comparison / OpenCV 轮廓比对
# ──────────────────────────────────────────────

def visual_compare_opencv(ref_path, model_path, view_name):
    """
    Pure OpenCV contour comparison, no LLM API needed.
    Metrics: area ratio + Hu moment shape match + centroid offset + feature count.
    纯 OpenCV 轮廓比对，不需要任何 LLM API。
    """
    import cv2
    import numpy as np

    ref = cv2.imread(ref_path, cv2.IMREAD_GRAYSCALE)
    model = cv2.imread(model_path, cv2.IMREAD_GRAYSCALE)

    if ref is None or model is None:
        return {"view": view_name, "overall_match": "poor", "overall_score": 0,
                "suggestions": ["Failed to read image files"]}

    # Normalize sizes / 统一尺寸
    h = max(ref.shape[0], model.shape[0])
    w = max(ref.shape[1], model.shape[1])
    ref = cv2.resize(ref, (w, h))
    model = cv2.resize(model, (w, h))

    # Edge detection / 边缘检测
    ref_edges = cv2.Canny(ref, 50, 150)
    model_edges = cv2.Canny(model, 50, 150)

    # Find contours / 查找轮廓
    ref_contours, _ = cv2.findContours(ref_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    model_contours, _ = cv2.findContours(model_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    ref_sorted = sorted(ref_contours, key=cv2.contourArea, reverse=True)[:10]
    model_sorted = sorted(model_contours, key=cv2.contourArea, reverse=True)[:10]

    # Area ratio (25%) / 面积比
    ref_area = cv2.contourArea(ref_sorted[0]) if ref_sorted else 0
    model_area = cv2.contourArea(model_sorted[0]) if model_sorted else 0
    area_ratio = min(ref_area, model_area) / max(ref_area, model_area) if max(ref_area, model_area) > 0 else 0

    # Hu moment shape matching (35%) / Hu 矩形状匹配
    shape_score = 0
    if ref_sorted and model_sorted:
        match_val = cv2.matchShapes(ref_sorted[0], model_sorted[0], cv2.CONTOURS_MATCH_I2, 0)
        shape_score = max(0, 1.0 - match_val)

    # Centroid offset (20%) / 质心偏移
    def centroid(contour):
        M = cv2.moments(contour)
        if M["m00"] == 0:
            return (0, 0)
        return (M["m10"] / M["m00"], M["m01"] / M["m00"])

    ref_c = centroid(ref_sorted[0]) if ref_sorted else (w / 2, h / 2)
    model_c = centroid(model_sorted[0]) if model_sorted else (w / 2, h / 2)
    center_ratio = np.sqrt((ref_c[0] - model_c[0])**2 + (ref_c[1] - model_c[1])**2) / np.sqrt(w**2 + h**2)

    # Feature count (20%) / 特征数量匹配
    min_area = w * h * 0.01
    ref_n = len([c for c in ref_sorted if cv2.contourArea(c) > min_area])
    model_n = len([c for c in model_sorted if cv2.contourArea(c) > min_area])
    feat_match = min(ref_n, model_n) / max(ref_n, model_n) if max(ref_n, model_n) > 0 else 1

    # Weighted score / 加权评分
    score = area_ratio * 25 + shape_score * 35 + (1 - center_ratio) * 20 + feat_match * 20

    suggestions = []
    if area_ratio < 0.7:
        suggestions.append("Main contour area differs significantly — check overall dimensions")
    if shape_score < 0.6:
        suggestions.append("Main contour shape differs — check fillet/proportion params")
    if center_ratio > 0.1:
        suggestions.append("Main contour centroid offset — check feature positions")
    if feat_match < 0.7:
        suggestions.append("Feature count mismatch — possible missing or extra features")

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


# ──────────────────────────────────────────────
# 6. Mode C: Manual Side-by-Side / 人工并排对比
# ──────────────────────────────────────────────

def visual_compare_manual(ref_path, model_path, view_name, output_dir):
    """
    Generate side-by-side comparison image for human review.
    生成并排对比图供人工目视检查。
    """
    from PIL import Image, ImageDraw

    ref = Image.open(ref_path)
    model = Image.open(model_path)

    # Normalize height / 统一高度
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

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"compare_{view_name}.png")
    canvas.save(path)
    return path


# ──────────────────────────────────────────────
# 7. Report Generation / 偏差报告
# ──────────────────────────────────────────────

def generate_visual_report(comparisons, contract):
    """
    Aggregate multi-view comparison results into a verdict.
    汇总多视角比对结果，生成判定报告。
    """
    scores = [c.get("overall_score", 100) for c in comparisons]
    avg_score = sum(scores) / len(scores) if scores else 0

    all_issues = []
    for comp in comparisons:
        # AI Vision mode checks / AI 视觉模式检查项
        for check in comp.get("checks", []):
            if check.get("issue"):
                all_issues.append({
                    "view": comp["view"],
                    "feature": check["feature"],
                    "issue": check["issue"],
                })
        # Missing features / 缺失特征
        for mf in comp.get("missing_features", []):
            all_issues.append({
                "view": comp["view"],
                "feature": mf,
                "issue": "Missing in model / 模型中缺失",
                "severity": "HIGH"
            })
        # OpenCV suggestions / OpenCV 建议
        for s in comp.get("suggestions", []):
            all_issues.append({
                "view": comp.get("view", "?"),
                "feature": "-",
                "issue": s,
            })

    return {
        "avg_score": round(avg_score, 1),
        "verdict": "PASS" if avg_score >= 80 else "WARN" if avg_score >= 60 else "FAIL",
        "n_views": len(comparisons),
        "n_issues": len(all_issues),
        "issues": all_issues,
        "per_view": [
            {"view": c.get("view"), "score": c.get("overall_score", 0),
             "match": c.get("overall_match", "?")}
            for c in comparisons
        ],
        "suggestions": list({s for c in comparisons for s in c.get("suggestions", [])})
    }


# ──────────────────────────────────────────────
# 8. Main Flow / Layer 2 主流程
# ──────────────────────────────────────────────

def layer2_verify(solid, contract, ref_images_dir, output_dir, mode="auto"):
    """
    Layer 2 visual comparison main flow.
    Layer 2 视觉比对主流程。

    Args:
        solid: build123d solid object
        contract: parsed contract dict (from YAML)
        ref_images_dir: directory containing reference images
        output_dir: directory for screenshots and comparison outputs
        mode: "auto", "ai_vision", "opencv", "manual", or "skip"

    Returns:
        dict with verdict (PASS/WARN/FAIL/SKIP/MANUAL_REVIEW)
    """
    if mode == "auto":
        mode = decide_layer2_mode(contract, ref_images_dir)

    if mode == "skip":
        return {"verdict": "SKIP", "reason": "No reference images available"}

    # V1: Generate screenshots / 截图
    screenshots = generate_screenshots(solid, output_dir)
    if screenshots["status"] == "SKIP":
        if mode in ("ai_vision", "opencv"):
            mode = "manual"  # degrade if can't screenshot / 无法截图则降级

    # Collect reference images / 收集参考图
    ref_images = match_ref_to_views(ref_images_dir, contract)

    if mode == "ai_vision":
        comparisons = []
        for view, ref_path in ref_images.items():
            model_path = screenshots.get("screenshots", {}).get(view)
            if model_path:
                r = visual_compare_ai(ref_path, model_path, view, contract)
                comparisons.append(r)
        if not comparisons:
            return {"verdict": "SKIP", "reason": "No matching view pairs"}
        return generate_visual_report(comparisons, contract)

    elif mode == "opencv":
        comparisons = []
        for view, ref_path in ref_images.items():
            model_path = screenshots.get("screenshots", {}).get(view)
            if model_path:
                r = visual_compare_opencv(ref_path, model_path, view)
                comparisons.append(r)
        if not comparisons:
            return {"verdict": "SKIP", "reason": "No matching view pairs"}
        return generate_visual_report(comparisons, contract)

    elif mode == "manual":
        compare_images = []
        for view, ref_path in ref_images.items():
            model_path = screenshots.get("screenshots", {}).get(view)
            if model_path:
                path = visual_compare_manual(ref_path, model_path, view, output_dir)
                compare_images.append(path)
            else:
                # No model screenshot, just note the reference / 无模型截图，仅记录参考图
                pass
        return {
            "verdict": "MANUAL_REVIEW",
            "compare_images": compare_images,
            "message": "Side-by-side comparison images generated for manual review"
        }

    return {"verdict": "SKIP", "reason": f"Unknown mode: {mode}"}


# ──────────────────────────────────────────────
# 9. Pretty Print Report / 格式化报告输出
# ──────────────────────────────────────────────

def print_report(report, mode):
    """Print formatted Layer 2 report to terminal."""
    verdict = report.get("verdict", "?")
    v_icon = {"PASS": "\u2705", "WARN": "\u26a0\ufe0f", "FAIL": "\u274c",
              "SKIP": "\u23ed\ufe0f", "MANUAL_REVIEW": "\U0001f441\ufe0f"}.get(verdict, "?")

    print()
    print("=" * 50)
    print(f"  Layer 2 Visual Verification Report")
    print("=" * 50)
    print(f"  Mode: {mode}")

    if verdict in ("SKIP", "MANUAL_REVIEW"):
        msg = report.get("reason") or report.get("message", "")
        print(f"  Verdict: {v_icon} {verdict}")
        if msg:
            print(f"  {msg}")
        if "compare_images" in report:
            print(f"  Generated {len(report['compare_images'])} comparison images:")
            for p in report["compare_images"]:
                print(f"    {p}")
        print("=" * 50)
        return

    print(f"  Views checked: {report.get('n_views', 0)}")
    for pv in report.get("per_view", []):
        s = pv.get("score", 0)
        icon = "\u2705" if s >= 80 else "\u26a0\ufe0f" if s >= 60 else "\u274c"
        print(f"    {pv['view']:8s} {s:5.1f}/100  {icon}")

    avg = report.get("avg_score", 0)
    print(f"  Avg score: {avg:.1f}")
    print(f"  Issues: {report.get('n_issues', 0)}")
    print(f"  Verdict: {v_icon} {verdict}")

    if report.get("issues"):
        print()
        print("  Issues:")
        for i, issue in enumerate(report["issues"][:10], 1):
            print(f"    {i}. [{issue.get('view', '?')}] {issue.get('feature', '-')}: {issue.get('issue', '')}")

    if report.get("suggestions"):
        print()
        print("  Suggestions:")
        for s in report["suggestions"][:5]:
            print(f"    - {s}")

    print("=" * 50)


# ──────────────────────────────────────────────
# 10. CLI Entry Point / 命令行入口
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Layer 2 Visual Comparison Tool / Layer 2 视觉比对验证工具")
    parser.add_argument("--contract", required=True, help="Path to contract.yaml")
    parser.add_argument("--ref-dir", default=None, help="Directory containing reference images")
    parser.add_argument("--output-dir", default="output/visual", help="Output directory for screenshots and comparisons")
    parser.add_argument("--mode", choices=["auto", "ai_vision", "opencv", "manual", "skip"],
                        default="auto", help="Comparison mode (default: auto)")
    parser.add_argument("--screenshots-only", action="store_true",
                        help="Only generate model screenshots, no comparison")
    parser.add_argument("--json", action="store_true", help="Output report as JSON")

    args = parser.parse_args()

    # Load contract / 加载合同
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML required. Install: pip install pyyaml")
        sys.exit(1)

    with open(args.contract, "r") as f:
        contract = yaml.safe_load(f)

    os.makedirs(args.output_dir, exist_ok=True)

    if args.screenshots_only:
        print("Screenshots-only mode: requires a running OCP Viewer with a loaded solid.")
        print("Use layer2_verify() programmatically for full comparison.")
        sys.exit(0)

    # Mode decision / 模式决策
    mode = args.mode
    if mode == "auto":
        mode = decide_layer2_mode(contract, args.ref_dir)
        print(f"Auto-detected mode: {mode}")

    if mode == "skip":
        report = {"verdict": "SKIP", "reason": "No reference images available"}
    elif mode in ("ai_vision", "opencv"):
        # Without a solid object, we can only do file-based comparison
        # if screenshots already exist / 如果截图已存在，直接比对文件
        ref_images = match_ref_to_views(args.ref_dir, contract)
        if not ref_images:
            report = {"verdict": "SKIP", "reason": "No reference images matched to views"}
        else:
            # Look for existing screenshots in output dir / 查找输出目录中已有的截图
            comparisons = []
            for view, ref_path in ref_images.items():
                model_path = os.path.join(args.output_dir, f"model_{view}.png")
                if os.path.exists(model_path):
                    if mode == "ai_vision":
                        r = visual_compare_ai(ref_path, model_path, view, contract)
                    else:
                        r = visual_compare_opencv(ref_path, model_path, view)
                    comparisons.append(r)
            if comparisons:
                report = generate_visual_report(comparisons, contract)
            else:
                report = {"verdict": "SKIP",
                          "reason": "No model screenshots found. Run with a solid object or generate screenshots first."}
    elif mode == "manual":
        ref_images = match_ref_to_views(args.ref_dir, contract)
        compare_images = []
        for view, ref_path in ref_images.items():
            model_path = os.path.join(args.output_dir, f"model_{view}.png")
            if os.path.exists(model_path):
                path = visual_compare_manual(ref_path, model_path, view, args.output_dir)
                compare_images.append(path)
        report = {
            "verdict": "MANUAL_REVIEW",
            "compare_images": compare_images,
            "message": f"Generated {len(compare_images)} comparison images"
        }
    else:
        report = {"verdict": "SKIP", "reason": f"Unknown mode: {mode}"}

    # Output / 输出
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report, mode)

    # Exit code / 退出码
    v = report.get("verdict", "FAIL")
    sys.exit(0 if v in ("PASS", "SKIP", "MANUAL_REVIEW") else 1 if v == "WARN" else 2)


if __name__ == "__main__":
    main()

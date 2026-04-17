#!/usr/bin/env python3
"""Generate synthetic phone images for unit tests.
合成手机测试图（已知 bbox + 特征位置 + 比例尺）用于单元测试。
"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).parent
PHONE_L_MM = 160.0
PHONE_W_MM = 75.0
PX_PER_MM = 5.0
BBOX_PAD = 40

def px(mm: float) -> int:
    return int(round(mm * PX_PER_MM))

def make_front() -> Image.Image:
    canvas_w = px(PHONE_W_MM) + BBOX_PAD * 2
    canvas_h = px(PHONE_L_MM) + BBOX_PAD * 2
    img = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(img)
    x0, y0 = BBOX_PAD, BBOX_PAD
    x1, y1 = x0 + px(PHONE_W_MM), y0 + px(PHONE_L_MM)
    draw.rectangle([x0, y0, x1, y1], fill=(40, 40, 40), outline=(0, 0, 0), width=2)
    screen_pad = px(3.0)
    draw.rectangle(
        [x0 + screen_pad, y0 + screen_pad, x1 - screen_pad, y1 - screen_pad],
        fill=(20, 20, 80),
    )
    cam_cx = x0 + px(PHONE_W_MM / 2)
    cam_cy = y0 + px(8.0)
    draw.ellipse([cam_cx - 8, cam_cy - 8, cam_cx + 8, cam_cy + 8], fill=(0, 0, 0))
    return img

def make_back() -> Image.Image:
    canvas_w = px(PHONE_W_MM) + BBOX_PAD * 2
    canvas_h = px(PHONE_L_MM) + BBOX_PAD * 2
    img = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(img)
    x0, y0 = BBOX_PAD, BBOX_PAD
    x1, y1 = x0 + px(PHONE_W_MM), y0 + px(PHONE_L_MM)
    draw.rectangle([x0, y0, x1, y1], fill=(180, 180, 180), outline=(0, 0, 0), width=2)
    cam_x = x0 + px(8.0)
    cam_y = y0 + px(8.0)
    cam_w = px(35.0)
    cam_h = px(35.0)
    draw.rectangle(
        [cam_x, cam_y, cam_x + cam_w, cam_y + cam_h],
        fill=(30, 30, 30),
        outline=(0, 0, 0),
        width=2,
    )
    return img

def main() -> None:
    front = make_front()
    back = make_back()
    front.save(OUT_DIR / "synthetic_phone_front.png")
    back.save(OUT_DIR / "synthetic_phone_back.png")
    meta = {
        "phone_length_mm": PHONE_L_MM,
        "phone_width_mm": PHONE_W_MM,
        "px_per_mm": PX_PER_MM,
        "bbox_pad_px": BBOX_PAD,
        "front_bbox_px": [BBOX_PAD, BBOX_PAD, px(PHONE_W_MM), px(PHONE_L_MM)],
        "back_bbox_px": [BBOX_PAD, BBOX_PAD, px(PHONE_W_MM), px(PHONE_L_MM)],
        "front_camera_center_px": [BBOX_PAD + px(PHONE_W_MM / 2), BBOX_PAD + px(8.0)],
        "back_camera_bbox_px": [BBOX_PAD + px(8.0), BBOX_PAD + px(8.0), px(35.0), px(35.0)],
    }
    import json
    (OUT_DIR / "fixtures_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"Wrote {OUT_DIR}/synthetic_phone_front.png")
    print(f"Wrote {OUT_DIR}/synthetic_phone_back.png")
    print(f"Wrote {OUT_DIR}/fixtures_meta.json")

if __name__ == "__main__":
    main()

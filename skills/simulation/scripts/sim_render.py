#!/usr/bin/env python3
"""无头离屏渲染 helper —— 给 run_sim.py 出关键帧 PNG(+ best-effort MP4)。

用 pybullet 自带的软渲染器 `getCameraImage(renderer=ER_TINY_RENDERER)`:CPU 光栅化,
p.DIRECT 无 GL context 也能跑(`ER_BULLET_HARDWARE_OPENGL` 需 GL/EGL,headless 会失败)。

PNG 写出兜底链:PIL → imageio → `.npy` + manifest(pybullet 本身没有 PNG 编码器)。
MP4 best-effort:imageio → cv2 → 跳过(只写 frames/manifest.json,给后续 ffmpeg 拼)。
**绝不 shell 调 ffmpeg 二进制**(不保证机器上有)。

也可单跑做单帧调试:
    <venv>/bin/python sim_render.py <model.urdf> [--out /tmp/one.png]
"""
from __future__ import annotations

import json
import os
import sys


def make_camera(p, target, *, dist=1.0, yaw=45.0, pitch=-30.0, width=640, height=460):
    """构造 view + projection 矩阵(对准 target)。"""
    view = p.computeViewMatrixFromYawPitchRoll(
        cameraTargetPosition=list(target),
        distance=dist, yaw=yaw, pitch=pitch, roll=0, upAxisIndex=2,
    )
    aspect = float(width) / float(height) if height else 1.0
    proj = p.computeProjectionMatrixFOV(fov=60.0, aspect=aspect, nearVal=0.01, farVal=100.0)
    return view, proj


def _rgb_array(p, width, height, view, proj):
    """getCameraImage → (h, w, 3) uint8 ndarray。用返回的 w,h(pybullet 可能 clamp)。"""
    import numpy as np

    w, h, rgba, _depth, _seg = p.getCameraImage(
        width, height, view, proj, renderer=p.ER_TINY_RENDERER,
    )
    arr = np.asarray(rgba, dtype=np.uint8).reshape(h, w, 4)
    return arr[:, :, :3]


def capture_frame(p, body, *, width, height, out_path, dist=None):
    """渲染当前帧到 out_path(PNG)。返回实际写出的路径(兜底可能是 .npy)。"""
    pos, _ = p.getBasePositionAndOrientation(body)
    # 相机距离:给定优先,否则按 base 高度粗估,保证机器人在视野里
    d = dist if dist is not None else max(0.6, abs(pos[2]) * 2 + 0.8)
    view, proj = make_camera(p, pos, dist=d, width=width, height=height)
    rgb = _rgb_array(p, width, height, view, proj)
    return _write_png(rgb, out_path)


def _write_png(rgb, out_path):
    """PIL → imageio → .npy 兜底。返回实际路径。"""
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    try:
        from PIL import Image

        Image.fromarray(rgb, "RGB").save(out_path)
        return out_path
    except Exception:
        pass
    try:
        import imageio.v2 as imageio

        imageio.imwrite(out_path, rgb)
        return out_path
    except Exception:
        pass
    # 最后兜底:落 .npy,绝不静默丢帧
    import numpy as np

    npy = os.path.splitext(out_path)[0] + ".npy"
    np.save(npy, rgb)
    return npy


def write_video(frames_dir, out_mp4, fps=20):
    """把 frames_dir 下 frame_*.png 拼成 MP4。imageio → cv2 → False。"""
    pngs = sorted(
        os.path.join(frames_dir, f)
        for f in os.listdir(frames_dir)
        if f.startswith("frame_") and f.endswith(".png")
    )
    if not pngs:
        return False
    # imageio(+imageio-ffmpeg)
    try:
        import imageio.v2 as imageio

        with imageio.get_writer(out_mp4, fps=fps) as w:
            for fp in pngs:
                w.append_data(imageio.imread(fp))
        return True
    except Exception:
        pass
    # cv2
    try:
        import cv2

        first = cv2.imread(pngs[0])
        h, w = first.shape[:2]
        vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        for fp in pngs:
            vw.write(cv2.imread(fp))
        vw.release()
        return True
    except Exception:
        return False


def write_manifest(frames_dir, fps=20):
    """无法直接出 MP4 时,落 manifest 让后续可复现拼帧。"""
    pngs = sorted(
        f for f in os.listdir(frames_dir)
        if f.startswith("frame_") and f.endswith(".png")
    )
    manifest = {
        "fps": fps,
        "frames": pngs,
        "cmd_hint": f"ffmpeg -r {fps} -i frame_%04d.png -pix_fmt yuv420p out.mp4",
        "note": "本机缺 imageio/cv2,未直接出 MP4;PNG 关键帧已落盘,可用上面命令离线拼。",
    }
    path = os.path.join(frames_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return path


def _main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description="单帧离屏渲染调试")
    ap.add_argument("model", help="URDF 文件(单帧 sanity 渲染)")
    ap.add_argument("--out", default="/tmp/sim_render_one.png")
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=460)
    args = ap.parse_args(argv)

    try:
        import pybullet as p
        import pybullet_data
    except ImportError:
        sys.exit("缺 pybullet。用装了 pybullet 的解释器跑"
                 "(如 ~/work/build123d-parts-lib/.venv/bin/python);或 pip install pybullet。")

    cid = p.connect(p.DIRECT)
    try:
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setAdditionalSearchPath(os.path.dirname(os.path.abspath(args.model)))
        body = p.loadURDF(args.model, basePosition=[0, 0, 0.3])
        out = capture_frame(p, body, width=args.width, height=args.height, out_path=args.out)
        print("写出:", out)
    finally:
        p.disconnect(cid)


if __name__ == "__main__":
    _main()

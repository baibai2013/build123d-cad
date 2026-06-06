#!/usr/bin/env python3
"""动力学仿真自验 —— run_sim 跑一次,断言稳定性,出 AI 视觉小图 + checklist。

哲学对标 skills/urdf/scripts/verify_urdf.py(render-verify),但用 pybullet 内置渲染器
而非浏览器 viewer。in-process import run_sim.simulate() 跑一次再判,不重复跑。

四项断言(阈值见 references/stability-checks.md):
  ① 没穿地     min_base_z > FLOOR_EPS
  ② 没数值爆炸  max|pos|<POS_CAP、max|jvel|<VEL_CAP、无 NaN/Inf
  ③ 关节在限位  每采样 joint_pos ∈ [lower-TOL, upper+TOL](跳过连续关节)
  ④ 末态稳     hold/gait: |roll|,|pitch| < FLIP_DEG;passive: 末速 < SETTLE_VEL

产物:<outdir>/_verify/{static.png, settled.png, checklist.txt} + checks 回填进 results.json。
退出码:0 全过 / 1 ≥1 项挂 / 2 输入错 / 3 缺 pybullet。

用法:
    verify_sim.py <model.urdf|.sdf> [--mode passive|hold|gait] [--steps] [--gait]
        [--fixed] [--base-z] [--outdir DIR] [--width 640] [--height 460]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_sim  # noqa: E402

# ---- 阈值 ----
FLOOR_EPS = -0.10     # 基座 z 全程须 > 此值(没穿透 z=0 地面)
POS_CAP = 1e3         # 基座位置任一轴绝对值上限
VEL_CAP = 1e3         # 关节速度绝对值上限
JOINT_TOL = 0.10      # 关节限位容差(rad)
FLIP_DEG = 80.0       # roll/pitch 超此值视为翻车
SETTLE_VEL = 1.0      # passive 末态基座线速度模(m/s)上限


def _check(record):
    """对 record 跑四项断言,返回 {name: {pass, detail}} 并回填 record['checks']。"""
    s = record["summary"]
    mode = record["meta"]["mode"]
    checks = {}

    # ① 没穿地
    mbz = s.get("min_base_z")
    checks["no_floor_tunnel"] = {
        "pass": mbz is not None and mbz > FLOOR_EPS,
        "detail": f"min_base_z={mbz} (须 > {FLOOR_EPS})",
    }

    # ② 没数值爆炸
    blew = (s.get("nan_or_inf") or s.get("max_pos", 0) >= POS_CAP
            or s.get("max_joint_vel", 0) >= VEL_CAP)
    checks["no_blowup"] = {
        "pass": not blew,
        "detail": f"max_pos={s.get('max_pos')} max_joint_vel={s.get('max_joint_vel')} "
                  f"nan_or_inf={s.get('nan_or_inf')}",
    }

    # ③ 关节在限位(movable = type in (0,1),与 timeseries.joint_pos 同序)
    movable = [j for j in record["joints"] if j["type"] in (0, 1)]
    worst = None
    ok = True
    for rec in record["timeseries"]:
        for j, q in zip(movable, rec["joint_pos"]):
            if j["upper"] <= j["lower"]:  # 连续/无限位关节
                continue
            if q < j["lower"] - JOINT_TOL or q > j["upper"] + JOINT_TOL:
                ok = False
                over = max(j["lower"] - q, q - j["upper"])
                if worst is None or over > worst[1]:
                    worst = (j["name"], over, q, j["lower"], j["upper"])
    detail = "全部在限位内" if ok else (
        f"越界最甚: {worst[0]} q={worst[2]:.3f} 超 {worst[1]:.3f} rad "
        f"(范围 [{worst[3]:.3f}, {worst[4]:.3f}])")
    checks["joints_within_limits"] = {"pass": ok, "detail": detail}

    # ④ 末态稳
    if mode == "passive":
        v = s.get("final_base_vel_norm")
        checks["settled"] = {
            "pass": v is not None and v < SETTLE_VEL,
            "detail": f"passive 末态线速度模={v} (须 < {SETTLE_VEL})",
        }
    else:
        rpy = s.get("final_rpy") or [0, 0, 0]
        roll_d, pitch_d = abs(math.degrees(rpy[0])), abs(math.degrees(rpy[1]))
        checks["settled"] = {
            "pass": roll_d < FLIP_DEG and pitch_d < FLIP_DEG,
            "detail": f"{mode} 末态 |roll|={roll_d:.1f}° |pitch|={pitch_d:.1f}° (须 < {FLIP_DEG}°)",
        }

    record["checks"] = {k: v["pass"] for k, v in checks.items()}
    return checks


def _emit_verify_imgs(record, outdir):
    """从已渲染关键帧复制 static(首)/settled(末)到 _verify/。"""
    vdir = os.path.join(outdir, "_verify")
    os.makedirs(vdir, exist_ok=True)
    frames = record.get("frames", [])
    static = settled = ""
    if frames:
        first = os.path.join(outdir, frames[0]["path"])
        last = os.path.join(outdir, frames[-1]["path"])
        if os.path.exists(first):
            static = os.path.join(vdir, "static.png")
            shutil.copyfile(first, static)
        if os.path.exists(last):
            settled = os.path.join(vdir, "settled.png")
            shutil.copyfile(last, settled)
    return vdir, static, settled


CHECK_LABELS = {
    "no_floor_tunnel": "① 没穿地(base_z 全程 > 地面)",
    "no_blowup": "② 没数值爆炸(pos/vel 有界、无 NaN)",
    "joints_within_limits": "③ 关节全程在限位内",
    "settled": "④ 末态稳定(passive 静止 / hold·gait 没翻车)",
}


def main(argv=None):
    ap = argparse.ArgumentParser(description="无头动力学仿真自验")
    ap.add_argument("model")
    ap.add_argument("--mode", default="hold", choices=["passive", "hold", "gait"])
    ap.add_argument("--steps", type=int, default=2400)
    ap.add_argument("--gait", default="trot", choices=list(run_sim.GAITS.keys()))
    ap.add_argument("--fixed", action="store_true")
    ap.add_argument("--base-z", type=float, default=0.3)
    ap.add_argument("--outdir", default="")
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=460)
    args = ap.parse_args(argv)

    if not os.path.exists(args.model):
        print(f"输入错误:模型文件不存在 {args.model}", file=sys.stderr)
        return 2
    ext = os.path.splitext(args.model)[1].lower()
    if ext not in (".urdf", ".sdf"):
        print(f"输入错误:不认识的后缀 {ext}(只收 .urdf/.sdf)", file=sys.stderr)
        return 2

    try:
        import pybullet  # noqa: F401
    except ImportError:
        print("缺 pybullet。用装了 pybullet 的解释器跑"
              "(如 ~/work/build123d-parts-lib/.venv/bin/python);或 pip install pybullet。",
              file=sys.stderr)
        return 3

    # 跑一次(出全部关键帧,供 static/settled 取首末帧)
    record = run_sim.simulate(
        args.model, mode=args.mode, steps=args.steps, gait=args.gait,
        fixed=args.fixed, base_z=args.base_z, outdir=(args.outdir or None),
        width=args.width, height=args.height, no_video=False,
    )
    outdir = os.path.dirname(record["_results_path"])

    checks = _check(record)
    vdir, static, settled = _emit_verify_imgs(record, outdir)

    # 回填 checks 进 results.json
    with open(record["_results_path"], "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in record.items() if not k.startswith("_")},
                  f, ensure_ascii=False, indent=2)

    # checklist.txt + stdout
    all_pass = all(c["pass"] for c in checks.values())
    lines = [f"模型: {args.model}", f"模式: {args.mode}"
             + (f" / 步态 {args.gait}" if args.mode == "gait" else ""),
             f"采样: {record['summary']['n_samples']}  退出码: {0 if all_pass else 1}", ""]
    for key, label in CHECK_LABELS.items():
        c = checks[key]
        lines.append(f"[{'PASS' if c['pass'] else 'FAIL'}] {label} —— {c['detail']}")
    lines += ["",
              "⑤ 看图核对:static.png(初始) → settled.png(末态):姿态合理、没下陷、没翻、没飞出视野。",
              f"static : {static or '(无帧)'}",
              f"settled: {settled or '(无帧)'}"]
    checklist = "\n".join(lines)
    with open(os.path.join(vdir, "checklist.txt"), "w", encoding="utf-8") as f:
        f.write(checklist + "\n")

    print(checklist)
    print(f"\nresults: {record['_results_path']}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())

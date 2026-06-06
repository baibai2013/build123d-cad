#!/usr/bin/env python3
"""无头动力学仿真 producer —— 把 URDF/SDF 丢进 pybullet HEADLESS(p.DIRECT)跑 N 步。

三种控制模式:passive(跌落/穿地测试)/ hold(位置保持/站立)/ gait(简单相位步态)。
记录时序(关节角 / 基座位姿 / 速度 / 接触)→ <stem>.results.json;
按 --fps 调 sim_render 出关键帧 PNG(+ best-effort MP4)。

用法(需装了 pybullet 的解释器,如 ~/work/build123d-parts-lib/.venv/bin/python):
    run_sim.py <model.urdf|.sdf> [--mode passive|hold|gait] [--steps 2400]
        [--gait stand|trot|crawl] [--fixed] [--base-z 0.3] [--outdir DIR]
        [--fps 20] [--width 640] [--height 460] [--no-video]

判定不在本脚本 —— 见 verify_sim.py(import 本模块 simulate() 跑一次再断言)。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

# 让单文件直跑时也能 import 同目录的 sim_render
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim_render  # noqa: E402

DT = 1.0 / 240.0

# 简单步态:相位偏置 + 正弦驱动(MVP,非 Bezier+IK;完整步态见 references/control-modes.md)。
GAITS = {
    "stand": {"phases": [0, 0, 0, 0], "amp": 0.0, "period": 1.0},
    "trot":  {"phases": [0, 0.5, 0.5, 0], "amp": 0.35, "period": 0.8},
    "crawl": {"phases": [0, 0.25, 0.5, 0.75], "amp": 0.25, "period": 2.0},
}


def _fail_no_pybullet():
    sys.exit("缺 pybullet。用装了 pybullet 的解释器跑"
             "(如 ~/work/build123d-parts-lib/.venv/bin/python);或 pip install pybullet。")


def get_joint_info(p, body):
    """关节映射:name → {index, type, lower, upper}(lift 自 mechanical pybullet_preview)。"""
    joints = {}
    for i in range(p.getNumJoints(body)):
        info = p.getJointInfo(body, i)
        joints[info[1].decode()] = {
            "index": i, "type": info[2],
            "lower": float(info[8]), "upper": float(info[9]),
        }
    return joints


def _movable(joints):
    return {n: j for n, j in joints.items() if j["type"] in (0, 1)}  # revolute/prismatic


def _safe_target(j):
    """限位中点;连续关节(lower>=upper)回 0。"""
    return (j["lower"] + j["upper"]) / 2.0 if j["upper"] > j["lower"] else 0.0


def simulate(model, *, mode="hold", steps=2400, gait="trot", fixed=False,
             base_z=0.3, outdir=None, fps=20, width=640, height=460,
             no_video=False, self_collision=True):
    """跑一次无头仿真,落盘产物,返回 record dict(供 verify_sim 复用)。"""
    try:
        import pybullet as p
        import pybullet_data
    except ImportError:
        _fail_no_pybullet()
    import numpy as np

    if not os.path.exists(model):
        sys.exit(f"模型文件不存在: {model}")
    ext = os.path.splitext(model)[1].lower()
    if ext not in (".urdf", ".sdf"):
        sys.exit(f"不认识的后缀 {ext}(只收 .urdf/.sdf);不静默吞。")

    model = os.path.abspath(model)
    stem = os.path.splitext(os.path.basename(model))[0]
    outdir = os.path.abspath(outdir) if outdir else os.path.join(os.path.dirname(model), "simulation")
    frames_dir = os.path.join(outdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    cid = p.connect(p.DIRECT)  # 永远 headless,绝不 GUI
    try:
        p.setAdditionalSearchPath(pybullet_data.getDataPath())     # plane.urdf
        p.setAdditionalSearchPath(os.path.dirname(model))          # 解析相对 meshes/
        p.setGravity(0, 0, -9.81)
        p.setTimeStep(DT)

        plane = -1
        if ext == ".urdf":
            plane = p.loadURDF("plane.urdf")
            body = p.loadURDF(
                model, basePosition=[0, 0, base_z], useFixedBase=fixed,
                flags=(p.URDF_USE_SELF_COLLISION if self_collision else 0),
            )
        else:  # .sdf —— loadSDF 返回 tuple,世界自带地面,不再叠 plane
            ids = p.loadSDF(model)
            if not ids:
                sys.exit(f"loadSDF 没返回任何 body: {model}")
            body = ids[0]
            p.resetBasePositionAndOrientation(body, [0, 0, base_z], [0, 0, 0, 1])

        joints = get_joint_info(p, body)
        movable = _movable(joints)
        if mode in ("hold", "gait") and not movable:
            print(f"⚠ 模型无可动关节,{mode} 退化为 passive。", file=sys.stderr)
            mode = "passive"

        g = GAITS.get(gait, GAITS["trot"])
        sample_every = max(1, int(round((1.0 / fps) / DT)))  # 每多少步采一帧

        timeseries, frames = [], []
        nan_seen = False
        idx = 0
        for step in range(steps):
            t = step * DT
            # ---- 控制 ----
            if mode == "hold":
                for j in movable.values():
                    p.setJointMotorControl2(body, j["index"], p.POSITION_CONTROL,
                                            targetPosition=_safe_target(j), force=5.0)
            elif mode == "gait":
                legs = list(movable.values())
                for li, j in enumerate(legs):
                    phase = g["phases"][li % 4]
                    target = _safe_target(j) + g["amp"] * math.sin(
                        2 * math.pi * (t / g["period"] + phase))
                    if j["upper"] > j["lower"]:
                        target = min(max(target, j["lower"]), j["upper"])
                    p.setJointMotorControl2(body, j["index"], p.POSITION_CONTROL,
                                            targetPosition=target, force=5.0)
            # passive: 不施加控制

            p.stepSimulation()

            # ---- 采样 ----
            if step % sample_every == 0 or step == steps - 1:
                pos, orn = p.getBasePositionAndOrientation(body)
                rpy = p.getEulerFromQuaternion(orn)
                lin, _ang = p.getBaseVelocity(body)
                jstates = p.getJointStates(body, [j["index"] for j in movable.values()]) if movable else []
                jpos = [s[0] for s in jstates]
                jvel = [s[1] for s in jstates]
                contacts = p.getContactPoints(body, plane) if plane >= 0 else p.getContactPoints(body)
                fn = float(sum(c[9] for c in contacts)) if contacts else 0.0
                rec = {
                    "t": round(t, 4),
                    "base_pos": [round(v, 5) for v in pos],
                    "base_rpy": [round(v, 5) for v in rpy],
                    "base_vel": [round(v, 5) for v in lin],
                    "joint_pos": [round(v, 5) for v in jpos],
                    "joint_vel": [round(v, 5) for v in jvel],
                    "contacts": {"count": len(contacts), "total_normal_force": round(fn, 3)},
                }
                if any(not math.isfinite(v) for v in list(pos) + list(lin) + jpos + jvel):
                    nan_seen = True
                timeseries.append(rec)
                # 关键帧
                if not no_video or idx == 0:
                    fpath = os.path.join(frames_dir, f"frame_{idx:04d}.png")
                    try:
                        written = sim_render.capture_frame(
                            p, body, width=width, height=height, out_path=fpath)
                        frames.append({"idx": idx, "t": round(t, 4),
                                       "path": os.path.relpath(written, outdir)})
                    except Exception as e:  # 渲染失败不该让仿真整体挂
                        print(f"⚠ 帧 {idx} 渲染失败: {e}", file=sys.stderr)
                idx += 1

        # ---- 汇总 ----
        base_z_series = [r["base_pos"][2] for r in timeseries]
        all_pos = [abs(v) for r in timeseries for v in r["base_pos"]]
        all_jvel = [abs(v) for r in timeseries for v in r["joint_vel"]]
        last = timeseries[-1] if timeseries else {}
        summary = {
            "min_base_z": round(min(base_z_series), 5) if base_z_series else None,
            "max_pos": round(max(all_pos), 5) if all_pos else 0.0,
            "max_joint_vel": round(max(all_jvel), 5) if all_jvel else 0.0,
            "final_rpy": last.get("base_rpy"),
            "final_base_vel_norm": round(
                math.sqrt(sum(v * v for v in last.get("base_vel", [0, 0, 0]))), 5) if last else None,
            "nan_or_inf": nan_seen,
            "n_samples": len(timeseries),
        }

        record = {
            "meta": {
                "model": model, "mode": mode, "gait": gait if mode == "gait" else None,
                "steps": steps, "dt": DT, "fps": fps,
                "pybullet_api": p.getAPIVersion(),
            },
            "joints": [{"name": n, **{k: j[k] for k in ("index", "type", "lower", "upper")}}
                       for n, j in joints.items()],
            "timeseries": timeseries,
            "summary": summary,
            "frames": frames,
            "checks": {},  # 由 verify_sim 填
        }
    finally:
        p.disconnect(cid)

    # ---- 落盘 ----
    results_path = os.path.join(outdir, f"{stem}.results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    record["_results_path"] = results_path

    # cad 引擎原生轨迹(供 viewer 3D 回放),失败不致命
    try:
        import to_trajectory
        traj_path = os.path.join(outdir, f"{stem}.trajectory.json")
        to_trajectory.write_trajectory(results_path, traj_path)
        record["_trajectory_path"] = traj_path
    except Exception as e:
        print(f"⚠ 轨迹文件生成失败(不影响 results.json): {e}", file=sys.stderr)

    # MP4 best-effort
    if not no_video and frames:
        mp4 = os.path.join(outdir, f"{stem}.sim.mp4")
        if sim_render.write_video(frames_dir, mp4, fps=fps):
            print("MP4:", mp4)
            record["_mp4_path"] = mp4
        else:
            man = sim_render.write_manifest(frames_dir, fps=fps)
            print(f"未直接出 MP4(缺 imageio/cv2);PNG 关键帧 + manifest 已落: {man}")
    return record


def main(argv=None):
    ap = argparse.ArgumentParser(description="无头 pybullet 动力学仿真")
    ap.add_argument("model", help="URDF 或 SDF 文件")
    ap.add_argument("--mode", default="hold", choices=["passive", "hold", "gait"])
    ap.add_argument("--steps", type=int, default=2400, help="步数(1/240 s/步,2400≈10s)")
    ap.add_argument("--gait", default="trot", choices=list(GAITS.keys()))
    ap.add_argument("--fixed", action="store_true", help="固定基座(调试)")
    ap.add_argument("--base-z", type=float, default=0.3)
    ap.add_argument("--outdir", default="")
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=460)
    ap.add_argument("--no-video", action="store_true", help="只出 frame_0000 + results,不拼 MP4")
    args = ap.parse_args(argv)

    rec = simulate(
        args.model, mode=args.mode, steps=args.steps, gait=args.gait,
        fixed=args.fixed, base_z=args.base_z, outdir=(args.outdir or None),
        fps=args.fps, width=args.width, height=args.height, no_video=args.no_video,
    )
    s = rec["summary"]
    print(f"results: {rec['_results_path']}")
    print(f"  mode={rec['meta']['mode']} samples={s['n_samples']} "
          f"min_base_z={s['min_base_z']} max_pos={s['max_pos']} "
          f"max_joint_vel={s['max_joint_vel']} nan={s['nan_or_inf']}")
    if rec.get("_trajectory_path"):
        print(f"trajectory: {rec['_trajectory_path']}")
        print("预览(3D 回放): 在 viewer cad 引擎打开 URDF 并带 "
              f"?trajectory=<上面的 trajectory.json>;数据面板: viewer 打开 {os.path.basename(rec['_results_path'])}(engine=sim)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

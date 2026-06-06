#!/usr/bin/env python3
"""results.json → cad 引擎原生轨迹格式,供 viewer 3D 回放。

cad 引擎(viewer)已内建 playUrdfTrajectory,认这个格式:
    { "points": [ { "timeFromStartSec": <s>, "positionsByNameDeg": {"<joint>": <deg>} }, ... ] }

本脚本把 run_sim 产的 results.json(joint_pos 是弧度、按 movable 关节顺序)转成上面格式:
每个采样时刻 → 关节名→角度(度)。run_sim/verify_sim 跑完会顺带调 to_trajectory(),
也可单独跑:
    to_trajectory.py <robot>.results.json [-o <robot>.trajectory.json]

设计见 docs/simulation-design.md §3/§4。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys


def results_to_trajectory(record):
    """record(results.json 解析后的 dict)→ cad 轨迹格式 dict。"""
    # movable 关节(type 0=revolute / 1=prismatic),与 timeseries.joint_pos 同序
    movable = [j for j in record.get("joints", []) if j.get("type") in (0, 1)]
    names = [j["name"] for j in movable]
    points = []
    for s in record.get("timeseries", []):
        jpos = s.get("joint_pos", [])
        by_name = {
            names[i]: round(math.degrees(jpos[i]), 4)
            for i in range(min(len(names), len(jpos)))
        }
        points.append({
            "timeFromStartSec": s.get("t", 0.0),
            "positionsByNameDeg": by_name,
        })
    return {
        "points": points,
        # 元信息(cad 忽略,人/调试可读):基座位姿轨迹,供后续驱动 root transform
        "meta": {
            "model": record.get("meta", {}).get("model"),
            "mode": record.get("meta", {}).get("mode"),
            "source": "build123d-cad/simulation",
        },
        "basePoses": [
            {"timeFromStartSec": s.get("t", 0.0),
             "positionXyz": s.get("base_pos"), "rpyDeg": [round(math.degrees(v), 4) for v in s.get("base_rpy", [])]}
            for s in record.get("timeseries", [])
        ],
    }


def write_trajectory(results_path, out_path=None):
    """读 results.json,写 trajectory.json(默认同目录 <stem>.trajectory.json),返回路径。"""
    with open(results_path, encoding="utf-8") as f:
        record = json.load(f)
    traj = results_to_trajectory(record)
    if out_path is None:
        d = os.path.dirname(os.path.abspath(results_path))
        stem = os.path.basename(results_path)
        # <robot>.results.json → <robot>.trajectory.json
        stem = stem[:-len(".results.json")] if stem.endswith(".results.json") else os.path.splitext(stem)[0]
        out_path = os.path.join(d, f"{stem}.trajectory.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(traj, f, ensure_ascii=False, indent=2)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description="results.json → cad 轨迹格式")
    ap.add_argument("results", help="<robot>.results.json")
    ap.add_argument("-o", "--out", default="", help="输出路径(默认 <robot>.trajectory.json)")
    args = ap.parse_args(argv)
    if not os.path.exists(args.results):
        print(f"输入错误:文件不存在 {args.results}", file=sys.stderr)
        return 2
    out = write_trajectory(args.results, args.out or None)
    print("trajectory:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

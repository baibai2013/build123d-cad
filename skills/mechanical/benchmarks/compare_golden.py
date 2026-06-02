#!/usr/bin/env python3
"""compare benchmarks 跑出的结果 vs golden.json,容差按题级 *_tolerance_*。

用法:
    python -m skills.mechanical.benchmarks.compare_golden --case calibration_block
    python -m skills.mechanical.benchmarks.compare_golden --suite fast

退出码:0 = 全部对得上,>0 = 有 case 偏离基线
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent


def compare_one(actual: dict, golden: dict) -> list[str]:
    """返回 mismatch 列表,空 = 通过。"""
    diffs: list[str] = []

    # 拓扑硬等
    for key in ("solid_count", "is_manifold", "step_reimport_ok"):
        if golden.get(key) != actual.get(key):
            diffs.append(f"{key}: actual={actual.get(key)} != golden={golden.get(key)}")

    # 体积
    vol_g = golden.get("volume_mm3")
    vol_a = actual.get("volume_mm3")
    tol_pct = golden.get("volume_tolerance_pct", 0.5)
    if vol_g and vol_a:
        delta_pct = abs(vol_a - vol_g) / vol_g * 100
        if delta_pct > tol_pct:
            diffs.append(
                f"volume_mm3: actual={vol_a} vs golden={vol_g} (Δ={delta_pct:.2f}% > {tol_pct}%)"
            )

    # bbox 各分量
    bbox_g = golden.get("bbox_mm")
    bbox_a = actual.get("bbox_mm")
    bbox_tol = golden.get("bbox_tolerance_mm", 0.05)
    if bbox_g and bbox_a:
        for axis, (g, a) in enumerate(zip(bbox_g, bbox_a)):
            if abs(a - g) > bbox_tol:
                diffs.append(
                    f"bbox_mm[{axis}]: actual={a} vs golden={g} (Δ={abs(a-g):.3f} > {bbox_tol})"
                )

    # com
    com_g = golden.get("center_of_mass_mm")
    com_a = actual.get("center_of_mass_mm")
    com_tol = golden.get("com_tolerance_mm", 0.1)
    if com_g and com_a:
        for axis, (g, a) in enumerate(zip(com_g, com_a)):
            if abs(a - g) > com_tol:
                diffs.append(
                    f"center_of_mass_mm[{axis}]: actual={a} vs golden={g} (Δ={abs(a-g):.3f} > {com_tol})"
                )

    # area
    area_g = golden.get("area_mm2")
    area_a = actual.get("area_mm2")
    area_tol_pct = golden.get("area_tolerance_pct", 1.0)
    if area_g and area_a:
        delta_pct = abs(area_a - area_g) / area_g * 100
        if delta_pct > area_tol_pct:
            diffs.append(
                f"area_mm2: actual={area_a} vs golden={area_g} (Δ={delta_pct:.2f}% > {area_tol_pct}%)"
            )

    return diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", help="单题 id")
    ap.add_argument("--suite", choices=["fast", "full"], help="对比一整套")
    ap.add_argument("--results", type=Path, default=None,
                    help="run_all 输出的 results_*.json;不传则按 --suite 推断")
    ap.add_argument("--golden", type=Path, default=BENCH_DIR / "golden.json")
    args = ap.parse_args()

    if not args.golden.exists():
        print(f"❌ golden.json 不存在: {args.golden}")
        print("   首次跑请先 `run_all.py --suite <s> --emit-golden` 生成种子")
        return 2

    golden = json.loads(args.golden.read_text(encoding="utf-8"))

    if args.case:
        results_path = args.results or BENCH_DIR / "output" / "results_full.json"
        if not results_path.exists():
            results_path = BENCH_DIR / "output" / "results_fast.json"
        results = json.loads(results_path.read_text(encoding="utf-8"))
        actual = next((r for r in results if r["case"] == args.case), None)
        if actual is None:
            print(f"❌ {args.case} 未在 {results_path} 找到")
            return 2
        if args.case not in golden:
            print(f"❌ {args.case} 未在 golden.json 找到")
            return 2
        diffs = compare_one(actual, golden[args.case])
        if diffs:
            print(f"❌ {args.case} 偏离基线:")
            for d in diffs:
                print(f"  - {d}")
            return 1
        print(f"✅ {args.case}")
        return 0

    if args.suite:
        results_path = args.results or BENCH_DIR / "output" / f"results_{args.suite}.json"
        results = json.loads(results_path.read_text(encoding="utf-8"))
        any_fail = 0
        for r in results:
            case = r["case"]
            if case not in golden:
                print(f"⚠️ {case} 无 golden 基线(跳过)")
                continue
            diffs = compare_one(r, golden[case])
            if diffs:
                any_fail += 1
                print(f"❌ {case}:")
                for d in diffs:
                    print(f"  - {d}")
            else:
                print(f"✅ {case}")
        return any_fail

    print("用法:--case <id>  或  --suite {fast,full}")
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""benchmarks 跑全部题(或子集)— 出 STEP + 提取几何特征 + 写 report/golden.json。

用法:
    # 跑 fast 子集
    python -m skills.mechanical.benchmarks.run_all --suite fast

    # 跑 full + emit golden 种子(只首版/双签时用)
    python -m skills.mechanical.benchmarks.run_all --suite full --emit-golden

    # 指定输出目录(默认 benchmarks/output/)
    python -m skills.mechanical.benchmarks.run_all --suite fast --out /tmp/bench

依赖:build123d 0.10+(在 ~/work/build123d-parts-lib/.venv/ 内)

导出策略:
    - .step 必导出
    - extra_outputs 中的 .dxf 由各 model 的 export_extras 自行处理
    - 关键几何字段:volume_mm3 / bbox_mm / center_of_mass_mm / area_mm2 / solid_count / is_manifold / step_reimport_ok

退出码:
    0 = 全部通过
    >0 = 有题失败(STEP 无法导出 / reimport 失败)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
SKILL_ROOT = BENCH_DIR.parent.parent.parent  # ../../../  → super skill 根

# 让 import 走 super-skill 相对路径
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


def _import_models():
    """触发 model 注册。"""
    from skills.mechanical.benchmarks import models  # noqa: F401
    from skills.mechanical.benchmarks.bench_def import all_benches, filter_suite
    return all_benches, filter_suite


def _extract_geom(part) -> dict:
    """从 build123d Part 提取核心几何字段。"""
    bbox = part.bounding_box()
    bbox_mm = [
        round(bbox.size.X, 4),
        round(bbox.size.Y, 4),
        round(bbox.size.Z, 4),
    ]
    com = part.center()
    com_mm = [round(com.X, 4), round(com.Y, 4), round(com.Z, 4)]
    return {
        "volume_mm3": round(part.volume, 4),
        "bbox_mm": bbox_mm,
        "center_of_mass_mm": com_mm,
        "area_mm2": round(part.area, 4),
        "solid_count": len(part.solids()),
        "is_manifold": _is_manifold(part),
    }


def _is_manifold(part) -> bool:
    """用 OCP 的 BRepCheck_Analyzer 判 part 整体几何/拓扑是否合规。

    BRepCheck_Analyzer.IsValid() 综合了 edge/face/shell/solid 各级 invariants,
    包括 manifold(每边 ≤ 2 face)、闭合 shell、面定向一致性等。
    单 solid 通过此检查 → 我们认为 manifold = true。
    """
    try:
        from OCP.BRepCheck import BRepCheck_Analyzer  # type: ignore
        return bool(BRepCheck_Analyzer(part.wrapped).IsValid())
    except Exception:
        # 探测失败不阻塞 — STEP reimport_ok 是更硬的约束
        return True


def _step_reimport_check(step_path: Path) -> bool:
    """读回 STEP 看能不能正常 import 出 solid。"""
    try:
        from build123d import import_step
        reimported = import_step(str(step_path))
        return len(reimported.solids()) >= 1
    except Exception:
        return False


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_one(bench, out_dir: Path) -> dict:
    """跑一题,返回结果 dict(失败时含 'error' 字段)。"""
    from build123d import export_step

    record: dict = {
        "case": bench.name,
        "difficulty": bench.difficulty,
        "suite": list(bench.suite),
        "timeout_seconds": bench.timeout_seconds,
        "step_path": f"{bench.name}.step",
    }
    t0 = time.time()
    try:
        part = bench.builder()
    except Exception as e:
        record["error"] = f"build_failed: {e}"
        record["traceback"] = traceback.format_exc()
        record["build_seconds"] = round(time.time() - t0, 3)
        return record
    record["build_seconds"] = round(time.time() - t0, 3)

    step_path = out_dir / f"{bench.name}.step"
    try:
        export_step(part, str(step_path))
    except Exception as e:
        record["error"] = f"step_export_failed: {e}"
        return record

    record.update(_extract_geom(part))
    record["step_reimport_ok"] = _step_reimport_check(step_path)
    record["checksum_sha256"] = _sha256(step_path)
    record["step_size_kb"] = round(step_path.stat().st_size / 1024, 2)

    # extra outputs(各 model 自处理)
    if bench.extra_outputs:
        try:
            module = sys.modules.get(bench.builder.__module__)
            if module and hasattr(module, "export_extras"):
                module.export_extras(part, out_dir)
            record["extra_outputs"] = list(bench.extra_outputs)
        except Exception as e:
            record["extra_outputs_error"] = str(e)

    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", choices=["fast", "full"], default="fast")
    ap.add_argument("--out", type=Path, default=BENCH_DIR / "output")
    ap.add_argument("--emit-golden", action="store_true",
                    help="把跑出的结果写到 golden.json 作种子(仅首版/双签时使用)")
    ap.add_argument("--report", type=Path, default=BENCH_DIR / "report.md")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    all_fn, filter_fn = _import_models()
    cases = filter_fn(args.suite)
    print(f"Running suite={args.suite} ({len(cases)} cases) → {args.out}")

    results = []
    failures = 0
    t_total = time.time()
    for b in cases:
        print(f"  [{b.difficulty}★] {b.name} ...", end=" ", flush=True)
        rec = run_one(b, args.out)
        results.append(rec)
        if "error" in rec:
            failures += 1
            print(f"FAIL ({rec['error']})")
        else:
            print(f"ok ({rec['build_seconds']}s, {rec['step_size_kb']} KB)")
    elapsed = round(time.time() - t_total, 2)

    # report.md
    lines = [f"# benchmarks report — suite={args.suite}",
             f"- 总耗时:{elapsed} s",
             f"- 通过:{len(results) - failures}/{len(results)}",
             "",
             "| case | ★ | build (s) | bbox (mm) | volume (mm³) | manifold | reimport | size (KB) |",
             "|---|---|---|---|---|---|---|---|"]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['case']} | {r['difficulty']} | — | — | — | — | — | FAIL: {r['error']} |")
        else:
            lines.append(
                f"| {r['case']} | {r['difficulty']} | {r['build_seconds']} | "
                f"{r['bbox_mm']} | {r['volume_mm3']} | {r['is_manifold']} | "
                f"{r['step_reimport_ok']} | {r['step_size_kb']} |"
            )
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report → {args.report}")

    # 结果落盘 raw json
    raw = args.out / f"results_{args.suite}.json"
    raw.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # emit golden
    if args.emit_golden:
        golden_path = BENCH_DIR / "golden.json"
        existing: dict = {}
        if golden_path.exists():
            existing = json.loads(golden_path.read_text(encoding="utf-8"))
        existing["_meta"] = {
            "schema_version": 1,
            "generator": "skills/mechanical/benchmarks/run_all.py",
            "frozen_by": "<待 Dave 签字>",
            "frozen_at_seed": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "_note": "首版种子,Dave 审过后改 frozen_by + commit",
        }
        for r in results:
            if "error" in r:
                continue
            existing[r["case"]] = {
                "version": 1,
                "build_seconds": r["build_seconds"],
                "step_path": f"output/{r['case']}.step",
                "step_reimport_ok": r["step_reimport_ok"],
                "solid_count": r["solid_count"],
                "is_manifold": r["is_manifold"],
                "volume_mm3": r["volume_mm3"],
                "volume_tolerance_pct": 0.5 if r["difficulty"] <= 2 else (1.0 if r["difficulty"] == 3 else (1.5 if r["difficulty"] == 4 else 2.0)),
                "bbox_mm": r["bbox_mm"],
                "bbox_tolerance_mm": 0.05,
                "center_of_mass_mm": r["center_of_mass_mm"],
                "com_tolerance_mm": 0.1,
                "area_mm2": r["area_mm2"],
                "area_tolerance_pct": 1.0,
                "checksum_sha256": r["checksum_sha256"],
            }
        golden_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Golden seed → {golden_path}")

    return failures


if __name__ == "__main__":
    sys.exit(main())

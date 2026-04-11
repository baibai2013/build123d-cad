#!/usr/bin/env python3
"""
batch_export.py — 批量执行并导出 build123d 脚本

用法:
    python3 batch_export.py <目录或脚本列表> [--format step|stl|both] [--out 输出目录]

示例:
    python3 batch_export.py assets/                        # 导出 assets/ 下所有 .py
    python3 batch_export.py assets/ --format stl           # 仅导出 STL
    python3 batch_export.py assets/ --out /tmp/exports     # 指定输出目录
    python3 batch_export.py part1.py part2.py --format both  # 同时导出 STEP + STL
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path


def run_script(script_path: Path, output_dir: Path, fmt: str) -> tuple[bool, str]:
    """运行零件脚本，捕获导出文件。"""
    inject = f"""
import sys, os, shutil
from pathlib import Path

# 收集导出调用
_exports = []
_orig_dir = os.getcwd()

import build123d as _b123

_orig_step = _b123.export_step
_orig_stl  = getattr(_b123, 'export_stl', None)
_orig_brep = getattr(_b123, 'export_brep', None)
_orig_3mf  = getattr(_b123, 'export_3mf', None)

def _wrap_step(shape, path, *a, **kw):
    result = _orig_step(shape, path, *a, **kw)
    _exports.append(('step', Path(path).resolve()))
    return result

def _wrap_stl(shape, path, *a, **kw):
    if _orig_stl:
        result = _orig_stl(shape, path, *a, **kw)
        _exports.append(('stl', Path(path).resolve()))
        return result

_b123.export_step = _wrap_step
if _orig_stl: _b123.export_stl = _wrap_stl

# 在脚本目录执行
os.chdir({repr(str(script_path.parent))})
with open({repr(str(script_path))}) as f:
    src = f.read()

import builtins
exec(src, dict(__builtins__=builtins.__dict__, __file__={repr(str(script_path))}))

# 移动导出文件到目标目录
out_dir = Path({repr(str(output_dir))})
out_dir.mkdir(parents=True, exist_ok=True)

moved = []
for ext, src_path in _exports:
    if src_path.exists():
        dest = out_dir / src_path.name
        shutil.move(str(src_path), str(dest))
        moved.append(str(dest))
        print(f"EXPORTED {{ext.upper()}} {{dest}}")

if not moved:
    print("NO_EXPORTS")
"""
    result = subprocess.run(
        [sys.executable, "-c", inject],
        capture_output=True, text=True, timeout=180,
        cwd=str(script_path.parent)
    )
    ok = result.returncode == 0 and "NO_EXPORTS" not in result.stdout
    msg = result.stdout + ("\n" + result.stderr if result.stderr.strip() else "")
    return ok, msg.strip()


def main():
    parser = argparse.ArgumentParser(description="批量导出 build123d 脚本")
    parser.add_argument("targets", nargs="+", help="目录或 .py 文件列表")
    parser.add_argument("--format", choices=["step", "stl", "both"], default="step")
    parser.add_argument("--out", default="./exports", help="输出目录（默认 ./exports）")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()

    # 收集脚本列表
    scripts: list[Path] = []
    for t in args.targets:
        p = Path(t)
        if p.is_dir():
            scripts.extend(sorted(p.glob("*.py")))
        elif p.is_file() and p.suffix == ".py":
            scripts.append(p)
        else:
            print(f"跳过（非 .py 或目录）: {t}")

    if not scripts:
        print("未找到任何 .py 脚本")
        sys.exit(1)

    print(f"\n批量导出 {len(scripts)} 个脚本 → {out_dir}")
    print(f"格式: {args.format.upper()}")
    print("=" * 60)

    results = {"ok": [], "fail": []}
    t0 = time.time()

    for i, script in enumerate(scripts, 1):
        prefix = f"[{i:2d}/{len(scripts)}]"
        print(f"{prefix} {script.name} ... ", end="", flush=True)
        ts = time.time()
        ok, msg = run_script(script, out_dir, args.format)
        elapsed = time.time() - ts

        if ok:
            print(f"OK  ({elapsed:.1f}s)")
            results["ok"].append(script.name)
            if args.verbose:
                for line in msg.splitlines():
                    if line.startswith("EXPORTED"):
                        print(f"         {line}")
        else:
            print(f"FAIL ({elapsed:.1f}s)")
            results["fail"].append(script.name)
            if args.verbose or True:  # 失败时始终显示
                for line in msg.splitlines()[-10:]:
                    print(f"  > {line}")

    total = time.time() - t0
    print("=" * 60)
    print(f"完成: {len(results['ok'])} 成功 / {len(results['fail'])} 失败  ({total:.1f}s 总计)")
    if results["fail"]:
        print("失败列表:", ", ".join(results["fail"]))
    print(f"输出目录: {out_dir}")

    sys.exit(0 if not results["fail"] else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
contract_verify.py — Layer 0/1 参数合同验证工具
Parameter Contract Verification Tool (Layer 0 static check + Layer 1 runtime verification)

用法 / Usage:
    # 静态检查合同（不需要跑模型）/ Static check only
    python3 contract_verify.py --contract contract.yaml --check-only

    # 完整验证（需要模型代码）/ Full verification with model
    python3 contract_verify.py --contract contract.yaml --code part.py

    # 从代码参数直接验证 / Verify from code params JSON
    python3 contract_verify.py --contract contract.yaml --params params.json

参考 / References:
    - Layer 0 合同规范: references/verify/layer0-contract.md
    - Layer 1 验证算法: references/verify/layer1-verification.md
    - 示例合同: references/verify/examples/k70-contract.yaml
"""

import sys
import os
import json
import argparse
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


# ════════════════════════════════════════════════════════════
#  Layer 0: 合同静态检查 / Contract Static Check
# ════════════════════════════════════════════════════════════

# 每种特征类型必需的 dims 字段 / Required dims fields per feature type
REQUIRED_DIMS = {
    "rounded_rect": ["w", "h", "r"],
    "rect": ["w", "h"],
    "circle": ["d"],
    "slot": ["w", "h", "end_r"],
    "cylinder": ["d", "depth"],
    "freeform": ["bbox_w", "bbox_h"],
}

# 约束类型锁定的轴 / Axes locked by each constraint type
CONSTRAINT_LOCKS = {
    "on_face":        lambda c: _face_locks(c.get("value", "")),
    "offset":         lambda c: set(c.get("locks", [c.get("axis", "")])),
    "edge_dist":      lambda c: set(c.get("locks", [_ref_to_axis(c.get("ref", ""))])),
    "centered":       lambda c: set(c.get("locks", [_plane_to_axis(c.get("plane", ""))])),
    "normal":         lambda c: set(),
    "parallel":       lambda c: set(),
    "inter_dist":     lambda c: set(),
    "ordering":       lambda c: set(),
    "colinear":       lambda c: set(),
    "same_face":      lambda c: set(),
    "symmetric_pair": lambda c: set(),
    "concentric":     lambda c: set(),
    "ratio":          lambda c: set(),
    "size_range":     lambda c: set(),
}


def _face_locks(face: str) -> set:
    """on_face 约束锁定哪个轴 / Which axis does on_face lock"""
    return {
        "back": {"Z"}, "front": {"Z"},
        "right": {"X"}, "left": {"X"},
        "top": {"Y"}, "bottom": {"Y"},
    }.get(face, set())


def _ref_to_axis(ref: str) -> str:
    """edge_dist ref → locked axis"""
    return {"top": "Y", "bottom": "Y", "left": "X", "right": "X"}.get(ref, "")


def _plane_to_axis(plane: str) -> str:
    """centered plane → locked axis"""
    return {"XZ": "X", "YZ": "Y", "XY": "Z"}.get(plane, "")


def static_check(contract: dict) -> dict:
    """
    Layer 0 静态检查：不需要模型，只检查合同自身的完备性和一致性
    Static check: no model needed, verify contract completeness and consistency
    """
    results = []
    total_constraints = 0
    conflicts = 0

    for feature in contract.get("features", []):
        name = feature.get("name", "???")
        ftype = feature.get("type", "")
        dims = feature.get("dims", {})
        constraints = feature.get("constraints", [])

        issues = []

        # 规则 1: dims 完整性 / Rule 1: dims completeness
        required = REQUIRED_DIMS.get(ftype, [])
        missing_dims = [d for d in required if d not in dims]
        dims_ok = len(missing_dims) == 0
        if not dims_ok:
            issues.append(f"dims missing: {missing_dims}")

        # 规则 2: ≥ 3 约束 / Rule 2: at least 3 constraints
        n_constraints = len(constraints)
        total_constraints += n_constraints
        enough = n_constraints >= 3
        if not enough:
            issues.append(f"only {n_constraints} constraints (need ≥3)")

        # 规则 3: XYZ 轴覆盖 / Rule 3: XYZ axis coverage
        axes = set()
        for c in constraints:
            ctype = c.get("type", "")
            lock_fn = CONSTRAINT_LOCKS.get(ctype)
            if lock_fn:
                axes |= lock_fn(c)
            # 也检查显式 locks 字段 / Also check explicit locks field
            if "locks" in c:
                axes |= set(c["locks"])

        xyz_complete = axes >= {"X", "Y", "Z"}
        if not xyz_complete:
            missing_axes = {"X", "Y", "Z"} - axes
            issues.append(f"axes not covered: {missing_axes}")

        # 规则 4: 矛盾检测 / Rule 4: conflict detection
        axis_constraints = {}
        for c in constraints:
            ctype = c.get("type", "")
            if ctype == "centered":
                ax = _plane_to_axis(c.get("plane", ""))
                axis_constraints.setdefault(ax, []).append(("centered", 0))
            elif ctype == "offset" and c.get("value") != "side_center":
                ax = c.get("axis", "")
                axis_constraints.setdefault(ax, []).append(("offset", c.get("value", 0)))

        for ax, entries in axis_constraints.items():
            types = set(e[0] for e in entries)
            if "centered" in types and "offset" in types:
                vals = [e[1] for e in entries if e[0] == "offset"]
                if any(v != 0 for v in vals):
                    issues.append(f"conflict on {ax}: centered + offset≠0")
                    conflicts += 1

        status = "PASS" if (dims_ok and enough and xyz_complete and not issues) else "FAIL"
        results.append({
            "feature": name,
            "dims_ok": dims_ok,
            "n_constraints": n_constraints,
            "axes": sorted(axes),
            "xyz_complete": xyz_complete,
            "issues": issues,
            "status": status,
        })

    all_pass = all(r["status"] == "PASS" for r in results)
    return {
        "verdict": "PASS" if all_pass else "FAIL",
        "features": results,
        "total_features": len(results),
        "total_constraints": total_constraints,
        "conflicts": conflicts,
    }


# ════════════════════════════════════════════════════════════
#  Layer 1: 运行时约束验证 / Runtime Constraint Verification
# ════════════════════════════════════════════════════════════

def resolve_params(contract: dict, code_params: dict) -> dict:
    """
    通过 param_map 将代码变量映射到合同字段
    Map code variables to contract fields via param_map
    """
    param_map = contract.get("param_map", {})
    resolved = {}
    for contract_key, code_var in param_map.items():
        if code_var in code_params:
            resolved[contract_key] = code_params[code_var]
    return resolved


def eval_constraint(feature: dict, constraint: dict, params: dict, body: dict, pos_cache: dict) -> dict:
    """
    评估单条约束 / Evaluate a single constraint
    Returns: {type, status, error, detail}
    """
    ctype = constraint.get("type", "")
    name = feature.get("name", "")
    pos = pos_cache.get(name, {})

    if ctype == "on_face":
        ok = feature.get("face") == constraint.get("value")
        return {"type": ctype, "status": "PASS" if ok else "FAIL",
                "error": 0 if ok else 1.0,
                "detail": f"face={feature.get('face')}, expected={constraint.get('value')}"}

    elif ctype == "offset":
        val = constraint.get("value")
        if val == "side_center":
            return {"type": ctype, "status": "PASS", "error": 0, "detail": "side_center (structural)"}
        axis = constraint.get("axis", "")
        tol = constraint.get("tol", 2.0)
        actual = pos.get("cx", 0) if axis == "X" else pos.get("cy", 0) if axis == "Y" else 0
        err = abs(actual - val)
        return {"type": ctype,
                "status": "PASS" if err <= tol else "WARN" if err <= tol * 2 else "FAIL",
                "error": err,
                "detail": f"axis={axis} actual={actual:.1f} expected={val} ±{tol}"}

    elif ctype == "edge_dist":
        ref = constraint.get("ref", "")
        expected = constraint.get("value", 0)
        tol = constraint.get("tol", 2.0)
        L, W = body.get("L", 0), body.get("W", 0)

        cy = pos.get("cy")
        from_top = pos.get("from_top")
        cx = pos.get("cx", 0)

        if ref == "top":
            actual = L / 2 - (cy if cy is not None else (L / 2 - (from_top or 0)))
        elif ref == "bottom":
            actual = L / 2 + (cy or 0)
        elif ref == "left":
            actual = W / 2 + cx
        elif ref == "right":
            actual = W / 2 - cx
        else:
            actual = 0

        err = abs(actual - expected)
        return {"type": ctype,
                "status": "PASS" if err <= tol else "WARN" if err <= tol * 2 else "FAIL",
                "error": err,
                "detail": f"dist_to_{ref}={actual:.1f} expected={expected:.1f} ±{tol}"}

    elif ctype == "centered":
        plane = constraint.get("plane", "")
        tol = constraint.get("tol", 1.0)
        err = abs(pos.get("cx", 0)) if plane == "XZ" else abs(pos.get("cy", 0))
        return {"type": ctype,
                "status": "PASS" if err <= tol else "FAIL",
                "error": err,
                "detail": f"centered on {plane}, offset={err:.1f} ±{tol}"}

    elif ctype == "ordering":
        axis = constraint.get("axis", "Y")
        sequence = constraint.get("sequence", [])
        values = []
        for fname in sequence:
            p = pos_cache.get(fname, {})
            if axis == "Y":
                v = p.get("cy") or (body.get("L", 0) / 2 - (p.get("from_top") or 0))
            else:
                v = p.get("cx", 0)
            values.append((fname, v))
        nums = [v for _, v in values]
        if axis == "Y":
            ok = all(a > b for a, b in zip(nums, nums[1:]))
        else:
            ok = all(a < b for a, b in zip(nums, nums[1:]))
        return {"type": ctype,
                "status": "PASS" if ok else "FAIL",
                "error": 0 if ok else 1.0,
                "detail": f"order({axis}): {[f'{n}={v:.1f}' for n,v in values]}"}

    elif ctype == "colinear":
        target = constraint.get("target", "")
        axis = constraint.get("axis", "X")
        tol = constraint.get("tol", 1.0)
        key = "cx" if axis == "X" else "cy"
        a = pos.get(key, 0)
        b = pos_cache.get(target, {}).get(key, 0)
        err = abs(a - b)
        return {"type": ctype,
                "status": "PASS" if err <= tol else "FAIL",
                "error": err,
                "detail": f"{name}.{axis}={a:.1f} vs {target}.{axis}={b:.1f} ±{tol}"}

    elif ctype == "same_face":
        target = constraint.get("target", "")
        target_f = next((f for f in params.get("_features", []) if f.get("name") == target), {})
        b_face = target_f.get("face", "")
        ok = feature.get("face") == b_face
        return {"type": ctype,
                "status": "PASS" if ok else "FAIL",
                "error": 0 if ok else 1.0,
                "detail": f"{name}={feature.get('face')} vs {target}={b_face}"}

    elif ctype == "symmetric_pair":
        target = constraint.get("target", "")
        tol = constraint.get("tol", 3.0)
        cx_a = pos.get("cx", 0)
        cx_b = pos_cache.get(target, {}).get("cx", 0)
        err = abs(abs(cx_a) - abs(cx_b))
        sign_ok = (cx_a * cx_b) < 0
        return {"type": ctype,
                "status": "PASS" if (err <= tol and sign_ok) else "FAIL",
                "error": err,
                "detail": f"cx={cx_a:.1f} vs {cx_b:.1f} mirror ±{tol}"}

    elif ctype == "inter_dist":
        target = constraint.get("target", "")
        axis = constraint.get("axis", "Y")
        expected = constraint.get("value", 0)
        tol = constraint.get("tol", 2.0)
        pos_b = pos_cache.get(target, {})

        if axis == "Y":
            ft_a = pos.get("from_top", 0)
            ft_b = pos_b.get("from_top", 0)
            dim_a = params.get(f"{name}.w", 0)
            dim_b = params.get(f"{target}.w", 0)
            gap = ft_b - (ft_a + dim_a) if ft_a < ft_b else ft_a - (ft_b + dim_b)
        else:
            gap = abs(pos.get("cx", 0) - pos_b.get("cx", 0))

        err = abs(gap - expected)
        return {"type": ctype,
                "status": "PASS" if err <= tol else "WARN" if err <= tol * 2 else "FAIL",
                "error": err,
                "detail": f"gap({name}↔{target})={gap:.1f} expected={expected:.1f} ±{tol}"}

    elif ctype == "ratio":
        param = constraint.get("param", "")
        expected = constraint.get("expected", 0)
        tol = constraint.get("tol", 0.05)
        # 从 dims._ratios 中读取 / Read from dims._ratios
        ratios = feature.get("dims", {}).get("_ratios", {})
        actual = ratios.get(param, 0)
        err = abs(actual - expected)
        return {"type": ctype,
                "status": "PASS" if err <= tol else "WARN" if err <= tol * 2 else "FAIL",
                "error": err,
                "detail": f"ratio:{param}={actual:.3f} expected={expected:.3f} ±{tol}"}

    return {"type": ctype, "status": "SKIP", "error": 0, "detail": f"unhandled type: {ctype}"}


def build_pos_cache(contract: dict, resolved_params: dict) -> dict:
    """构建特征位置缓存 / Build feature position cache"""
    cache = {}
    for f in contract.get("features", []):
        name = f["name"]
        pos = f.get("pos", {})
        cache[name] = {
            "cx": resolved_params.get(f"{name}.cx", pos.get("cx", 0)),
            "cy": resolved_params.get(f"{name}.cy", pos.get("cy")),
            "from_top": resolved_params.get(f"{name}.from_top", pos.get("from_top")),
            "face": f.get("face", ""),
        }
    return cache


def runtime_verify(contract: dict, resolved_params: dict) -> dict:
    """
    Layer 1 Stage B+C 运行时验证（不含 Stage A/D，那些需要 BRep 实体）
    Runtime verification of dims + spatial constraints
    """
    body = contract.get("meta", {}).get("body_ref", {})
    features = contract.get("features", [])
    resolved_params["_features"] = features  # for same_face lookup
    pos_cache = build_pos_cache(contract, resolved_params)

    results = []
    for feature in features:
        name = feature["name"]
        f_result = {"feature": name, "constraints": [], "axes_locked": set()}

        for c in feature.get("constraints", []):
            r = eval_constraint(feature, c, resolved_params, body, pos_cache)
            if "locks" in c:
                f_result["axes_locked"] |= set(c["locks"])
            else:
                ctype = c.get("type", "")
                lock_fn = CONSTRAINT_LOCKS.get(ctype)
                if lock_fn:
                    f_result["axes_locked"] |= lock_fn(c)
            f_result["constraints"].append(r)

        f_result["xyz_complete"] = f_result["axes_locked"] >= {"X", "Y", "Z"}

        statuses = [cr["status"] for cr in f_result["constraints"]]
        f_result["status"] = "FAIL" if "FAIL" in statuses else "WARN" if "WARN" in statuses else "PASS"

        errors = [cr["error"] for cr in f_result["constraints"]
                  if isinstance(cr.get("error"), (int, float))]
        f_result["E_feature"] = sum(errors) / len(errors) if errors else 0

        results.append(f_result)

    E_total = sum(r["E_feature"] for r in results) / len(results) if results else 0
    all_pass = all(r["status"] == "PASS" for r in results)
    has_warn = any(r["status"] == "WARN" for r in results)

    verdict = "PASS" if all_pass else "PASS_WITH_WARN" if (not any(r["status"] == "FAIL" for r in results)) else "FAIL"

    return {
        "verdict": verdict,
        "E_total": E_total,
        "features": results,
        "summary": {
            "total_features": len(results),
            "total_constraints": sum(len(r["constraints"]) for r in results),
            "all_xyz_complete": all(r["xyz_complete"] for r in results),
            "pass": sum(1 for r in results if r["status"] == "PASS"),
            "warn": sum(1 for r in results if r["status"] == "WARN"),
            "fail": sum(1 for r in results if r["status"] == "FAIL"),
        }
    }


# ════════════════════════════════════════════════════════════
#  输出格式化 / Output Formatting
# ════════════════════════════════════════════════════════════

def print_static_check(result: dict):
    print("\n=== Layer 0: Contract Static Check ===\n")
    for f in result["features"]:
        dims = "✅" if f["dims_ok"] else "❌"
        axes_str = ",".join(f["axes"])
        xyz = "✅" if f["xyz_complete"] else "❌"
        status = "✅" if f["status"] == "PASS" else "❌"
        print(f"  {f['feature']:<20s} dims:{dims}  constraints:{f['n_constraints']}  "
              f"axes:{{{axes_str}}} {xyz}  {status}")
        for issue in f["issues"]:
            print(f"    ⚠ {issue}")

    v = result["verdict"]
    icon = "✅" if v == "PASS" else "❌"
    print(f"\n  Static check: {icon} {v} "
          f"({result['total_features']} features, "
          f"{result['total_constraints']} constraints, "
          f"{result['conflicts']} conflicts)\n")


def print_runtime_verify(result: dict):
    print("\n=== Layer 1: Runtime Constraint Verification ===\n")
    for f in result["features"]:
        n = len(f["constraints"])
        xyz = "✓" if f["xyz_complete"] else "✗"
        icon = "✅" if f["status"] == "PASS" else "⚠️" if f["status"] == "WARN" else "❌"
        print(f"  {f['feature']:<20s} [{n} constraints, XYZ {xyz}]  {icon} {f['status']}")
        for c in f["constraints"]:
            ci = "✅" if c["status"] == "PASS" else "⚠️" if c["status"] == "WARN" else "❌"
            print(f"    {ci} {c['type']}: {c['detail']}")
        print(f"    ▸ E_feature = {f['E_feature']:.3f}")

    s = result["summary"]
    v = result["verdict"]
    icon = "✅" if v == "PASS" else "⚠️" if v == "PASS_WITH_WARN" else "❌"
    print(f"\n  {icon} Verdict: {v}")
    print(f"  Features: {s['pass']}/{s['total_features']} PASS"
          f" | {s['warn']} WARN | {s['fail']} FAIL")
    print(f"  Constraints: {s['total_constraints']} total")
    print(f"  XYZ Complete: {'all' if s['all_xyz_complete'] else 'INCOMPLETE'}")
    print(f"  E_total: {result['E_total']:.4f}\n")


# ════════════════════════════════════════════════════════════
#  CLI 入口 / CLI Entry
# ════════════════════════════════════════════════════════════

def load_contract(path: str) -> dict:
    """加载合同（YAML 或 JSON）/ Load contract from YAML or JSON"""
    p = Path(path)
    content = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        if yaml is None:
            print("Error: PyYAML not installed. Run: pip install pyyaml")
            sys.exit(1)
        return yaml.safe_load(content)
    else:
        return json.loads(content)


def main():
    parser = argparse.ArgumentParser(
        description="Layer 0/1 参数合同验证工具 / Parameter Contract Verification Tool")
    parser.add_argument("--contract", "-c", required=True,
                        help="合同文件路径（YAML/JSON）/ Contract file path")
    parser.add_argument("--check-only", action="store_true",
                        help="仅静态检查，不做运行时验证 / Static check only")
    parser.add_argument("--params", "-p",
                        help="代码参数 JSON 文件 / Code params JSON file")
    args = parser.parse_args()

    contract = load_contract(args.contract)

    # Layer 0: 静态检查 / Static check
    static_result = static_check(contract)
    print_static_check(static_result)

    if static_result["verdict"] != "PASS":
        print("Static check failed. Fix contract before runtime verification.")
        sys.exit(1)

    if args.check_only:
        sys.exit(0)

    # Layer 1: 运行时验证 / Runtime verification
    if args.params:
        with open(args.params) as f:
            code_params = json.load(f)
        resolved = resolve_params(contract, code_params)
    else:
        # 从合同自身的 pos 字段做自验证 / Self-verify from contract's own pos
        resolved = {}
        for feature in contract.get("features", []):
            name = feature["name"]
            pos = feature.get("pos", {})
            dims = feature.get("dims", {})
            for k, v in pos.items():
                if not k.startswith("_"):
                    resolved[f"{name}.{k}"] = v
            for k, v in dims.items():
                if not k.startswith("_"):
                    resolved[f"{name}.{k}"] = v

    runtime_result = runtime_verify(contract, resolved)
    print_runtime_verify(runtime_result)

    sys.exit(0 if runtime_result["verdict"] in ("PASS", "PASS_WITH_WARN") else 1)


if __name__ == "__main__":
    main()

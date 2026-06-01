#!/usr/bin/env python3
"""
extract_params.py — 从 build123d 脚本中提取参数表

用法:
    python3 extract_params.py <part_script.py>
    python3 extract_params.py assets/01_mounting_plate.py

输出参数表（变量名 + 值 + 注释），方便快速了解零件可调参数。
"""

import sys
import re
import ast
from pathlib import Path


PARAM_SECTION_RE = re.compile(
    r"#\s*=+\s*参数\s*=+",    # 匹配 "# ===== 参数 ====="
    re.IGNORECASE
)
NEXT_SECTION_RE = re.compile(
    r"#\s*=+\s*\S",            # 下一个 "# ===== XXX =====" 部分
)


def extract_params_from_source(src: str) -> list[dict]:
    """
    从源代码中提取顶部参数段落的赋值语句。
    策略：找到 "# ===== 参数 =====" 开始，到下一个大节标题结束。
    """
    lines = src.splitlines()
    params = []

    # 找参数段开始行
    start_line = None
    for i, line in enumerate(lines):
        if PARAM_SECTION_RE.search(line):
            start_line = i + 1
            break

    if start_line is None:
        # 没有明确参数段，扫描前30行的简单赋值
        start_line = 0
        end_line = min(30, len(lines))
    else:
        # 找结束行
        end_line = len(lines)
        for i in range(start_line, len(lines)):
            if i != start_line and NEXT_SECTION_RE.search(lines[i]):
                end_line = i
                break

    # 解析赋值行
    assign_re = re.compile(
        r"^(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?P<value>[^#\n]+?)(?:\s*#\s*(?P<comment>.*))?$"
    )
    multi_assign_re = re.compile(
        r"^(?P<names>[a-zA-Z_][a-zA-Z0-9_, ]+)\s*=\s*(?P<values>[^#\n]+?)(?:\s*#\s*(?P<comment>.*))?$"
    )

    for line in lines[start_line:end_line]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("from ") or stripped.startswith("import "):
            continue

        # 尝试解析多重赋值 a, b, c = 1, 2, 3
        m = multi_assign_re.match(stripped)
        if m and "," in m.group("names"):
            names = [n.strip() for n in m.group("names").split(",")]
            comment = m.group("comment") or ""
            try:
                values_str = m.group("values").strip()
                # 尝试 ast.literal_eval
                vals = ast.literal_eval(values_str)
                if isinstance(vals, tuple) and len(vals) == len(names):
                    for n, v in zip(names, vals):
                        params.append({"name": n, "value": repr(v), "comment": comment})
                    continue
            except Exception:
                pass

        # 单变量赋值
        m = assign_re.match(stripped)
        if m:
            name = m.group("name")
            value_str = m.group("value").strip()
            comment = m.group("comment") or ""
            # 过滤掉 with/def/class/import 等
            if name in ("with", "def", "class", "import", "from", "if", "for"):
                continue
            try:
                value = ast.literal_eval(value_str)
                params.append({
                    "name": name,
                    "value": repr(value),
                    "comment": comment,
                    "raw": value_str
                })
            except Exception:
                # 非字面量（表达式），保留原始
                if not any(c in value_str for c in "([{"):
                    params.append({
                        "name": name,
                        "value": value_str,
                        "comment": comment,
                        "raw": value_str
                    })

    return params


def print_params_table(script_path: Path, params: list[dict]):
    print(f"\n参数表: {script_path.name}")
    print("=" * 65)
    if not params:
        print("  未检测到参数（脚本中无 '# ===== 参数 =====' 段落）")
        return

    col_name  = max(len(p["name"])  for p in params) + 2
    col_value = max(len(p["value"]) for p in params) + 2
    col_name  = max(col_name, 12)
    col_value = max(col_value, 12)

    header = f"{'变量名':{col_name}} {'值':{col_value}} 注释"
    print(header)
    print("-" * 65)
    for p in params:
        name  = p["name"].ljust(col_name)
        value = p["value"].ljust(col_value)
        comment = p.get("comment", "")
        print(f"{name} {value} {comment}")
    print()
    print(f"共 {len(params)} 个可调参数")
    print()


def main():
    if len(sys.argv) < 2:
        print("用法: python3 extract_params.py <part_script.py>")
        sys.exit(1)

    script = Path(sys.argv[1]).resolve()
    if not script.exists():
        print(f"错误: 找不到文件 {script}")
        sys.exit(1)

    src = script.read_text(encoding="utf-8")
    params = extract_params_from_source(src)
    print_params_table(script, params)


if __name__ == "__main__":
    main()

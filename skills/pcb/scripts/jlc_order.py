#!/usr/bin/env python3
"""嘉立创报价 / 下单 — 经 jlcpcb-mcp(免大量手写 REST),无 key fail-loud + 降级,下单双重 gate。

用法:
    # 板级报价(需 creds;无则降级开网页):
    python3 jlc_order.py <gerbers.zip> [--layers 2] [--qty 5]
    # 免 key 物料报价(任意机器可用):
    python3 jlc_order.py --component C25104 [--qty 100]
    # 下单(gate:需 creds + JLCPCB_ENABLE_ORDERS=true + --confirm):
    python3 jlc_order.py <gerbers.zip> --order --confirm

环境变量:JLCPCB_APP_ID / JLCPCB_ACCESS_KEY / JLCPCB_SECRET_KEY(板级/下单需要);
        JLCPCB_ENABLE_ORDERS=true(下单总开关)。
本技能默认**不接 key**(决策①):无 creds 时板级报价降级开网页,绝不假装成功。
工具名/字段对 references/jlcpcb-mcp.md 与实时文档为准,不编。
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys

WEB_QUOTE = "https://jlcpcb.com/quote"
MCP_PKG = "jlcpcb-mcp@0.3.3"
HAS_CREDS = all(os.environ.get(k) for k in ("JLCPCB_APP_ID", "JLCPCB_ACCESS_KEY", "JLCPCB_SECRET_KEY"))


def mcp_call(tool: str, arguments: dict, timeout: int = 300) -> dict:
    """起 jlcpcb-mcp(stdio),initialize + tools/call,返回 result。首次会建本地 DB(慢)。"""
    if not shutil.which("npx"):
        raise RuntimeError("缺 npx(Node)。无法启动 jlcpcb-mcp。")
    reqs = "\n".join(json.dumps(m) for m in [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "pcb-skill", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": tool, "arguments": arguments}},
    ]) + "\n"
    p = subprocess.run(["npx", "-y", MCP_PKG], input=reqs, capture_output=True,
                       text=True, timeout=timeout)
    for line in p.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            m = json.loads(line)
        except ValueError:
            continue
        if m.get("id") == 2:
            if "error" in m:
                raise RuntimeError(m["error"])
            return m.get("result", {})
    raise RuntimeError("未收到 tools/call 响应(可能仍在建库;增大 --timeout)")


def degrade_manual(reason: str) -> dict:
    print(f"⚠ {reason}\n→ 降级:请打开 {WEB_QUOTE} 手动上传 Gerber 报价/下单(不假装成功)。",
          file=sys.stderr)
    return {"quote_source": "manual", "web_url": WEB_QUOTE, "reason": reason}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="嘉立创报价/下单(经 jlcpcb-mcp)")
    ap.add_argument("gerbers", nargs="?", help="gerbers.zip 路径(板级报价/下单)")
    ap.add_argument("--component", help="免 key 物料报价:LCSC 料号,如 C25104")
    ap.add_argument("--qty", type=int, default=5)
    ap.add_argument("--layers", type=int, default=2)
    ap.add_argument("--order", action="store_true", help="真实下单(gate)")
    ap.add_argument("--confirm", action="store_true", help="确认真实下单/付费")
    ap.add_argument("--out", default="quote.json")
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args(argv)

    # 免 key 物料报价
    if a.component:
        try:
            r = mcp_call("jlcpcb_get_component_pricing",
                         {"lcsc": a.component, "quantity": a.qty}, a.timeout)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return 0
        except Exception as e:  # noqa: BLE001
            print(f"✗ 物料报价失败:{e}", file=sys.stderr)
            return 1

    if not a.gerbers:
        print("用法:jlc_order.py <gerbers.zip> | --component <LCSC>", file=sys.stderr)
        return 2

    # 下单 = 双重 gate
    if a.order:
        if not a.confirm:
            print("✗ 下单需 --confirm(防误下单)。未下单。", file=sys.stderr)
            return 2
        if os.environ.get("JLCPCB_ENABLE_ORDERS") != "true":
            print("✗ 下单总开关未开:export JLCPCB_ENABLE_ORDERS=true。未下单。", file=sys.stderr)
            return 2
        if not HAS_CREDS:
            json.dump(degrade_manual("下单缺 creds(JLCPCB_APP_ID/ACCESS_KEY/SECRET_KEY)"),
                      open(a.out, "w"), ensure_ascii=False, indent=2)
            return 2

    # 板级报价(→ 下单):需 creds;无则降级
    if not HAS_CREDS:
        res = degrade_manual("板级报价缺 creds(本技能默认不接 key,决策①)")
        json.dump(res, open(a.out, "w"), ensure_ascii=False, indent=2)
        return 0  # 降级是预期路径,非失败

    try:
        up = mcp_call("jlcpcb_pcb_upload_gerber", {"file_path": a.gerbers}, a.timeout)
        file_key = (up or {}).get("fileKey") or up
        q = mcp_call("jlcpcb_pcb_calculate_price",
                     {"fileKey": file_key, "layers": a.layers, "quantity": a.qty}, a.timeout)
        res = {"quote_source": "mcp", "quote": q, "fileKey": file_key}
        if a.order:  # 已过 gate
            res["order"] = mcp_call("jlcpcb_pcb_create_order",
                                    {"fileKey": file_key, "layers": a.layers,
                                     "quantity": a.qty}, a.timeout)
        json.dump(res, open(a.out, "w"), ensure_ascii=False, indent=2)
        print(f"✓ 写 {a.out}(quote_source=mcp{', 已下单' if a.order else ''})")
        return 0
    except Exception as e:  # noqa: BLE001
        json.dump(degrade_manual(f"MCP 调用失败:{e}"), open(a.out, "w"),
                  ensure_ascii=False, indent=2)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

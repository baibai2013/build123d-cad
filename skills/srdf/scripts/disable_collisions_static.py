#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SRDF 自碰撞矩阵静态推导(04 §10.4 / §7.2 决议)。

P1 阶段不引入 MoveIt setup_assistant 运行时依赖,纯 graph 静态推导。
输入:URDF 的 link 列表 + joint 树;输出:list[(link1, link2, reason)]。

规则集(按优先级,先命中先定 reason):
  1. adjacent          任意 (parent, child) 直连对 → disable(reason="adjacent")
                       —— 受 enable_default_adjacent 开关控制(默认开)
  2. fixed-chain       fixed joint 两端 link → disable(reason="fixed-chain")
  3. same-leg-non-adjacent
                       同腿前缀(fl_/fr_/rl_/rr_)且链上段距 ≥ 2 → disable
                       (相邻段距=1 已被规则 1 覆盖)
  4. user pairs        srdf.yaml.disabled_collisions.pairs 直接并入,reason 用 yaml 提供

不做(留 P2,见 04 §13 R6):
  - never-collide / default-in-collision(需 sample-based 全状态空间扫,依赖 MoveIt/PyBullet)

CLI:
  python disable_collisions_static.py robot.urdf [--no-adjacent]
"""
from __future__ import annotations

import argparse
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

LEG_PREFIX = re.compile(r"^(fl|fr|rl|rr)_")


@dataclass(frozen=True)
class UrdfJoint:
    name: str
    type: str
    parent: str
    child: str


@dataclass
class UrdfTree:
    robot: str
    links: list[str]
    joints: list[UrdfJoint]


# ---------------------------------------------------------------------------
# URDF 解析(只取拓扑,不读几何 —— SRDF 只面对 link/joint 名)
# ---------------------------------------------------------------------------
def parse_urdf_tree(urdf_path: Path) -> UrdfTree:
    root = ET.fromstring(Path(urdf_path).read_text(encoding="utf-8"))
    if root.tag != "robot":
        raise ValueError(f"{urdf_path} 根不是 <robot>")
    links = [l.get("name") for l in root.findall("link")]
    joints = [
        UrdfJoint(
            name=j.get("name"),
            type=j.get("type", "fixed"),
            parent=j.find("parent").get("link"),
            child=j.find("child").get("link"),
        )
        for j in root.findall("joint")
    ]
    return UrdfTree(robot=root.get("name", ""), links=links, joints=joints)


# ---------------------------------------------------------------------------
# 链深度(从根 link BFS,用于 same-leg 段距)
# ---------------------------------------------------------------------------
def link_depths(tree: UrdfTree) -> dict[str, int]:
    parent_of = {j.child: j.parent for j in tree.joints}
    children: dict[str, list[str]] = {}
    for j in tree.joints:
        children.setdefault(j.parent, []).append(j.child)
    roots = [l for l in tree.links if l not in parent_of]
    depths: dict[str, int] = {}
    for r in roots:
        depths[r] = 0
        q = deque([r])
        while q:
            node = q.popleft()
            for c in children.get(node, []):
                if c not in depths:
                    depths[c] = depths[node] + 1
                    q.append(c)
    # 未连通的(理论不该有)给 -1,same-leg 规则会跳过
    for l in tree.links:
        depths.setdefault(l, -1)
    return depths


def _leg_prefix(link: str) -> str | None:
    m = LEG_PREFIX.match(link)
    return m.group(1) if m else None


def _key(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a <= b else (b, a)


# ---------------------------------------------------------------------------
# 主推导
# ---------------------------------------------------------------------------
def disable_collisions_static(
    tree: UrdfTree,
    *,
    enable_default_adjacent: bool = True,
    user_pairs: list[dict[str, str]] | None = None,
) -> list[tuple[str, str, str]]:
    reason_of: dict[tuple[str, str], str] = {}

    def put(a: str, b: str, reason: str) -> None:
        if a == b:
            return
        k = _key(a, b)
        reason_of.setdefault(k, reason)  # 先命中先定,优先级见规则顺序

    # 规则 1:adjacent
    if enable_default_adjacent:
        for j in tree.joints:
            put(j.parent, j.child, "adjacent")

    # 规则 2:fixed-chain(fixed joint 两端;若已被 adjacent 占,保留 adjacent)
    for j in tree.joints:
        if j.type == "fixed":
            put(j.parent, j.child, "fixed-chain")

    # 规则 3:same-leg-non-adjacent
    depths = link_depths(tree)
    legs: dict[str, list[str]] = {}
    for link in tree.links:
        pfx = _leg_prefix(link)
        if pfx is not None and depths.get(link, -1) >= 0:
            legs.setdefault(pfx, []).append(link)
    for members in legs.values():
        for i in range(len(members)):
            for k in range(i + 1, len(members)):
                a, b = members[i], members[k]
                if abs(depths[a] - depths[b]) >= 2:
                    put(a, b, "same-leg-non-adjacent")

    # 规则 4:user pairs 覆盖(显式 reason 优先级最高,直接改写)
    for p in (user_pairs or []):
        reason_of[_key(p["link1"], p["link2"])] = p.get("reason", "user")

    return sorted((a, b, r) for (a, b), r in reason_of.items())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="disable_collisions_static",
        description="SRDF 自碰撞矩阵静态推导(04 §10.4)。",
    )
    parser.add_argument("urdf", type=Path)
    parser.add_argument("--no-adjacent", action="store_true",
                        help="关闭 adjacent 规则(给玩具 robot 用)")
    args = parser.parse_args(argv)
    tree = parse_urdf_tree(args.urdf.resolve())
    pairs = disable_collisions_static(tree, enable_default_adjacent=not args.no_adjacent)
    print(f"# robot={tree.robot}  links={len(tree.links)}  joints={len(tree.joints)}  disabled={len(pairs)}")
    for a, b, reason in pairs:
        print(f"{a}\t{b}\t{reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

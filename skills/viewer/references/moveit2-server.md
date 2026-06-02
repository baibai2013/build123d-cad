# MoveIt2 集成

> cad-viewer 上游的 `moveit2_server/` 子模块(在 ~/.agents/skills/cad-viewer/scripts/viewer/moveit2_server/)。
> P0 阶段不集成;urdf/srdf 渲染由 cad SPA 原生支持已够。

## 何时集成

触发条件:04-机器人描述子技能(srdf)落地后,需要 `MoveIt setup assistant` 产出自碰撞矩阵
或路径规划演示时再考虑。

## 集成路径

- `engines/cad/` 已包含 cad-viewer 全部产物;moveit2 集成走 cad-viewer 原 standalone server(`engines/cad/backend/server.mjs`)而非父 server。
- 父 server 不必感知 moveit2 — 客户端发 WebSocket 直接打到 cad-viewer 老 server(占 4178 默认端口)。

## 决策记录

详见规格 `docs/superpowers/specs/03-viewer.md` §16 "后续待协作"。

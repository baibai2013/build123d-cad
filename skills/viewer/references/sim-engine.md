# P3 · sim engine

> 目录就位但未实现。落地前需在 04-机器人描述 子技能里产出 URDF + joint timeline JSON 样例。

## 选型

| 后缀 | 工具 | License | 集成方式 |
|---|---|---|---|
| `.csv`(波形) | plotly.js | MIT | CDN 或本地 dist,`csv → plotly traces` |
| `.json`(URDF 轨迹回放) | 复用 cad engine | 自研 | 共用 `engines/cad/dist`,加 `?mode=playback` |
| `.mp4 .webm`(录屏) | HTML5 `<video>` | 0 deps | 浏览器内置 |

## .json 后缀冲突说明

`.json` 既可能是 urdf 配套配置(走 cad)也可能是轨迹时间序列(走 sim)。
**router.mjs 不 sniff JSON 顶层 schema**,P3 sim 落地时由调用方显式 `?engine=sim` 透传。

## 实现路线图

1. 04 子技能产出 `joint_timeline.schema.json` + 一个样例
2. `engines/sim/` 引入 plotly + 自定义 playback HTML
3. cad SPA 增加 `?mode=playback` 模式(读时间序列驱动 joint 滑块)
4. `tests/test_sim_engine.py` 去 skip

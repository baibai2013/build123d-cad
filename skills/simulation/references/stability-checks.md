# 稳定性断言（verify_sim 的大脑）

> 四项数值断言 + AI 视觉清单。阈值定义在 `scripts/verify_sim.py` 顶部常量，改阈值改那里。

`verify_sim.py` in-process 调 `run_sim.simulate()` 跑一次，对返回的 record 跑四项断言，
全过退 0、任一挂退 1。阈值与判据：

| check | 判据 | 常量（默认） | 含义 |
|---|---|---|---|
| `no_floor_tunnel` | `min_base_z > FLOOR_EPS` | `FLOOR_EPS = -0.10` | 基座没穿透 z=0 地面（碰撞/惯量错会穿地） |
| `no_blowup` | `max|pos|<POS_CAP` 且 `max|jvel|<VEL_CAP` 且无 NaN/Inf | `POS_CAP=1e3` `VEL_CAP=1e3` | 数值没发散（飞出/抖爆） |
| `joints_within_limits` | 每采样 `lower-TOL ≤ q ≤ upper+TOL` | `JOINT_TOL=0.10` rad | 关节没冲出机械限位（连续关节跳过） |
| `settled`（模式相关） | passive: 末速 `< SETTLE_VEL`；hold/gait: `|roll|,|pitch| < FLIP_DEG` | `SETTLE_VEL=1.0` m/s `FLIP_DEG=80°` | 末态落定/没翻车 |

## 判据细节

- **min_base_z**：取整段 `base_pos[2]` 最小值。腿长高的机器人 base 本就高于 0；穿地表现为负值骤降。
- **no_blowup**：`nan_or_inf` 在 `run_sim` 采样时实时检测（任何 pos/vel 非有限即置 true）。
  t=0 就爆炸 → 多半是碰撞几何重叠（试 `--no-self-collision` 对照），不是仿真 bug。
- **joints_within_limits**：movable = `type ∈ {0,1}`，与 `timeseries.joint_pos` **同序**（都按关节 index 升序）。
  `upper <= lower` 视为连续/无限位关节，跳过。容差 `TOL` 吸收伺服超调。
- **settled**：
  - `passive` → 看末态线速度模 `final_base_vel_norm`，落定应趋 0。
  - `hold/gait` → 看末态 roll/pitch，翻车表现为接近 ±90°/±180°。

## ⑤ AI 视觉清单（人/AI 看图复核，断言之外的兜底）

`verify_sim` 出 `_verify/{static.png, settled.png}`（首帧/末帧，640×460）。看图核对：

```
① 模型渲出来了（不是空场景 / 灰块）
② 每个 link 都在、形状对（没缺件、没穿模）
③ static：初始姿态在地面上方、朝向合理
④ settled：passive 落定在地面、hold/gait 站住——没下陷、没翻、没飞出视野
⑤ 接触合理（脚/底盘贴地，不悬空也不陷进地里）
```

数值断言抓「爆炸/穿地/越界/翻车」，看图抓「渲染失败/穿模/朝向错」——两者互补，都过才算稳。

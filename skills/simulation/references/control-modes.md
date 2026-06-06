# 控制模式（passive / hold / gait）

> simulation 子技能自包含查询表。GAITS 知识 lift 自 mechanical `gait-planning.md`，按零互引用独立。

`run_sim.py --mode {passive|hold|gait}`。三种模式覆盖「会不会塌/站得稳/动起来稳不稳」三类问题。

| 模式 | 测什么 | 控制 | 典型 steps | 看哪个 check |
|---|---|---|---|---|
| `passive` | 自由跌落：会不会**穿地** / 散架 / 数值爆炸 | 不施加任何电机控制 | 480–1200（2–5 s） | 没穿地 + 没爆炸 + 末速小 |
| `hold` | **站得稳**吗：关节伺服到限位中点，看基座是否保持直立 | 全可动关节 POSITION_CONTROL→中点 | 720–2400 | 关节限位 + 末态没翻 |
| `gait` | 动起来**会不会翻**：相位步态驱动 | 相位偏置正弦 POSITION_CONTROL | 1600–4800 | 末态没翻 + 没爆炸 |

## passive（跌落测试）

不调 `setJointMotorControl2`，只 `stepSimulation()`。机器人在重力下落到地面。
- **没穿地**：`min_base_z > FLOOR_EPS`（base 没穿透 z=0 地面）。
- **末态稳**：末态基座线速度模 < `SETTLE_VEL`（落定了，没继续弹/滚）。

## hold（位置保持/站立）

每步对每个可动关节伺服到限位中点 `(lower+upper)/2`，`force=5.0`：

```python
p.setJointMotorControl2(body, j.index, p.POSITION_CONTROL,
                        targetPosition=(j.lower + j.upper)/2, force=5.0)
```

连续关节（`lower>=upper`）目标取 0。看末态 `|roll|,|pitch| < FLIP_DEG`（没翻车）。

## gait（简单相位步态）

**MVP = 相位偏置正弦**，不是完整 Bezier+IK 足端轨迹。每个可动关节按腿序取相位偏置：

```python
GAITS = {
    "stand": {"phases": [0,0,0,0],        "amp": 0.0,  "period": 1.0},
    "trot":  {"phases": [0,0.5,0.5,0],    "amp": 0.35, "period": 0.8},  # 对角同相
    "crawl": {"phases": [0,0.25,0.5,0.75],"amp": 0.25, "period": 2.0},  # 依次抬腿
}
target = mid + amp * sin(2π·(t/period + phase[leg%4]))   # 再 clamp 进限位
```

- `phases`：四腿相位（trot 对角腿同相、crawl 顺序错开），按可动关节顺序 `leg % 4` 取。
- `amp`：关节摆幅（rad）；`period`：步态周期（s）。
- 关节数 ≠ 4 时退化为按序循环取相位——足够做「会不会翻」的粗判；精细步态属 deferred。

## 进阶（本 MVP 不做）

完整 11 点 Bézier 摆动相 + 解析 IK 足端轨迹、duty/clearance/stride 参数、力矩/速度控制混合，
属后续迭代。本 MVP 只用位置伺服 + 相位正弦，目标是 headless 跑通 + 判稳，不是步态优化。

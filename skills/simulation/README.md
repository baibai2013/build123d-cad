# simulation — 无头动力学仿真子技能

把 URDF/SDF 丢进 **pybullet headless（`p.DIRECT`）** 跑动力学，判「站得稳 / 会不会翻 / 会不会穿地」，
出数据 + 截图给 AI/CI 判定。和 viewer 一样**纯无头、可截图、可进 CI** —— 不弹 GUI、不依赖浏览器。

> 定位：`urdf` 管「描述对」，`simulation` 管「丢进物理引擎跑得稳」。
> 与 `mechanical/scripts/simulation/pybullet_preview.py`（交互式 GUI 调试）互补——本子技能是它的 headless/CI 化对应。

## 为什么单独成子技能

CAD 闭环了「画对」、PCB 闭环了「造得出」，但机器人「动起来对不对」此前只停在**描述层**（urdf/sdf 生成）。
本子技能把动力学仿真升级为**一等公民**：headless 跑 + 自验稳定性 + 截图回归。符合 super-skill 的「子技能自治」原则。

## 安装

```bash
# pybullet 是运行依赖(venv 已装的话直接用)
~/work/build123d-parts-lib/.venv/bin/python -m pip install pybullet
# 可选:出 MP4(否则只出 PNG 关键帧 + manifest)
pip install imageio imageio-ffmpeg   # 或 opencv-python
```

PNG 写盘走 PIL（CAD 栈通常已有）→ imageio → `.npy` 兜底，绝不静默丢帧。

## Quickstart

```bash
VENV=~/work/build123d-parts-lib/.venv/bin/python
R2D2=$($VENV -c "import pybullet_data,os;print(os.path.join(pybullet_data.getDataPath(),'r2d2.urdf'))")

# 跑一次(出 results.json + 关键帧)
$VENV scripts/run_sim.py "$R2D2" --mode passive --steps 1200 --outdir /tmp/simtest

# 自验(退出码 0=稳 / 1=有项挂 / 2=输入错 / 3=缺 pybullet)
$VENV scripts/verify_sim.py "$R2D2" --mode hold --steps 2400 --outdir /tmp/simtest
cat /tmp/simtest/_verify/checklist.txt          # 四项断言 + 看图清单
open /tmp/simtest/_verify/{static,settled}.png  # AI/人 视觉复核
```

## 文件

```
scripts/
  run_sim.py      # producer:headless 跑 N 步 → results.json + frames/ + mp4(best-effort)
  verify_sim.py   # judge:import run_sim 跑一次 + 四项稳定性断言 + _verify/ 截图 + checklist
  sim_render.py   # helper:getCameraImage(ER_TINY) → PNG;mp4 拼帧;可单跑做单帧调试
references/        # pybullet-headless / control-modes / stability-checks / output-contract
tests/             # 结构 smoke + importorskip pybullet 跑 r2d2 极小仿真
```

## 测试

```bash
cd <repo-root> && <venv>/bin/python -m pytest skills/simulation/tests -m smoke -q
```

`test_smoke.py` 无 pybullet 依赖恒跑；`test_sim_smoke.py` 用 `importorskip` —— 缺 pybullet 自动 skip（CI 安全）。

## 零互引用说明

`references/` 的 pybullet/步态知识**刻意从 `mechanical` 仿真 refs lift 而来并独立维护**，
不跨子技能引用（super-skill 的零互引用红线）。重复是该规则的可接受成本。

## Deferred（后续迭代）

- MuJoCo / Gazebo 真跑（Gazebo 世界由 `sdf` 子技能出）
- viewer `engine=sim` 回放（plotly 曲线 + HTML5 video）—— 当前 sim 引擎是占位页
- 完整 Bézier + IK 步态轨迹、力矩/速度控制、golden-diff 回归

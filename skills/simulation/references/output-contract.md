# 产物契约（results.json schema + 路径布局 + handoff）

> simulation 落盘的权威格式。改 schema 要同步 `run_sim.simulate()` 写出处 + `verify_sim` 读处。

## 输出布局

沿用 `shared/handoff-protocols.md` 的 `output/<task>/` 约定，simulation 全落 `output/<task>/simulation/`：

```
output/<task>/simulation/
├── <robot>.results.json        # 时序 + 汇总 + checks(权威产物)
├── frames/
│   ├── frame_0000.png …        # 按 --fps 采的关键帧(永远出,PIL/imageio)
│   └── manifest.json           # 缺 imageio/cv2 时:帧列表 + ffmpeg 拼帧命令
├── <robot>.sim.mp4             # 仅本机有 imageio/cv2 才出(best-effort)
└── _verify/
    ├── static.png              # 首帧(初始姿态)
    ├── settled.png             # 末帧(末态)
    └── checklist.txt           # 四项断言 PASS/FAIL + 看图清单
```

`run_sim.py`/`verify_sim.py` 不传 `--outdir` 时默认落模型同目录的 `simulation/`。

## results.json schema

```jsonc
{
  "meta": {
    "model": "/abs/path/robot.urdf",
    "mode": "passive|hold|gait",
    "gait": "trot|crawl|stand|null",   // 仅 mode=gait
    "steps": 2400, "dt": 0.0041667, "fps": 20,
    "pybullet_api": 202010061           // getAPIVersion(),给未来 golden-diff 用
  },
  "joints": [                           // 全部关节(含 fixed),按 index 升序
    {"name": "...", "index": 0, "type": 0, "lower": -1.57, "upper": 1.57}
  ],
  "timeseries": [                       // 每 --fps 采一帧
    {
      "t": 0.0,
      "base_pos": [x, y, z], "base_rpy": [r, p, y], "base_vel": [vx, vy, vz],
      "joint_pos": [...], "joint_vel": [...],   // 仅 movable 关节,与 joints 里 type∈{0,1} 同序
      "contacts": {"count": 4, "total_normal_force": 12.3}
    }
  ],
  "summary": {
    "min_base_z": 0.31, "max_pos": 0.84, "max_joint_vel": 6.58,
    "final_rpy": [r, p, y], "final_base_vel_norm": 0.02,
    "nan_or_inf": false, "n_samples": 61
  },
  "frames": [{"idx": 0, "t": 0.0, "path": "frames/frame_0000.png"}],
  "checks": {                           // verify_sim 回填;run_sim 单跑时为空 {}
    "no_floor_tunnel": true, "no_blowup": true,
    "joints_within_limits": true, "settled": true
  }
}
```

## handoff（文件接口，不互调函数）

| 链路 | 输入 → 动作 |
|---|---|
| **urdf → simulation** | `output/<task>/<robot>.urdf` + `meshes/` → `loadURDF`（base 目录进 search path 解析相对 mesh） |
| **sdf → simulation** | `output/<task>/{world,model}.sdf` → `loadSDF`（取 `ids[0]`，世界自带地面不叠 plane） |
| **simulation → 用户/CI** | `results.json`（判稳数据）+ `frames/`/`mp4`（回放）+ `_verify/`（截图 + checklist） |
| **simulation → viewer**（未来，非 MVP） | `mp4`/`results.json` → `?engine=sim` 回放（当前 sim 引擎占位，本期不实现） |

规则（同 `shared/handoff-protocols.md`）：路径由调用方传入、被调方不臆造；不认识的后缀（非 `.urdf/.sdf`）明确报错不静默吞。

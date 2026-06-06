# pybullet headless 速查（DIRECT + 离屏渲染）

> 本文是 simulation 子技能自包含的查询表。知识 lift 自 mechanical 仿真 refs，按**零互引用**刻意独立。
> 不在本表的 API 先查官方 [PyBullet Quickstart Guide](https://github.com/bulletphysics/bullet3/blob/master/docs/pybullet.md) 再补，不凭印象。

## 1. 无头连接与搜索路径

```python
import pybullet as p, pybullet_data
cid = p.connect(p.DIRECT)                              # 永远 headless,绝不 p.GUI
p.setAdditionalSearchPath(pybullet_data.getDataPath()) # plane.urdf 等内置资源
p.setAdditionalSearchPath(os.path.dirname(model))      # 解析模型相对 meshes/
p.setGravity(0, 0, -9.81)
p.setTimeStep(1/240)                                   # 240 Hz 是 pybullet 稳定默认
```

- **mesh 路径**：URDF 里若是相对路径（`meshes/foo.stl`），必须把模型所在目录加进 search path。
  `package://xxx/...` URI pybullet **不解析** → 让 urdf 子技能出相对路径；遇到 `package://` 应 fail-loud 提示展平。

## 2. 加载：loadURDF vs loadSDF

```python
# URDF —— 单个 body id
body = p.loadURDF(model, basePosition=[0,0,0.3],
                  useFixedBase=False, flags=p.URDF_USE_SELF_COLLISION)

# SDF —— 返回 tuple(一个世界可含多 body),且无 basePosition/useFixedBase kwarg
ids = p.loadSDF(model); body = ids[0]
p.resetBasePositionAndOrientation(body, [0,0,0.3], [0,0,0,1])
```

- `.urdf`：自己 `loadURDF("plane.urdf")` 铺地面。
- `.sdf`：world 通常**自带地面/灯光** → 不要再叠 plane（否则双地面）。
- `URDF_USE_SELF_COLLISION`：碰撞几何重叠时会在 t=0 炸 → 设成开关；爆炸多半是几何重叠，不是仿真 bug。

## 3. 关节信息与控制

```python
for i in range(p.getNumJoints(body)):
    info = p.getJointInfo(body, i)
    name, jtype, lower, upper = info[1].decode(), info[2], info[8], info[9]
    # jtype: 0=revolute 1=prismatic 4=fixed;可动 = (0,1)

# 位置伺服(hold/gait 都用这个)
p.setJointMotorControl2(body, idx, p.POSITION_CONTROL, targetPosition=q, force=5.0)
# 另有 VELOCITY_CONTROL / TORQUE_CONTROL(本 MVP 不用)
```

`lower >= upper` 表示连续/无限位关节 → 限位检查时跳过。

## 4. 推进与采样

```python
p.stepSimulation()                                  # headless 不要 time.sleep
pos, orn = p.getBasePositionAndOrientation(body)
rpy = p.getEulerFromQuaternion(orn)
lin, ang = p.getBaseVelocity(body)
states = p.getJointStates(body, [idx0, idx1, ...])  # 每个 (pos, vel, reactionForces, appliedTorque)
contacts = p.getContactPoints(body, plane)          # c[9] = normalForce
```

## 5. 离屏渲染（关键帧 PNG）

```python
view = p.computeViewMatrixFromYawPitchRoll(
    cameraTargetPosition=pos, distance=1.0, yaw=45, pitch=-30, roll=0, upAxisIndex=2)
proj = p.computeProjectionMatrixFOV(fov=60, aspect=w/h, nearVal=0.01, farVal=100)
rw, rh, rgba, depth, seg = p.getCameraImage(w, h, view, proj, renderer=p.ER_TINY_RENDERER)
arr = np.asarray(rgba, dtype=np.uint8).reshape(rh, rw, 4)[:, :, :3]  # 用返回的 rw,rh!
```

- **必须用 `ER_TINY_RENDERER`**（CPU 软光栅器）：p.DIRECT 无 GL context 也能渲。
  `ER_BULLET_HARDWARE_OPENGL` 需 GL/EGL，headless 会失败。
- rgba 可能是 flat list → 用**返回的** `rw,rh` reshape（pybullet 可能 clamp 尺寸），别用请求值。
- pybullet 自身无 PNG 编码器 → 用 PIL / imageio 写盘（见 `sim_render.py` 兜底链）。
- 小尺寸（640×460 ≈ 390 token/张）省 AI 视觉 token；smoke 用 160×120。

## 6. 收尾

```python
finally:
    p.disconnect(cid)   # 永远在 finally,别泄连接
```

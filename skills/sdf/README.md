# sdf 子技能

SDFormat / Gazebo 仿真世界生成。L1(`scripts/sdf/`)整块复刻 earthtojake/text-to-cad
(MIT,见 `LICENSE`),L2 适配层(`scripts/export_sdf.py`)吃 `world.yaml` + 上游 URDF →
出 `model.sdf`(URDF→SDF model)+ `world.sdf`(注入 physics/ground/light/include/sensors)。

> 注意:本 SDF 是 **SDFormat 仿真描述**,不是 signed-distance-field 几何。

详细规格见 [04 文档 §11](../../../share/build123d-cad改造/04-机器人描述子技能-urdf-srdf-sdf.md);
跨技能数据契约 `world.yaml` v1 schema 见
[`shared/schemas/world.schema.json`](../../shared/schemas/world.schema.json)。

## 用法

```bash
# 1) 先用 urdf 子技能出 URDF
python skills/urdf/scripts/export_urdf.py \
    shared/schemas/example/single_leg.joints.yaml -o /tmp/dog/

# 2) 再出 SDF(world + model)
python skills/sdf/scripts/export_sdf.py \
    shared/schemas/example/playground.world.yaml \
    --urdf /tmp/dog/robot.urdf -o /tmp/dog/

# 期望产物:
#   /tmp/dog/world.sdf                    ← <sdf><world> + physics/light/include/ground
#   /tmp/dog/model.sdf                    ← URDF→SDF model(含 yaml 注入的 sensor)
#   /tmp/dog/dog_playground_gen_sdf.py    ← L1 passthrough 生成器源
#   /tmp/dog/_errors/sdf.json             ← 仅当本机无 gz-tools(见下)
```

不给 `--urdf` 时只出 `world.sdf`(用 `model://` include 引用外部 model)。

L1 原 CLI(零改动复刻)保留:

```bash
cd skills/sdf/scripts && python -m sdf <some_gen_sdf>.py -o model.sdf --gz-check auto
```

## URDF → SDF 转换路径(04 §11.3 / R3)

- **`gz` 在 PATH**:走官方 `gz sdf -p robot.urdf`,语义保真、版本跟随 sdformat。
- **`gz` 缺失**:走自写转换器 fallback,只覆盖 `link / joint / inertial / visual / collision`
  5 个 tag(sensor 仅注入 yaml 声明的、plugin 缺省),并在 `_errors/sdf.json` 标
  `gz_unavailable=true`。要高保真请先 `brew install ignition-tools`(macOS)/
  `apt install libgz-tools2`(Ubuntu)再重跑。

> 自写转换器把 URDF 关节链 origin 累乘成每个 link 在 model 系下的绝对 `<pose>`(零关节角姿态),
> rpy 用 URDF 固定轴约定 `R = Rz·Ry·Rx`。

## 依赖

```
pyyaml >= 6.0
jsonschema >= 4.20
cadpy_metadata        # 复用 shared/python/cadpy_metadata(R5,见 requirements.txt)
gz-tools              # 可选,缺时走 fallback
build123d 或 trimesh  # 可选,本子技能不直接用(mesh 由 urdf 子技能 STEP→STL)
```

## 验收 / 测试

```bash
cd skills/sdf && pytest tests/ -v
# test_schema_validate  world.schema.json 自检 + example 校验
# test_export_sdf       export_sdf 行为(link/joint/sensor 计数、ground、不变量)
# test_urdf_to_sdf      自写转换器 5-tag + SE(3) 位姿累乘 + rpy 往返
# test_l1_passthrough   L1 bundled validation + 完整 `python -m sdf` CLI 不破
```

本子技能 P1 只过 **结构校验 + `gz sdf --check`(若装)**;真跑 Gazebo 仿真留 P2
(本机无 ROS/Gazebo,见 04 §13 R7)。viewer sim 引擎对接也是 P2(`viewer.url` 暂留空)。

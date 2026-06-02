# urdf 子技能

URDF 机器人描述生成。L1(`scripts/urdf/`) 整块复刻 earthtojake/text-to-cad
(MIT,见 `LICENSE`),L2 适配层(`scripts/export_urdf.py`)吃 mechanical 出的
STEP + `joints.yaml` → 写 `gen_urdf()` Python 源 → 调 L1 CLI 校验 → 出
`robot.urdf` + `meshes/`。

详细规格见 [04 文档](../../../share/build123d-cad改造/04-机器人描述子技能-urdf-srdf-sdf.md);
跨技能数据契约 `joints.yaml` v1 schema 见
[`shared/schemas/joints.schema.json`](../../shared/schemas/joints.schema.json)。

## 用法

```bash
python skills/urdf/scripts/export_urdf.py \
    shared/schemas/example/single_leg.joints.yaml \
    -o /tmp/dog/

# 期望产物:
# /tmp/dog/robot.urdf
# /tmp/dog/dog_left_front_leg_gen_urdf.py
# /tmp/dog/meshes/<link>.stl   (如果 STEP 文件在场且 build123d/trimesh 可用)
```

L1 原 CLI(零改动复刻)保留:

```bash
cd skills/urdf/scripts && python -m urdf <some_gen_urdf>.py -o robot.urdf
```

## 依赖

```
pyyaml >= 6.0
jsonschema >= 4.20
pybullet >= 3.2.5    # 仅 tests/smoke 验收
build123d 或 trimesh # 可选,STEP→STL,缺时跳过 mesh
```

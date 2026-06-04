# URDF Workflow

Use this reference when editing robot-description structure, frame placement, mesh references, inertial data, or generated URDF output.

## Edit Loop

1. Find the Python source that defines `gen_urdf()`.
2. Treat that Python source as source of truth and the `.urdf` file as generated.
3. Identify target consumers and strictness requirements: visualization, TF tree, simulation, planning, or real robot integration.
4. Create or update the design ledger before changing frames, origins, axes, limits, mesh scales, or inertials.
5. Apply URDF frame semantics: joint origin in parent frame, child link frame at joint frame, joint axis in joint frame, visual/collision/inertial origins in link frame.
6. Edit links, joints, limits, axes, origins, inertials, materials, visual/collision geometry, and mesh filenames deliberately in the generator source.
7. Regenerate only the explicit URDF target with `scripts/urdf <source-file>`, `scripts/urdf <source-file> -o <output.urdf>`, or `scripts/urdf <source-file>=<output.urdf>`.
8. Let generation-time validation catch structural and semantic problems. Fix the generator source instead of hand-editing generated XML.
9. If mesh outputs changed, regenerate only the affected explicit outputs with the owning CAD or mesh workflow.
10. Hand generated or modified `.urdf` files to `$cad-viewer` for live viewer links when available.
11. When available, run a consumer smoke test and report what was not checked.

## Spatial-Reasoning Guardrails

LLMs are prone to plausible-looking spatial mistakes. Use these guardrails:

- Do not infer dimensions, handedness, axes, mesh units, or joint signs from vague descriptions.
- Do not silently mirror left/right parts unless the mirror transform and sign changes are explicit.
- Do not assume visual mesh origin equals link frame, collision frame, or center of mass.
- Do not assume CAD mesh units are meters. STL files often carry no reliable unit metadata.
- Do not encode a kinematic correction by offsetting only the visual mesh; correct the link and joint frames unless the visual mesh is genuinely offset.
- Preserve existing proven transforms unless the task explicitly requires changing them.
- Use named constants and comments for assumptions.

## Standard Link Tags

Use these tags for each link that represents physical robot geometry:

- `inertial`: mass, center of mass, and inertia tensor used by simulators.
- `visual`: display geometry and optional material.
- `collision`: contact geometry used by physics and planning.

Frame-only links, such as `base_footprint`, optical frames, or tool-center marker frames, may intentionally omit these tags when they represent no physical mass or geometry.

For movable physical links, avoid zero or missing mass unless the target simulator explicitly supports that modeling choice. If exact mass properties are unavailable, use a documented approximation and make the approximation easy to replace later.

## Joint Authoring

For every joint, confirm:

- parent and child direction are correct;
- joint origin is expressed in the parent link frame;
- child link frame is intended to coincide with the joint frame;
- non-fixed joint axis is expressed in the joint frame;
- positive motion is documented;
- revolute limits are radians;
- prismatic limits are meters;
- continuous joints are not given artificial finite lower/upper limits;
- fixed joints are used for frame relationships and rigid assemblies.

Supported joint types may vary by project runtime. If the validator/runtime supports only `fixed`, `continuous`, `revolute`, and `prismatic`, do not author `floating` or `planar` joints unless the consumer and validation path support them.

## Mesh References

URDF mesh filenames should be stable from the generated URDF file's perspective or use a package URI convention understood by the consumer.

The current `scripts/urdf` validation path accepts any non-empty mesh filename or URI. Local relative mesh paths are checked relative to the generated URDF file; `package://...` and remote references are left unresolved with warnings unless a package map is supplied through `read_urdf_source()`.

When using package URIs, confirm the consuming environment resolves the package root the same way as the generated URDF expects.

Do not use generated URDF XML as the source of truth for mesh placement. Prefer deriving visual mesh references from the same source data that owns the mesh instance placement.

When mesh references point to generated assets, keep the ownership clear:

- CAD or mesh workflows own mesh generation;
- URDF generation owns references, scales, and placements;
- SRDF/MoveIt workflows own semantic groups, named joint poses via `<group_state>`, and planning metadata.

## Collision Geometry

Add collision geometry under each `<link>` that should participate in physics, contact, or collision-aware planning. Do not encode collision behavior on joints.

Use one or more `<collision>` blocks per link. The `<origin>` is expressed in the link frame, just like `<visual>`, and mesh scales must match the units of the exported mesh:

The current `scripts/urdf` validator allows visual and collision geometry to use `<mesh>`, `<box>`, `<cylinder>`, or `<sphere>`.

```xml
<link name="forearm_link">
  <visual>
    <origin xyz="0 0 0" rpy="0 0 0" />
    <geometry>
      <mesh filename="package://robot_description/meshes/forearm.stl" scale="0.001 0.001 0.001" />
    </geometry>
  </visual>
  <collision>
    <origin xyz="0.12 0 0" rpy="0 1.57079632679 0" />
    <geometry>
      <cylinder radius="0.035" length="0.24" />
    </geometry>
  </collision>
</link>
```

Prefer simplified collision geometry over detailed visual meshes. Good options, from simplest to most specific:

- primitive `<box>`, `<cylinder>`, or `<sphere>` geometry when it approximates the part well;
- a coarse, closed collision mesh exported from CAD;
- the visual mesh as a temporary fallback for loading and smoke tests.

In generator sources, model collisions explicitly rather than hand-editing generated URDF. A common pattern is to add a `collisions` collection beside `visuals` in each link spec and emit it with the same origin and scale helper code used for visual meshes.

## Inertials

For each physical link, use an explicit `inertial` block when the target simulator or dynamics consumer needs mass properties.

The inertial origin is the center of mass in the link frame. It is not automatically the visual mesh origin, collision origin, or link origin.

When exact mass properties are unavailable, use a documented approximation and make it easy to replace. Mark approximate mass, COM, and inertia constants clearly.

## Smoke Tests

After generation-time validation, use the most relevant available smoke test:

- load in RViz or equivalent visualization to inspect visible placement;
- run robot_state_publisher or equivalent to check the TF tree;
- load in Gazebo/Ignition or another simulator for physics consumers;
- load in MoveIt only after URDF structure is stable, then handle semantic data through the SRDF workflow.

Report the smoke tests run and any skipped checks that would materially affect confidence.

## Render-Verify + Fix Loop(自我验证闭环,适用任何 URDF)

无论 URDF 是 `gen_urdf()` 生成的、纯 primitive(box/cylinder/sphere,无网格文件)、还是引用 STL/GLB/
纹理网格——**落地后都应在 cad-viewer 里自我渲染验证一遍,发现问题就改、再验,直到通过**。不要只靠
生成期 XML 校验(那只查结构,查不出朝向/单位/关节轴/网格加载这些只有渲染才暴露的问题)。

固化脚本(headless,勿弹可见标签页):
```
~/work/build123d-parts-lib/.venv/bin/python scripts/verify_urdf.py <urdf> [--joint NAME] [--deg 60]
```
自动起服务 → 截 `static.png` + 驱动一个关节的 `driven.png`(默认 640×460 小图省 AI token)→ 抓控制台
报错 → 打印核对清单。需用装了 playwright + chromium 的解释器(build123d-parts-lib 的 .venv)。

核对清单:① 无报错且渲出来(没 `Failed to load render mesh`)② 每个 link 都在、形状对 ③ 朝向对
④ 居中、相对位置/原点对 ⑤ 关节面板列出可动关节,驱动后对应 link 绕正确轴动、mimic 联动对
(有纹理再加查贴图显示+跟随)。

常见故障 → 对症修复:

| 现象 | 根因 | 修法 |
|---|---|---|
| `Failed to load render mesh` / `Invalid typed array length` / `allocation failed` | 网格 URL 扩展名在 `?file=` query,格式判定回落 STL 把 GLB 当 STL 解析 | 已修 viewer `meshLoaders.js`;复发查该处 |
| 某 link 不显示 | 网格路径错/文件缺;或被其它 link 遮挡 | 核对 `filename` 相对路径与文件存在;换视角确认是否遮挡 |
| GLB 网格的 link 缩在原点/重叠、转动不对 | viewer 把 GLB ×1000 但关节原点是米,几何放大 1000× | GLB 顶点 ×1e-6(见 `references/textures.md` §2.3);根因是 viewer 既有单位 bug |
| GLB 网格的 link 朝向歪 90° | GLB 不是 Y-up | 生成 GLB 时 Z-up→Y-up `(x,y,z)→(x,z,-y)` |
| 关节面板「No movable joints」 | 关节全 fixed/mimic,或 URDF 解析失败 | 确认有非 fixed、非纯 mimic 关节;先排查渲染报错 |
| 关节驱动后 link 绕错轴/不动/穿插 | `<axis>`、`origin`、parent/child 或 mimic multiplier 错 | 核对 frame-semantics;改 `gen_urdf()` 源重生成再验 |
| 「没居中/朝向不对」但模型其实对 | viewer 按文件名记住相机,复用了上次手动视角 | 换文件名=默认框定;gizmo 顶端切俯视;工具栏准星复位 |

改 URDF 一律改 `gen_urdf()` 源、重生成,再跑本验证;不手改 XML。

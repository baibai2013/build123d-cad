# 示例:木纹行星齿轮(URDF 每 link 纹理 + 关节动画)

「制作纹理 URDF」工作流的成品样例,配合 [`../../textures.md`](../../textures.md) 阅读。

- `planetary_wood.urdf` — 6 个 link(齿圈/太阳轮/行星架/3×行星轮),`continuous` + `mimic` 关节;
  每个 visual 引用 `wood_meshes/<part>.glb`(已烘木纹 baseColorTexture)。

## 网格 GLB 不在版本库里

本技能 `.gitignore` 忽略 `*.glb`/`*.stl`(生成产物不纳入版本控制),所以 `wood_meshes/*.glb` 不随技能提交。
两种拿到方式:

1. **自己再生**(从行星齿轮 STL,推荐):
   ```bash
   mkdir -p wood_meshes
   STL=~/work/build123d-cad-skill-test/tests/24-planetary-gear/output/planetary_urdf/meshes
   for p in ring sun carrier planet_1 planet_2 planet_3; do
     # scale 1.0 保持毫米源单位;URDF 里各 <mesh scale="0.001"> 接米制(见 textures.md §2)。末参=木种色调
     python ../../../scripts/stl_to_wood_glb.py "$STL/$p.stl" "wood_meshes/$p.glb" 1.0 oak
   done
   ```
   建议各 link 用不同木种区分:齿圈 oak、太阳轮 cherry、行星架 maple、行星轮 walnut。
2. skill-test `tests/24-planetary-gear/wood_textured/wood_meshes/` 的现成二进制是**旧单位(`1e-6`)**,
   与当前 viewer(`unitScale=1` + URDF `<mesh scale="0.001">`)不兼容,请用上面方式1再生。

## 看效果

```bash
bash ~/.agents/skills/build123d-cad/skills/viewer/scripts/start.sh <abs-path>/planetary_wood.urdf
```
打开输出的 URL → ▶ 播放看太阳轮带动行星轮转、木纹跟随;gizmo 顶端切俯视能看清咬合与居中。

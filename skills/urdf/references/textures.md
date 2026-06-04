# 制作纹理 URDF 工作流(设计 → 制作 → 验证 → 修改 → 展示)

> 目标:让 URDF **每个 link 显示其 GLB 网格自带的 baseColor 贴图**,且关节运动时纹理跟随。
> 渲染由 cad-viewer 引擎完成(`$cad-viewer`):带纹理 link 走「旁路直渲」——主线程 GLTFLoader
> 加载原始 `gltf.scene` 保留贴图,套标定矩阵 + 运动学 `part.transform`,随关节动;无纹理 link 走
> 合并快路径。这是 SW/Fusion/FreeCAD 的标准做法(几何常驻、每帧只更 per-link 矩阵、材质跟零件走)。
> 脚本:`scripts/stl_to_wood_glb.py`(STL→木纹 GLB 模板)。示例:`references/examples/wood-planetary/`
> (URDF + README;GLB 被 .gitignore,见 README 再生/取用)。现成二进制 demo 在 skill-test
> `tests/24-planetary-gear/wood_textured/`。

## 1. 设计

- 选定哪些 link 要纹理(通常 visual link 全要)。
- **纹理来源——先问用户,别擅自决定**:
  - **用户提供**:用户给贴图图片(png/jpg)或材质名 → 直接把该图嵌成 GLB 的 baseColorTexture。
    多 link 时问清每个 link 用哪张、是否区分,以及贴图平铺/朝向。
  - **自动生成**:用户没图、只说"木纹/金属/某材质感" → 程序化生成贴图(如 `stl_to_wood_glb.py`
    的木纹)。生成前把材质风格、配色、是否各 link 用不同色调区分跟用户对齐。
  - 默认:用户没明确给图就先问一句「贴图你提供,还是我按某材质感生成?」,得答复再做。
- 选 **UV** 方式:基础面零件可平面投影(把 link 正面投到 UV);复杂件需真实 UV 展开。
- 规划**朝向**与**单位**(见 §2 两个硬约束),否则必返工。

## 2. 制作(把每个 link 的 mesh 做成「合规」纹理 GLB)

GLB 必须同时满足三点,缺一即出问题:

1. **带 UV + baseColorTexture**。STL 无 UV/材质,必须转 GLB 并烘贴图。
2. **Y-up 朝向**。glTF 标准 Y-up,viewer 会 Y-up→Z-up({x,y,z}→{x,-z,y})。CAD/URDF 是 Z-up,
   故从 STL(Z-up)生成时先转 **(x,y,z)→(x,z,-y)**,viewer 再转回正好复原。漏了 → 零件立起来 90°。
3. **单位**。viewer 把 GLB 顶点 **×1000**(假设 GLB 米→显示毫米),**但 URDF 关节原点仍是米**。
   为让几何与关节原点同尺度,GLB 顶点应 authored 在 **米 ÷ 1000**(从 mm 源乘 `1e-6`)。漏了 →
   几何相对关节间距放大 1000 倍,带非零关节偏移的多 link **全缩在原点重叠、看不见**(单 link 看不出)。

URDF 引用:`<mesh filename="meshes/x.glb"/>`,**不要再写 scale**(缩放已烘进 GLB);关节/mimic/origin 照旧。
按本技能常规:改 `gen_urdf()` 源,不手改 XML。

工具:`scripts/stl_to_wood_glb.py <in.stl> <out.glb> <scale> <tone>`(scale 用 `1e-6`)——解析二进制
STL、程序化木纹 PNG、平面投影 UV、Z-up→Y-up、写 GLB。照搬改贴图来源即可(**用户提供贴图时**把
`make_wood_png()` 换成读取用户的 PNG 字节直接嵌入)。

## 3. 验证(headless,勿弹可见标签页)

起服务:交给 `$cad-viewer`,或 `bash skills/viewer/scripts/start.sh <abs.urdf>` → 输出唯一 URL。

headless 截图(playwright headless chromium;用 `~/work/build123d-parts-lib/.venv/bin/python`,已装
chromium;`web_preview._chromium_installed()` 有 PATH bug,直接用 playwright):

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(args=["--use-gl=angle","--use-angle=swiftshader","--ignore-gpu-blocklist"])
    pg=b.new_page(viewport={"width":640, "height":460})   # ← 截图尺寸要小,省 AI token(见下)
    pg.goto(URL, wait_until="load", timeout=30000); pg.wait_for_timeout(6000)
    pg.screenshot(path="check.png")
    inp=pg.query_selector('input[aria-label="<joint_name> value in deg"]')   # 驱动关节验证纹理跟随
    inp.click(); inp.fill("60"); pg.keyboard.press("Enter"); pg.wait_for_timeout(3000)
    pg.screenshot(path="check_driven.png")
```

**截图尺寸省 token**:喂给 AI 看的截图按 ~视口面积/750 计 token(1100×760≈1100 token,640×460≈390 token)。
验证用截图设小视口(640×460 上下足够看清朝向/咬合/纹理);只有要抠细节时才用大图。批量帧更要压尺寸。

逐项核对:① 每个纹理 link 显示贴图(非灰模);② 朝向——平躺在 XY、Z 薄(比 bounds:`X/Y >> Z`);
③ 居中——bounds 关于原点对称、装配中心在 (0,0);④ 咬合/相对位置正确;⑤ 拖关节 → 纹理 link 跟随。
node 里 import cadjs 需 `globalThis.self=globalThis`(three 用 self)。

## 4. 迭代修改(常见问题 → 对症)

| 现象 | 根因 | 修法 |
|---|---|---|
| 零件立起来 90° | GLB 不是 Y-up | 生成时 (x,y,z)→(x,z,-y) |
| 多 link 缩在原点/看不见、转动不对 | GLB×1000 vs 关节米制,几何放大 1000× | GLB 顶点乘 `1e-6` |
| `Invalid typed array length`/`allocation failed` | mesh URL 扩展名在 `?file=` query,格式判定回落 STL 把 GLB 当 STL 解析 | 已修 viewer `meshLoaders.js`(回看 file query 扩展名);复发查此处 |
| 各零件糊在一起分不清 | 同一种纹理 | 不同 link 不同色调/贴图 |
| "没居中/朝向不对"但模型其实对 | viewer **按文件名记住相机**,复用了上次手动转到的视角 | 换文件名=默认框定;gizmo 顶端(Z)切俯视;工具栏"准星"复位 |

## 5. 给用户展示

- 给 localhost 链接 + 看法:gizmo 顶端切俯视、工具栏准星复位相机、▶ 播放或拖关节滑块。
- **主动提示是否演示纹理动画**:展示静态后,问用户「要不要看关节转动时纹理跟随的动画?」要的话用
  §3 的驱动法逐帧截图(尺寸压小)或让其点 ▶,呈现纹理随关节运动。

## 6. 已知核心问题(建议单独修)

§2.3 单位不一致是 **viewer 对「GLB 网格 + 米制关节原点」URDF 的既有 bug**,合并路径同样中招,影响
任何用 GLB 网格的 build123d URDF(含机器狗)。当前靠生成端 `1e-6` 缩放绕过。**正路是 viewer 核心修复**:
让 URDF 渲染对 GLB 几何与关节原点采用一致单位(GLB-URDF 不 ×1000,或关节原点也 ×1000)。
维护落点:`viewer-src/packages/cadjs/src/lib/render/glbMeshData.js`(`buildGlbToCadCalibrationMatrix`/
`resolveGlbCadConversion`)、`lib/urdf/kinematics.js`、`components/CadViewer.js`
(`mountUrdfTexturedGroups`/`syncUrdfTexturedGroups`)、`common/cadScene.js`(`applyObjectMatrix`)。

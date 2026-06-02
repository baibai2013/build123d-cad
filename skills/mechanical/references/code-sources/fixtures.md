# 工装夹具领域(Fixtures)

> 场景:加工夹具、定位销、压板、t-slot 工装、测试治具、反求测量治具。
> 在本仓的语义 = **装夹件 / 工装夹具 / 测试治具**(给零件做加工或反求测试时用)。
> 核心原则:**夹具几何高度同质化,先翻 build123d examples 与 cqparts;不要从零写**。

---

## 候选源(5 个,P1-3 落定)

### 1. build123d 官方 examples ★★★★★

- **URL**:https://github.com/gumyr/build123d/tree/dev/examples
- **价值**:夹具典型样式(底板 + 定位销 + 压板)在 examples 下有现成
- **借鉴点**:
  - `examples/handle.py`、`examples/build_handle.py` 等可借鉴 boss + 沉孔 + clamp 思路
  - 与 `references/parts/patterns.md` 第 13/14/15 模式直接对应
- **stack**:Python / build123d
- **license**:Apache 2.0
- **license_status**:pending(本仓亦 Apache 2.0,无缝;但每条 example 文件头复核)
- **retrieved_at**:2026-06-02
- **借鉴注意**:同 license,直接抄就行,文件头加注 `# 参考: gumyr/build123d@<hash> examples/<file>.py (Apache-2.0)`

### 2. CadQuery cqparts ★★★★

- **URL**:https://github.com/fragmuffin/cqparts
- **价值**:标准夹具件(t-slot extrusion / 钳口 / 销 / 销座)有库
- **借鉴点**:
  - `cqparts.fasteners` 钳口和压板风格
  - t-slot 横截面参数化(40×40 / 20×20)
- **stack**:Python / CadQuery(借鉴时走 cadquery-to-build123d.md 翻译)
- **license**:Apache 2.0
- **license_status**:pending
- **retrieved_at**:2026-06-02
- **借鉴注意**:CadQuery → build123d 翻译走本目录 `cadquery-to-build123d.md` 规则

### 3. OpenJSCAD MachineLib ★★

- **URL**:https://github.com/jscad/OpenJSCAD.org/tree/master/packages/lib
- **价值**:机械工装库(夹具 / 导槽 / 滑轨)的几何思路参考
- **借鉴点**:
  - 仅"几何思路"层面参考,不直接抄 JS 代码
  - 用作"夹具有哪些常见样式"的灵感库
- **stack**:JavaScript(只参考几何思路,不翻译代码)
- **license**:MIT
- **license_status**:pending
- **retrieved_at**:2026-06-02

### 4. Misumi 工业图册(尺寸基准)★★★

- **URL**:https://misumi-techcentral.com / https://us.misumi-ec.com
- **价值**:工业夹具尺寸基准(销座 / V-block / clamp / 滑轨等)的事实尺寸
- **借鉴点**:
  - 标准件尺寸数字 → 进 `references/data-sources/<标准件>.yaml`
  - 不复制图纸/截图/版式
- **stack**:技术资料(非代码)
- **license**:proprietary(技术资料)
- **license_status**:pending(限制使用,只引用尺寸事实)
- **retrieved_at**:2026-06-02
- **借鉴注意**:**红线 #4** —— 只复述参数与公开数值,不复制原图与版式;引用要标 `# 尺寸来源:Misumi 图册 <文档名> <URL>`

### 5. kicad-fixtures(公司内部占位)

- **URL**:_TBD,P2 沉淀_
- **价值**:本公司在使用过程中沉淀的私有夹具(测试治具 / 反求测量治具)
- **借鉴点**:仅本公司内部使用,不公开
- **stack**:build123d
- **license**:proprietary(公司内部)
- **license_status**:n/a
- **retrieved_at**:n/a

---

## 借鉴流程

同 `robotics.md` 流程,差异:

- 夹具高同质化,优先级:**build123d examples > cqparts > OpenJSCAD > Misumi**
- 走 Playbook §S2.5 / P2.0 / R4.0,优先 ★★★★★ 候选
- Misumi 等 datasheet 引用要在文件头标 `# 尺寸来源: Misumi <doc> <URL>`,数字写常量

---

## 典型场景

| 场景 | 推荐候选 |
|---|---|
| 加工夹具底板 | build123d examples + cqparts |
| 定位销 / 销座 | cqparts.fasteners + Misumi 标准 |
| t-slot 工装 | cqparts t-slot |
| 测试治具(反求拍照)| build123d examples 自定 + 内部 kicad-fixtures |
| V-block / clamp | OpenJSCAD MachineLib(只参考思路)+ Misumi 尺寸 |

---

## 待补充(P1+)

- **OpenBuilds** parts catalog(t-slot 全套)
- **Hammond Manufacturing** 仪表盒(给电控盒做夹具时参考)
- 公司内部 fixtures 沉淀(P2)

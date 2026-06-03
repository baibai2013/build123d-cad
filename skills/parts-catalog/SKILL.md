---
name: build123d-cad-parts-catalog
description: |
  build123d 标准件目录子技能。在自己建模之前先回答「这个件别人画过没?能直接用吗?」
  覆盖：① 常用标准件索引(轴承 608/625/MR/skf、M2-M8 螺丝/螺母/垫片、SG90/MG996R 舵机、
  NEMA8/14/17 步进、O 型圈、卡簧、销轴);② STEP 来源策略与 license 红线
  (McMaster-Carr / GrabCAD / TraceParts / 厂商官网);③ 与 build123d-parts-lib 仓库对接
  (parts_lib: 字段 → make_xxx() 工厂函数);④ 落盘 STEP → handoff 给 mechanical 装配。
  触发词:找现成件、标准件、STEP 下载、McMaster、GrabCAD、TraceParts、608 轴承、
  M3 螺丝、SG90、NEMA17、O 型圈、卡簧、screw、bearing、fastener、part library。
  本子技能不做:从零参数化建模(→ mechanical)、URDF(→ urdf)、网页预览(→ viewer)。
---

# build123d-cad · parts-catalog 子技能

> 「能买到现成件就别自己画。能从开源库 import 就别下载 STEP。能下 STEP 就别拍照反求。」

收到机械需求里出现**标准件型号**(608ZZ / M3x10 / SG90 / NEMA17 / O 型圈…)时,
**先走本子技能**,再 handoff 给 mechanical 做装配——而不是让 mechanical 凭空建模。

---

## AI 执行准入序列(每次会话第一件事)

1. 读本 SKILL.md 的「四级查找优先级」表,知道按什么顺序找件。
2. 命中 build123d-parts-lib 已收录件 → 直接 `import` + 加入装配,**不要下 STEP、不要重建**。
3. 库里没有 → 按「STEP 来源策略」找官方 STEP,落盘到 `output/<task>/parts/`。
4. 都找不到 → 回退到 mechanical 子技能从规格书参数化建模。
5. **禁止**:跳过 parts-lib 直接下 STEP;不标 license 引入第三方 STEP;凭印象写尺寸。

---

## 四级查找优先级(按这个顺序问自己)

| 级 | 来源 | 命中后做什么 | 何时跳到下一级 |
|---|---|---|---|
| L1 | `build123d-parts-lib` 工厂函数 | `from build123d_parts_lib.parts.<cat>.<mod> import make_xxx` | 该型号未在 yaml 中收录 |
| L2 | 厂商官网 / McMaster-Carr STEP | 下载 → 落 `output/<task>/parts/<id>.step` → `import_step()` | 厂商无 STEP 或 license 不允许 |
| L3 | GrabCAD / TraceParts / 3DContentCentral | 同上,**必须记录原始 URL + license** | 找不到匹配型号 |
| L4 | 规格书参数化重建 | handoff 给 mechanical 子技能从 PDF 尺寸建模 | — |

> 详细索引见 `references/standard-parts-index.md`,STEP 来源 license 速查见 `references/step-sources.md`。

---

## L1: build123d-parts-lib 已收录件(优先用)

仓库:`/Users/liyijiang/work/build123d-parts-lib/`(本机 editable 已装)。
所有件都是 **factory 函数返回 `Part`/`Compound`**,可直接装入装配。

### 起手公式

```python
# 1. 查 yaml 看支持型号
# cat build123d_parts_lib/parts/<category>/<category>.yaml | head

# 2. import 工厂函数
from build123d_parts_lib.parts.bearings.ball_bearing import make_ball_bearing
from build123d_parts_lib.parts.fasteners.socket_head_screw import make_socket_head_screw
from build123d_parts_lib.parts.servos.sg90 import make_sg90

# 3. 实例化加入装配
b = make_ball_bearing(model="608ZZ")
s = make_socket_head_screw(model="M3", length=10)
servo = make_sg90()
```

### 已收录类目速览(完整索引在 references/standard-parts-index.md)

| 类目 | 模块路径 | 代表型号 |
|---|---|---|
| 深沟球轴承 | `parts.bearings.ball_bearing` | 608ZZ / 625ZZ / 626ZZ / 6000ZZ / 6001-2RS / 6002ZZ |
| 微型轴承 | `parts.bearings.mr_bearing` | MR63ZZ / MR74ZZ / MR84ZZ / MR85ZZ / MR105ZZ |
| 法兰/角接触/薄壁/滚针/直线衬套 | `parts.bearings.*` | 见 `bearings.yaml` / `lm_bearings.yaml` |
| 内六角螺丝(ISO 4762) | `parts.fasteners.socket_head_screw` | M2 / M2.5 / M3 / M4 / M5 / M6 / M8 / M10 |
| 圆头/沉头/十字/一字螺丝 | `parts.fasteners.screw_*` | 见 `fasteners.yaml` |
| 六角/方/法兰/翼形/T 槽螺母 | `parts.fasteners.nut_*` | 同上 |
| 平/弹簧/锯齿垫片 | `parts.fasteners.washer` | 同上 |
| 螺纹热熔铜套 | `parts.fasteners.threaded_insert` | M2 / M3 / M4 / M5 |
| 拉铆螺母/六角立柱/弹簧销 | `parts.fasteners.{rivet_nut,standoff_hex,pin_spring}` | — |
| 舵机 | `parts.servos.{sg90,standard_servo,servo_horn}` | SG90 / MG90S / MG996R / 标准 25T 舵盘 |
| 卡簧 | `parts.retainers` | 轴用/孔用 |
| O 型圈(ISO 3601-1 / GB 3452.1) | `parts.seals` | — |
| 销轴/光轴 | `parts.pins` | 圆销 / 开口销 / 弹簧销 |
| 传动 | `parts.transmission` | GT2 同步轮带、直齿/斜齿/锥齿/蜗轮、齿条 |
| 谐波减速关节(开发中) | `parts.actuators` | QDD Φ45×45 |

### yaml 单一数据源约定

每个类目根 yaml(如 `bearings.yaml`)是**唯一尺寸源**:
- yaml 改了 → 下次 `make_xxx()` 调用自动用新参数。
- 工厂函数**不复制**尺寸常量,运行时 `yaml.safe_load()` 后取值。
- 想看某型号支持没:`grep -i "<型号>" .../parts/<cat>/<cat>.yaml`(认 aliases)。

---

## L2-L3: 外部 STEP 来源 + license 红线

| 来源 | License 友好度 | 注意 |
|---|---|---|
| McMaster-Carr | 商用免费下载,**不可二次分发** | 装配里 import 可,提交到公有仓需删 |
| 厂商官网(SKF/NSK/Bosch/Festo/SMC…) | 通常允许装配引用 | 下载页常有"For evaluation only"小字,逐站确认 |
| GrabCAD | 上传者声明 license,**逐件确认** | 默认假设非商用 |
| TraceParts | 注册免费,商用 OK | 必须保留水印里的来源 URL |
| 3DContentCentral(SolidWorks) | 商用 OK,要求注明出处 | — |

**红线**(违反 = `parts-lib` 拒收 + 装配文件需删除):
- 不标 source URL / 不标 license → 一律视作不可用。
- license 模糊(无声明 / "personal use") → 不入 parts-lib,只本地装配临时引用。
- 仅 MIT / BSD / Apache-2.0 / Unlicense / CC0 / 厂商授权可入 parts-lib。

> 完整速查见 `references/step-sources.md`,含每来源典型 license 文案与判定流程图。

---

## handoff:目录 → mechanical 装配

按 `shared/handoff-protocols.md`,本子技能产出**两类**接口:

### A. 已入库件(L1 命中)

```python
# 装配脚本(由 mechanical 子技能拿走)
from build123d import Compound, Pos
from build123d_parts_lib.parts.bearings.ball_bearing import make_ball_bearing
from build123d_parts_lib.parts.servos.sg90 import make_sg90

bearing = make_ball_bearing(model="608ZZ")   # bbox: Φ22 × 7
servo   = make_sg90()                         # bbox: 29.9 × 12.6 × 31.1
asm = Compound(label="leg_joint", children=[
    Pos(0, 0, 0) * bearing,
    Pos(0, 0, 7) * servo,
])
```

返回给 mechanical:**模块路径列表 + 实例化参数**,不下 STEP。

### B. 未入库件(L2/L3 落盘)

```
output/<task>/parts/
  ├── 608zz_skf.step           # 厂商官网下载
  ├── 608zz_skf.LICENSE.txt    # 必须同名 .LICENSE.txt 标注来源 + license
  └── manifest.yaml            # part_id / source_url / license / sha256
```

mechanical 端:`from build123d import import_step; b = import_step("output/<task>/parts/608zz_skf.step")`。

`manifest.yaml` 模板见 `references/step-sources.md` §产物清单。

---

## 入库 promotion(L2/L3 → L1)

外部 STEP 反复用 → 提交到 build123d-parts-lib,变成 L1 可重用件。流程见
`build123d-parts-lib/CLAUDE.md` "Adding a New Part" 7 步;关键节点:
1. 选目录(`parts/<category>/`),写 `make_<name>()` 工厂(参数化优先,STEP 反求次之)。
2. 在 yaml 里加该型号 entry(含 `source.primary` URL + `factory.module/fn/cache`)。
3. 写 smoke test(`tests/test_<category>.py`),`scripts/build_cache.py` 注册产 STEP 缓存。
4. 跑 `python scripts/scan_all_gates.py` 三档闸门通过(D0 ops + D1 yaml + D2 code)。
5. PR 进 parts-lib;合并后本子技能 `references/standard-parts-index.md` 加一行。

---

## 快速起手 4 例

| 需求 | 第一行代码 |
|---|---|
| 「装个 608 轴承」 | `from build123d_parts_lib.parts.bearings.ball_bearing import make_ball_bearing; b = make_ball_bearing(model="608ZZ")` |
| 「来 4 颗 M3x10 内六角」 | `from build123d_parts_lib.parts.fasteners.socket_head_screw import make_socket_head_screw; s = make_socket_head_screw(model="M3", length=10)` |
| 「机器狗腿装 SG90」 | `from build123d_parts_lib.parts.servos.sg90 import make_sg90; servo = make_sg90()` |
| 「需要个 NEMA17 步进」 | parts-lib 暂未收录(TODO),走 L2:`https://www.stepperonline.com/` 下 STEP → `output/<task>/parts/nema17.step` |

---

## 不做什么

- ❌ 不在装配代码里硬编码标准件尺寸常量(违反「单一数据源」)。
- ❌ 不允许 import McMaster STEP 后提交到公有仓(license 不允许二次分发)。
- ❌ 不替 mechanical 子技能做装配关系/Joint(本子技能只产「件 + 实例化参数」)。
- ❌ 不下 STL 替代 STEP(STL 不带特征,无法做配合公差);3D 打印再 mechanical 转换。
- ❌ 不让用户「等我画一下 608 轴承」——库里有,直接 import。

---

## 验证(每次回报前自检)

- [ ] 引用的 `make_xxx()` 模块路径在 parts-lib 仓库里能 `import` 成功。
- [ ] 外部 STEP 都有同名 `.LICENSE.txt` + `manifest.yaml` 入参。
- [ ] 没有把 McMaster / "personal use" STEP 推到 parts-lib。
- [ ] handoff 给 mechanical 的清单含「模块路径 + 实例化参数 + bbox 预估」。

# 常用标准件索引(build123d-parts-lib 对接表)

本表回答两个问题:
1. **「这个件 parts-lib 有没有?」** —— 看 `module` 列。
2. **「调起来什么样?」** —— 看 `factory call` 列。

约定:`PARTS = build123d_parts_lib.parts`,例:`PARTS.bearings.ball_bearing.make_ball_bearing(...)`。
所有型号字符串大小写不敏感(yaml 里都登记了 `aliases:`),`"608"` / `"608zz"` / `"608-ZZ"` 等价。

> **数据源唯一性**:每个类目根 yaml(如 `bearings.yaml`)是尺寸单一来源;工厂函数运行时 `yaml.safe_load()` 取值,不要在装配代码里硬编码尺寸常量。

---

## 1. 轴承 Bearings

源 yaml:`build123d_parts_lib/parts/bearings/bearings.yaml`(主)、`lm_bearings.yaml`(直线衬套)。

| 型号 | 类型 | d × D × B | 模块 | factory call |
|---|---|---|---|---|
| 608ZZ | 深沟球(skateboard 标准) | 8 × 22 × 7 | `bearings.ball_bearing` | `make_ball_bearing(model="608ZZ")` |
| 624ZZ | 深沟球(微型) | 4 × 13 × 5 | 同上 | `make_ball_bearing(model="624ZZ")` |
| 625ZZ | 深沟球 | 5 × 16 × 5 | 同上 | `make_ball_bearing(model="625ZZ")` |
| 626ZZ | 深沟球 | 6 × 19 × 6 | 同上 | `make_ball_bearing(model="626ZZ")` |
| 6000ZZ | 深沟球(60xx 系列) | 10 × 26 × 8 | 同上 | `make_ball_bearing(model="6000ZZ")` |
| 6001-2RS | 深沟球(双密封) | 12 × 28 × 8 | 同上 | `make_ball_bearing(model="6001-2RS")` |
| 6002ZZ | 深沟球 | 15 × 32 × 9 | 同上 | `make_ball_bearing(model="6002ZZ")` |
| MR63ZZ | 微型(D3 轴) | 3 × 6 × 2.5 | `bearings.mr_bearing` | `make_mr_bearing(model="MR63ZZ")` |
| MR74ZZ | 微型(D4 轴) | 4 × 7 × 2.5 | 同上 | `make_mr_bearing(model="MR74ZZ")` |
| MR84ZZ | 微型(D4 轴宽版) | 4 × 8 × 3   | 同上 | `make_mr_bearing(model="MR84ZZ")` |
| MR85ZZ | 微型(D5 轴) | 5 × 8 × 2.5 | 同上 | `make_mr_bearing(model="MR85ZZ")` |
| MR105ZZ | 微型(D5 轴宽版) | 5 × 10 × 4 | 同上 | `make_mr_bearing(model="MR105ZZ")` |
| F608ZZ | 法兰深沟球 | 8 × 22 × 7 + flange | `bearings.flanged_bearing` | `make_flanged_bearing(model="F608ZZ")` |
| 7001-AC | 角接触球 | 12 × 28 × 8 | `bearings.angular_contact_bearing` | `make_angular_contact_bearing(model="7001-AC")` |
| 61804 | 薄壁深沟球 | 20 × 32 × 7 | `bearings.thin_section_bearing` | `make_thin_section_bearing(model="61804")` |
| HK0408 | 滚针轴承 | 4 × 8 × 8 | `bearings.needle_bearing` | `make_needle_bearing(model="HK0408")` |
| LM8UU | 直线衬套 | 8 × 15 × 24 | `bearings.linear_bushing` | `make_linear_bushing(model="LM8UU")` |
| LM10UU | 直线衬套 | 10 × 19 × 29 | 同上 | `make_linear_bushing(model="LM10UU")` |

> SKF / NSK 系列别名:`6000` / `6001` / `608` 在 yaml 里注册了厂商前缀别名(如 `skf-608`),写哪个都行。完整 alias 见 `bearings.yaml` 内 `aliases:` 字段。

---

## 2. 螺丝 / 螺母 / 垫片 Fasteners

源 yaml:`build123d_parts_lib/parts/fasteners/fasteners.yaml`(全部紧固件)。
**所有 fastener 都是光杆几何**(`smooth-shank`):无螺纹齿形,只有小径圆柱;`pitch` 字段保留供配合孔计算用。

| 类目 | 标准 | 规格 | 模块 | factory call |
|---|---|---|---|---|
| 内六角圆柱头 | ISO 4762 / DIN 912 | M2 / M2.5 / M3 / M4 / M5 / M6 / M8 / M10 | `fasteners.socket_head_screw` | `make_socket_head_screw(model="M3", length=10)` |
| 圆头六角(button) | ISO 7380 | M2.5–M6 | `fasteners.screw_button_hex` | `make_screw_button_hex(model="M3", length=8)` |
| 沉头十字 | ISO 7046 | M2–M6 | `fasteners.screw_csk_phillips` | `make_screw_csk_phillips(model="M3", length=10)` |
| 沉头一字 | ISO 2009 | M2–M6 | `fasteners.screw_csk_slotted` | `make_screw_csk_slotted(model="M3", length=10)` |
| 盘头十字 | ISO 7045 | M2–M6 | `fasteners.screw_pan_phillips` | `make_screw_pan_phillips(model="M3", length=8)` |
| 盘头一字 | ISO 1580 | M2–M6 | `fasteners.screw_pan_slotted` | `make_screw_pan_slotted(model="M3", length=8)` |
| 沉头方颈(carriage) | DIN 603 | M5–M10 | `fasteners.screw_carriage` | `make_screw_carriage(model="M6", length=20)` |
| 外六角螺栓 | ISO 4014 | M3–M16 | `fasteners.hex_bolt` | `make_hex_bolt(model="M5", length=20)` |
| 自攻螺丝套件 | — | 暂用 set 抽象 | `fasteners.screw_set` | `make_screw_set(...)` |
| 六角螺母 | ISO 4032 | M2–M10 | `fasteners.nut_hex` | `make_nut_hex(model="M3")` |
| 方螺母 | DIN 557 | M3–M8 | `fasteners.nut_square` | `make_nut_square(model="M4")` |
| 法兰螺母 | DIN 6923 | M3–M10 | `fasteners.nut_flange` | `make_nut_flange(model="M5")` |
| 翼形螺母 | DIN 315 | M3–M8 | `fasteners.nut_wing` | `make_nut_wing(model="M4")` |
| 帽螺母(盖) | DIN 1587 | M3–M10 | `fasteners.nut_cap` | `make_nut_cap(model="M4")` |
| T 槽螺母 | 2020/3030 槽 | M3 / M4 / M5 / M6 | `fasteners.nut_tslot` | `make_nut_tslot(model="M5", profile="2020")` |
| 平/弹簧/锯齿垫片 | ISO 7089 / DIN 127 / DIN 6797 | M2–M10 | `fasteners.washer` | `make_washer(model="M3", kind="flat")` |
| 螺纹热熔铜套 | — | M2 / M3 / M4 / M5 | `fasteners.threaded_insert` | `make_threaded_insert(model="M3")` |
| 拉铆螺母 | — | M3 / M4 / M5 / M6 | `fasteners.rivet_nut` | `make_rivet_nut(model="M4")` |
| 六角立柱 | — | M3 / M4 / M5(公-母 / 公-公) | `fasteners.standoff_hex` | `make_standoff_hex(model="M3", length=10, kind="MF")` |
| 弹簧销 | ISO 8752 | Φ2–Φ8 | `fasteners.pin_spring` | `make_pin_spring(d=3, length=10)` |

> **配合孔尺寸**:不要凭印象写孔径,用 `generators.clearance.get_clearance_diameter(m_size, fit)`(`fit ∈ {"close","medium","loose"}`)取标准过孔。

---

## 3. 舵机 Servos

源 yaml:`build123d_parts_lib/parts/servos/servos.yaml`。

| 型号 | 类型 | bbox(L×W×H) | 模块 | factory call |
|---|---|---|---|---|
| SG90 | 9g 微型(塑齿) | 23 × 12.6 × 31.1 | `servos.sg90` | `make_sg90()` |
| MG90S | 9g 金属齿(SG90 兼容) | 22.5 × 12 × 30 | `servos.sg90` 或 `standard_servo` | yaml 里别名指向 sg90 工厂(几何兼容) |
| MG996R | 标准舵机(55g) | 40 × 19 × 43 | `servos.standard_servo` | `make_standard_servo(model="MG996R")` |
| 标准 25T 舵盘 | 一字 / 十字 / 圆形 | Φ20–Φ25 | `servos.servo_horn` | `make_servo_horn(kind="cross")` |

四足机器狗装腿默认:髋关节用 MG996R(扭矩),膝/踝用 SG90/MG90S(空间小)。

---

## 4. 步进电机 Stepper(TODO,parts-lib 暂未收录)

| 规格 | 法兰 | 典型尺寸 | 推荐 STEP 来源 |
|---|---|---|---|
| NEMA8 | 20×20 | 长 30 / 38 | StepperOnline / 厂商 |
| NEMA14 | 35×35 | 长 28 / 36 | 同上 |
| NEMA17 | 42×42 | 长 33 / 39 / 47 | 同上(机器人最常见) |
| NEMA23 | 56.4×56.4 | 长 56 / 76 | 同上(大功率) |

入库前先走 L2:`https://www.stepperonline.com/<model>` → 下 STEP → `output/<task>/parts/nema17.step`。
**入库 PR 模板**:在 `parts/motors/` 新建目录,加 `motors.yaml` + `stepper_nema.py` 工厂(参数化:法兰宽 / 长 / 轴径 / 螺孔距),走 build123d-parts-lib 7 步流程。

---

## 5. 卡簧 Retainers

源:`build123d_parts_lib/parts/retainers/`。

- 轴用卡簧(外卡):DIN 471,Φ3–Φ50。
- 孔用卡簧(内卡):DIN 472,Φ8–Φ60。

调用:`from build123d_parts_lib.parts.retainers import make_external_retainer; r = make_external_retainer(d=8)`。

---

## 6. 密封 Seals

源 yaml:`build123d_parts_lib/parts/seals/`(O 型圈,ISO 3601-1 / GB/T 3452.1)。

- ID(内径)+ CS(线径)双索引。
- 常用线径:1.0 / 1.5 / 1.8 / 2.0 / 2.5 / 3.0 / 3.5 mm。
- 调用:`from build123d_parts_lib.parts.seals import make_o_ring; o = make_o_ring(id_mm=10, cs_mm=2.0)`。

---

## 7. 销轴 / 光轴 Pins

源:`build123d_parts_lib/parts/pins/`。

- 圆柱销 / 开口销 / 弹簧销 / 光轴(铬钢镜面)。
- 直径 Φ1.5 / Φ2 / Φ2.5 / Φ3 / Φ4 / Φ5 / Φ6 / Φ8 / Φ10。
- 调用:`make_smooth_shaft(d=5, length=80)`。

---

## 8. 传动 Transmission

源:`build123d_parts_lib/parts/transmission/`。

| 类目 | 模块 | 备注 |
|---|---|---|
| GT2 同步带轮 | `transmission.gt2_pulley` | 16T / 20T / 36T / 60T |
| GT2 同步带 | `transmission.gt2_belt` | 闭环 / 开口长度参数化 |
| 直齿轮(spur) | `transmission.spur_gear` | 模数 0.5 / 0.8 / 1.0 / 1.25 |
| 斜齿轮(helical) | `transmission.helical_gear` | 螺旋角参数化 |
| 锥齿轮(bevel) | `transmission.bevel_gear` | 直齿锥 / 弧齿锥 |
| 蜗轮蜗杆 | `transmission.worm_*` | 单头 / 多头 |
| 齿条(rack) | `transmission.rack` | 模数 + 长度 |

---

## 9. 关节执行器 Actuators(开发中)

`parts/actuators/` — QDD 谐波减速关节模块(Φ45×45 mm)。M0–M4 milestone,见
`build123d-parts-lib/build123d_parts_lib/parts/actuators/PLAN.md`。机器狗髋关节预选项,
**短期内不要 import**(API 未冻结)。

---

## 速查:某型号没找到怎么办

1. `grep -i "<型号>" /Users/liyijiang/work/build123d-parts-lib/build123d_parts_lib/parts/*/[a-z]*.yaml`
   命中 → 读对应 yaml 看 `factory.module/fn`。
2. 没命中 → 走 `step-sources.md` 找 STEP → 落 `output/<task>/parts/`。
3. 项目里第二次用同一件 → 提 PR 入 parts-lib(promotion 流程见 SKILL.md §入库 promotion)。

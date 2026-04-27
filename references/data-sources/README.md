# 数据源目录（Standard Parts Data Sources）

> **用途**：回答"标准件参数从哪查"的唯一入口。
> AI 做 CAD 建模遇到螺丝/轴承/舵机/电子模块等通用零件时，**先查本目录**，未命中再走 WebSearch/WebFetch。

---

## 目录组织

```
references/data-sources/
├── README.md              # 本文件（规范 + schema）
├── sources-catalog.yaml   # 按类别的权威源清单 + WebSearch prompt 模板
├── servos.yaml            # 舵机（SG90、MG90S、MG996R…）
├── fasteners.yaml         # 紧固件（M2~M5 螺丝）
├── bearings.yaml          # 轴承（608ZZ、624ZZ、6001-2RS…）
└── …                      # 用到新类别再加
```

---

## 查询方式

```bash
# CLI 查询（推荐）
python3 scripts/research/spec_lookup.py SG90
python3 scripts/research/spec_lookup.py M3
python3 scripts/research/spec_lookup.py 608ZZ

# 大小写不敏感 + alias 命中
python3 scripts/research/spec_lookup.py sg90
python3 scripts/research/spec_lookup.py mini-servo-9g

# 列出某类别全部条目
python3 scripts/research/spec_lookup.py --list servos

# 列出所有类别
python3 scripts/research/spec_lookup.py --list-categories
```

**返回结果**：
- 命中 → 结构化 YAML 片段 + `source.primary` URL + `confidence` 置信度
- 未命中 → `sources-catalog.yaml` 里该类别的 `priority_sources` + `websearch_prompt` 建议

---

## YAML Schema（所有组件共用）

```yaml
# 顶级 key = 规范化零件 ID（保留大小写便于阅读，查询时不敏感）
SG90:
  aliases: [sg90, tower-pro-sg90, mini-servo-9g]   # 别名（查询命中）
  category: servo                                   # 对应 sources-catalog 里的大类
  body:                                             # 核心几何尺寸
    length: 22.8                                    # 数值
    width:  12.2
    height: 22.7
    unit:   mm                                      # 单位（显式声明）
  mount_holes:                                      # 可选：安装孔/耳朵/接口
    ear_width_total: 32.2
    ear_thickness:   2.5
    ear_z_offset:    15.5
  source:                                           # ⚠️ 必填
    primary:       "https://servodatabase.com/servo/towerpro/sg-90"
    datasheet:     ""                               # PDF URL（可空）
    confidence:    4                                # 1~5，见下
    last_verified: 2026-04-27                       # ISO 日期
  notes: "量产公差 ±0.3mm；塑料齿轮版本常见"
```

---

## 置信度约定（confidence 1~5）

沿用 `references/protocols/reference-product-playbook.md` R3 的 ★ 规范：

| confidence | 含义 | 典型来源 |
|-----------:|------|---------|
| 5 ★★★★★ | 厂商官方 datasheet / ISO/DIN 标准 | 厂商 PDF、国标表 |
| 4 ★★★★ | 权威社区/垂直数据库交叉验证 | servodatabase、McMaster 尺寸页 |
| 3 ★★★ | 单一可信来源但未二次验证 | GrabCAD 社区 STEP、厂商 wiki |
| 2 ★★ | 博客/教程/淘宝页（仅占位） | 草根测评、店铺描述 |
| 1 ★ | 纯推断 | AI 类比估算 |

**规则**：`confidence >= 3` 才可被 AI 当"权威"直接引用到 params.md；`< 3` 必须在当次建模里重新核实。

---

## 贡献规则

新增/修改条目时：

1. **必须带 `source.primary` + `confidence` + `last_verified`**——缺一律视为未收录
2. **尺寸必带单位**（`unit: mm` 显式）——避免英制/公制混淆
3. **别名覆盖真实使用场景**：用户叫"9g 舵机"也要能命中 SG90
4. **冲突数据显式保留**：若不同源给出不同值，在 `notes:` 里记录差异 + 选用理由
5. **超过 90 天未复核** → 下次使用时 `last_verified` 超期，查询脚本会打 `[stale]` 警告，建议本次重新校验

---

## 与 experience/ 的分工

| 目录 | 负责 | 粒度 | 示例 |
|------|------|------|------|
| `references/data-sources/` | **标准件** — 通用、可复用 | 零件型号级 | SG90、M3 ISO 4762、608ZZ |
| `experience/` | **产品级** — 整机/具体产品 | 产品型号级 | Redmi K80 Pro、树莓派 4B、特定手办 |

**判断边界**：
- 能被多个不同项目**原样复用** → `data-sources/`
- 仅对某款具体产品有意义（整机外壳、某款手机开孔布局） → `experience/<category>/<slug>.md`

---

## 扩展清单（优先级粗排，用到再加）

- [ ] `motors.yaml` — NEMA 17/23 步进电机、无刷电机典型尺寸
- [ ] `connectors.yaml` — XT30/XT60、杜邦、USB-C、Type-A 接口机械尺寸
- [ ] `mcu-boards.yaml` — Arduino Uno/Nano、ESP32 DevKit、树莓派 Pico 外形 + 孔位
- [ ] `displays.yaml` — 0.96" OLED、1.28" 圆屏、2.4"/3.5" TFT 可视区 + 安装孔
- [ ] `sensors.yaml` — HC-SR04、MPU6050、VL53L0X 常用传感器模块
- [ ] `threaded-inserts.yaml` — 热压铜螺母（M2/M3/M4）
- [ ] `extrusions.yaml` — 2020/3030/4040 铝型材断面

新增类别时同步在 `sources-catalog.yaml` 里登记该类别的权威源。
